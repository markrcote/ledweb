#!/usr/bin/env python3

import http.client
import json
import os
import time
import urllib.request

import redis
from PIL import Image

from rgbmatrix import RGBMatrix, graphics

import options


class LedServiceMode:
    MODE_NAME = None
    LOOP_SLEEP = None

    def __init__(self, matrix, cmd):
        self.matrix = matrix
        self.setup()
        self.handle_command(cmd)

    def setup(self):
        pass

    def handle_command(self, cmd):
        return True

    def iterate(self):
        pass


class DisplayMode(LedServiceMode):
    MODE_NAME = 'display'

    def setup(self):
        self.current_image = None

    @property
    def images(self):
        return sorted(os.listdir(options.IMAGES_DIR))

    def display_image(self, img_filename):
        path = os.path.join(options.IMAGES_DIR, os.path.basename(img_filename))
        if not os.path.isfile(path):
            return False
        image = Image.open(path)
        image.load()
        self.matrix.SetImage(image.convert('RGB'))
        self.current_image = img_filename

    def next_image(self, incr):
        cur_images = self.images
        try:
            next_image = cur_images[
                (cur_images.index(self.current_image) + incr)
                % len(cur_images)
            ]
        except ValueError:
            next_image = cur_images[0]
        self.display_image(next_image)

    def handle_command(self, cmd):
        if not self.images:
            return
        if not cmd:
            self.display_image(self.images[0])
        elif cmd[0] == 'image':
            self.display_image(cmd[1])
        elif cmd[0] == 'next':
            self.next_image(1)
        elif cmd[0] == 'prev':
            self.next_image(-1)
        return True


class TimeMode(LedServiceMode):
    # Adapted from https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/examples-api-use/clock.cc.

    MODE_NAME = 'time'
    LOOP_SLEEP = 0.001
    WEATHER_POLL_SECONDS = 60*10
    OPEN_WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5/weather?id={city_id}&APPID={app_id}'

    def setup(self):
        self.offscreen = self.matrix.CreateFrameCanvas()
        self.font = graphics.Font()
        self.font.LoadFont('fonts/5x7.bdf')
        self.text_colour = graphics.Color(0, 255, 255)

        self.weather = None
        self.next_time = time.time()
        self.next_weather = time.time()
        self.prepare_offscreen()

    def get_weather(self):
        print('getting weather')
        if (not options.OPEN_WEATHER_API_KEY
                or not options.OPEN_WEATHER_CITY_ID):
            print('OpenWeather API not configured.')
            return

        url = self.OPEN_WEATHER_API_URL.format(
            city_id=options.OPEN_WEATHER_CITY_ID,
            app_id=options.OPEN_WEATHER_API_KEY
        )

        response = None

        try:
            response = json.loads(urllib.request.urlopen(url).read().decode())
        except http.client.HTTPException as e:
            print('Error loading OpenWeather API: {}'.format(e))
        except ValueError:
            print('Invalid response from OpenWeather API')

        if not response:
            return

        self.weather = response

    def prepare_offscreen(self):
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
            self.font.baseline + 2,
            self.text_colour,
            ts
        )

        graphics.DrawText(
            self.offscreen,
            self.font,
            0,
            self.font.baseline * 2 + 4,
            self.text_colour,
            month_day
        )

        if self.weather:
            temps = '{}°'.format(int(self.weather['main']['temp'] - 273.15))

            graphics.DrawText(
                self.offscreen,
                self.font,
                44,
                28,
                self.text_colour,
                temps
            )

            if 'weather' in self.weather:
                icon_path = os.path.join(
                    os.path.dirname(__file__),
                    'icons',
                    '{}.json'.format(self.weather['weather'][0]['icon'])
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
        now = time.time()

        if now < self.next_time:
            return

        if now >= self.next_weather:
            self.get_weather()
            self.next_weather += self.WEATHER_POLL_SECONDS

        self.offscreen = self.matrix.SwapOnVSync(self.offscreen)
        self.next_time += 1
        self.prepare_offscreen()


class LedService:

    def __init__(self, matrix, redis_cli, modes):
        self.matrix = matrix
        self.redis_cli = redis_cli
        self.modes = modes
        self.mode_map = {mode.MODE_NAME: i for i, mode in enumerate(self.modes)}
        self.reset()

    def reset(self):
        self.matrix.Clear()
        self.current_mode_idx = None
        self.current_mode = None

    def switch_mode(self, mode_idx, cmd):
        self.matrix.Clear()
        self.current_mode = None
        self.current_mode_idx = mode_idx
        self.current_mode = self.modes[self.current_mode_idx](self.matrix, cmd)

    def next_mode(self, incr):
        if self.modes:
            if self.current_mode_idx is None:
                new_mode_idx = 0 if incr > 0 else len(self.modes) - 1
            else:
                new_mode_idx = self.current_mode_idx + incr
            new_mode_idx %= len(self.modes)

            self.switch_mode(new_mode_idx, [])

    def loop(self):
        while True:
            if self.current_mode and self.current_mode.LOOP_SLEEP:
                while self.redis_cli.llen(options.REDIS_QUEUE) == 0:
                    self.current_mode.iterate()
                    time.sleep(self.current_mode.LOOP_SLEEP)
            msg = self.redis_cli.brpop([options.REDIS_QUEUE])

            cmd = msg[1].decode('utf-8').split()
            print('got cmd: {}'.format(cmd))
            if cmd[0] == 'next_mode':
                self.next_mode(1)
            elif cmd[0] == 'prev_mode':
                self.next_mode(-1)
            elif cmd[0] == 'off' or cmd[0] == 'clear':
                self.reset()
            elif self.current_mode and (
                cmd[0] == self.current_mode.MODE_NAME or
                cmd[0] == 'mode'
            ):
                self.current_mode.handle_command(cmd[1:])
            elif cmd[0] in self.mode_map:
                self.switch_mode(self.mode_map[cmd[0]], cmd[1:])
            else:
                print('unknown command {}'.format(cmd))


def main():
    redis_cli = redis.from_url(options.REDIS_URL)
    matrix = RGBMatrix(options=options.matrix_options())

    led_service = LedService(matrix, redis_cli, [DisplayMode, TimeMode])
    led_service.loop()


if __name__ == '__main__':
    main()
