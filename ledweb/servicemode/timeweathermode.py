import json
import os
import time

from rgbmatrix import graphics

from ledweb import options
from ledweb.servicemode.ledservicemode import LedServiceMode
from ledweb.weather.openweather import OpenWeather


class TimeWeatherMode(LedServiceMode):
    # Adapted from https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/examples-api-use/clock.cc.

    MODE_NAME = 'time'
    BACKGROUND_POLL_TIME = 60
    WEATHER_POLL_SECONDS = 60*10

    SCREEN_CURRENT = 0

    SCREENS = [
        SCREEN_CURRENT
    ]

    def setup(self):
        self.offscreen = None
        self.font = graphics.Font()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # FIXME: Find a better place to put the fonts or better way to specify it.
        self.font.LoadFont(os.path.join(dir_path, '..', 'fonts/5x7.bdf'))
        self.text_colour = graphics.Color(0, 255, 255)

        self.weather = OpenWeather(
            options.OPEN_WEATHER_API_KEY,
            options.OPEN_WEATHER_CITY_ID
        )
        self.next_time = time.time()
        self.next_weather = time.time()
        self.screen = self.SCREEN_CURRENT

    def background_job(self):
        if time.time() < self.next_weather:
            return

        self.next_weather += self.WEATHER_POLL_SECONDS

        self.weather.get_weather()

    def prepare_current_offscreen(self):
        t = time.localtime(self.next_time)
        ts = time.strftime('%I:%M %p', t)
        if ts[0].startswith('0'):
            ts = ' {}'.format(ts[1:])
        month_day = time.strftime('%a %e %b')

        self.offscreen.Clear()
        graphics.DrawText(
            self.offscreen,
            self.font,
            0,
            self.font.baseline + 3,
            self.text_colour,
            ts
        )

        graphics.DrawText(
            self.offscreen,
            self.font,
            0,
            self.font.baseline * 2 + 6,
            self.text_colour,
            month_day
        )

        if self.weather.weather:
            temps = '{}°'.format(self.weather.current_temp())

            graphics.DrawText(
                self.offscreen,
                self.font,
                44,
                28,
                self.text_colour,
                temps
            )

            weather_icon = self.weather.current_weather_icon()

            if weather_icon:
                icon_path = os.path.join(
                    os.path.dirname(__file__),
                    'icons',
                    '{}.json'.format(weather_icon)
                )

                if os.path.exists(icon_path):
                    icon = json.loads(open(icon_path).read())
                    for pixel in icon:
                        self.offscreen.SetPixel(
                            pixel[0] + 32,
                            pixel[1] + 20,
                            *pixel[2:]
                        )

    def iterate(self):
        '''Refreshes time.

        Weather refreshing is handled by the background job.
        '''
        now = time.time()

        if now < self.next_time:
            return

        self.offscreen = self.matrix.SwapOnVSync(self.offscreen)
        self.next_time += 1
        self.prepare_offscreen()

    def prepare_offscreen(self):
        if self.screen == self.SCREEN_CURRENT:
            self.prepare_current_offscreen()

    def do_activate(self):
        self.offscreen = self.matrix.CreateFrameCanvas()
        self.next_time = time.time()
        self.prepare_offscreen()

    def do_deactivate(self):
        self.offscreen = None

    def handle_command(self, cmd):
        if not cmd:
            return True
        elif cmd[0] == 'next':
            self.screen += 1
        elif cmd[0] == 'prev':
            self.screen -= 1
        self.screen %= len(self.SCREENS)
        self.prepare_offscreen()
        return True
