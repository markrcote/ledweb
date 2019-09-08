#!/usr/bin/env python3

import json
import os
import time

import redis
from PIL import Image

from rgbmatrix import RGBMatrix, graphics

import options
from weather import OpenWeather


def redis_retry(ex):
    def wrap(func):
        def wrapper(*arg):
            while True:
                try:
                    func(*arg)
                except ex as e:
                    print('Error connecting to redis: {}'.format(e))
                    print('Sleeping for 5 seconds...')
                    time.sleep(5)
        return wrapper
    return wrap


class LedServiceMode:
    MODE_NAME = None
    BACKGROUND_POLL_TIME = None

    def __init__(self, matrix):
        self.matrix = matrix
        self.setup()
        self.last_bg_poll = None

    def setup(self):
        pass

    def handle_command(self, cmd):
        return True

    def iterate(self):
        pass

    def activate(self):
        '''Called when this mode is foregrounded.'''
        pass

    def background_poll(self):
        if self.BACKGROUND_POLL_TIME is None:
            return

        now = time.time()
        if (not self.last_bg_poll or
                now - self.last_bg_poll >= self.BACKGROUND_POLL_TIME):
            self.last_bg_poll = now
            self.background_job()

    def background_job(self):
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
    BACKGROUND_POLL_TIME = 10
    WEATHER_POLL_SECONDS = 60*10

    SCREEN_CURRENT = 0

    SCREENS = [
        SCREEN_CURRENT
    ]

    def setup(self):
        self.offscreen = self.matrix.CreateFrameCanvas()
        self.font = graphics.Font()
        self.font.LoadFont('fonts/5x7.bdf')
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

    def activate(self):
        self.next_time = time.time()
        self.prepare_offscreen()

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


class LedService:
    LOOP_SLEEP = 0.001

    def __init__(self, matrix, redis_cli, modes):
        self.matrix = matrix
        self.redis_cli = redis_cli
        self.modes = [x(self.matrix) for x in modes]
        self.mode_map = {mode.MODE_NAME: i for i, mode in
                         enumerate(self.modes)}
        self.reset()

    def reset(self):
        self.matrix.Clear()
        self.current_mode_idx = None
        self.current_mode = None

    def switch_mode(self, mode_idx, cmd):
        self.matrix.Clear()
        self.current_mode = None
        self.current_mode_idx = mode_idx
        self.current_mode = self.modes[self.current_mode_idx]
        self.current_mode.activate()
        self.current_mode.handle_command(cmd)

    def next_mode(self, incr):
        if self.modes:
            if self.current_mode_idx is None:
                new_mode_idx = 0 if incr > 0 else len(self.modes) - 1
            else:
                new_mode_idx = self.current_mode_idx + incr
            new_mode_idx %= len(self.modes)

            self.switch_mode(new_mode_idx, [])

    @redis_retry(redis.exceptions.ConnectionError)
    def loop(self):
        while True:
            while self.redis_cli.llen(options.REDIS_QUEUE) == 0:
                if self.current_mode:
                    self.current_mode.iterate()
                for mode in self.modes:
                    mode.background_poll()
                time.sleep(self.LOOP_SLEEP)
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
