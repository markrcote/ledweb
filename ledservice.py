#!/usr/bin/python

import os

import redis
from PIL import Image

from rgbmatrix import Adafruit_RGBmatrix

IMAGES_DIR = '/tmp/ledweb_img'

matrix = Adafruit_RGBmatrix(32, 2)


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
    matrix.SetImage(image.im.id, 1, 1)
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
