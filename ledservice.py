#!/usr/bin/env python3

import os
import time

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

    def handle_command(self, cmd):
        if not self.images:
            return
        if not cmd:
            self.display_image(self.images[0])
        elif cmd[0] == 'image':
            self.display_image(cmd[1])
        elif cmd[0] == 'next':
            cur_images = self.images
            try:
                next_image = cur_images[
                    (cur_images.index(self.current_image) + 1)
                    % len(cur_images)
                ]
            except ValueError:
                next_image = cur_images[0]
            self.display_image(next_image)
        return True


class TimeMode(LedServiceMode):
    # Adapted from https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/examples-api-use/clock.cc.

    MODE_NAME = 'time'
    LOOP_SLEEP = 0.001

    def setup(self):
        self.offscreen = self.matrix.CreateFrameCanvas()
        self.font = graphics.Font()
        self.font.LoadFont('fonts/5x7.bdf')
        self.text_colour = graphics.Color(0, 255, 255)

        self.next_time = time.time()
        self.prepare_offscreen()

    def prepare_offscreen(self):
        t = time.localtime(self.next_time)
        ts = time.strftime('%I:%M %p', t)
        if ts[0].startswith('0'):
            ts = ' {}'.format(ts[1:])

        self.offscreen.Clear()
        graphics.DrawText(
            self.offscreen,
            self.font,
            0,
            self.font.baseline + 2,
            self.text_colour,
            ts
        )

    def iterate(self):
        if time.time() < self.next_time:
            return

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
        self.current_mode_idx = -1
        self.current_mode = None

    def switch_mode(self, mode_idx, cmd):
        self.matrix.Clear()
        self.current_mode = None
        self.current_mode_idx = mode_idx
        self.current_mode = self.modes[self.current_mode_idx](self.matrix, cmd)

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
                if self.modes:
                    self.switch_mode((self.current_mode_idx + 1) % len(self.modes), [])
            elif cmd[0] == 'off' or cmd[0] == 'clear':
                self.reset()
            elif self.current_mode and cmd[0] == self.current_mode.MODE_NAME:
                self.current_mode.handle_command(cmd[1:])
            elif cmd[0] in self.mode_map:
                self.switch_mode(self.mode_map[cmd[0]], cmd[1:])
            else:
                print('unknown command {}'.format(cmd))


def main():
    redis_cli = redis.from_url('redis://localhost:6379')
    matrix = RGBMatrix(options=options.matrix_options())

    led_service = LedService(matrix, redis_cli, [DisplayMode, TimeMode])
    led_service.loop()


if __name__ == '__main__':
    main()
