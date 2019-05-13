#!/usr/bin/env python3

import os
import time

import redis
from PIL import Image

from rgbmatrix import RGBMatrix, graphics

import options

matrix = RGBMatrix(options=options.matrix_options())


def clear_matrix():
    matrix.Clear()
    return 'success'


def display_png(img_filename):
    path = os.path.join(options.IMAGES_DIR, os.path.basename(img_filename))
    if not os.path.isfile(path):
        return 'notfound'
    clear_matrix()
    image = Image.open(path)
    image.load()
    matrix.SetImage(image.convert('RGB'))
    return 'success'


def clock_loop(cli):
    # Adapted from https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/examples-api-use/clock.cc.
    offscreen = matrix.CreateFrameCanvas()
    font = graphics.Font()
    font.LoadFont('fonts/5x7.bdf')
    text_colour = graphics.Color(0, 255, 255)

    next_time = time.time()

    while cli.llen('matrix') == 0:
        t = time.localtime(next_time)
        ts = time.strftime('%I:%M %p', t)
        if ts[0].startswith('0'):
            ts = ' {}'.format(ts[1:])

        offscreen.Clear()
        graphics.DrawText(
            offscreen,
            font,
            0,
            font.baseline + 2,
            text_colour,
            ts
        )

        while time.time() < next_time:
            time.sleep(0.001)

        offscreen = matrix.SwapOnVSync(offscreen)
        next_time += 1

    clear_matrix()


def loop():
    cli = redis.from_url('redis://localhost:6379')
    while True:
        try:
            msg = cli.brpop(['matrix'])
        except redis.exceptions.ConnectionError:
            print('failed to connect to redis')
            time.sleep(5)
            continue
        cmd = msg[1].decode('utf-8').split()
        print('got cmd: {}'.format(cmd))
        if cmd[0] == 'clear':
            clear_matrix()
        elif cmd[0] == 'display':
            print('displaying {}'.format(cmd[1]))
            display_png(cmd[1])
        elif cmd[0] == 'clock':
            clock_loop(cli)
        else:
            print('unknown command')


if __name__ == '__main__':
    loop()
