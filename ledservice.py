#!/usr/bin/env python3

import os
import time

import redis
from PIL import Image

from rgbmatrix import RGBMatrix

from options import matrix_options

IMAGES_DIR = os.getenv('LEDWEB_IMAGES_DIR', '/tmp/ledweb_img')

matrix = RGBMatrix(options=matrix_options())


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
        else:
            print('unknown command')


if __name__ == '__main__':
    loop()
