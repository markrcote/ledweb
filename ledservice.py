#!/usr/bin/python

import os

import redis
from PIL import Image

from rgbmatrix import RGBMatrix, RGBMatrixOptions

IMAGES_DIR = '/tmp/ledweb_img'

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1

# Use 'adafruit-hat' if you haven't soldered GPIO pins 4 and 18 together
# (see https://github.com/hzeller/rpi-rgb-led-matrix#switch-the-pinout).
options.hardware_mapping = 'adafruit-hat-pwm'

# Newer Raspberry PIs put out data too quickly, which causes flickering.
# This slows them down.
options.gpio_slowdown = 2

matrix = RGBMatrix(options=options)


def clear_matrix():
    matrix.Clear()
    return 'success'


def display_png(img_filename):
    path = os.path.join(IMAGES_DIR, os.path.basename(img_filename))
    if not os.path.isfile(path):
        return 'notfound'
    clear_matrix()
    image = Image.open(path)
    image.load()
    matrix.SetImage(image.convert('RGB'))
    return 'success'


def loop():
    cli = redis.from_url('redis://localhost:6379')
    while True:
        msg = cli.brpop(['matrix'])
        cmd = msg[1].split()
        print 'got cmd: {}'.format(cmd)
        if cmd[0] == 'clear':
            clear_matrix()
        elif cmd[0] == 'display':
            print 'displaying {}'.format(cmd[1])
            display_png(cmd[1])


if __name__ == '__main__':
    loop()
