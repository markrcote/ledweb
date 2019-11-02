#!/usr/bin/env python3

import logging
import os

import redis
from flask import (
    abort,
    Flask,
    request,
)
from werkzeug.utils import secure_filename

import options

application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = options.IMAGES_DIR
application.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # probably too high

cli = redis.from_url(options.REDIS_URL)

if not os.path.exists(options.IMAGES_DIR):
    os.mkdir(options.IMAGES_DIR)


def send_cmd(cmd):
    cli.lpush(
        options.REDIS_QUEUE,
        cmd.encode('utf-8')
    )


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in options.ALLOWED_EXTENSIONS)


@application.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logging.error('"file" not in request.files')
        abort(400)

    file = request.files['file']
    if file.filename == '':
        logging.error('no filename')
        abort(400)

    if not allowed_file(file.filename):
        logging.error('file not allowed')
        abort(400)

    filename = secure_filename(file.filename)
    file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))

    # Trim files if needed.
    saved_files = [os.path.join(options.IMAGES_DIR, x)
                   for x in os.listdir(options.IMAGES_DIR)]
    # Order oldest to newest.
    saved_files.sort(key=lambda x: int(os.stat(x).st_mtime))
    saved_files.reverse()
    while len(saved_files) > options.MAX_NUM_IMAGES:
        os.remove(saved_files.pop())

    return 'success'


@application.route('/display/<img_filename>', methods=['POST'])
def display(img_filename):
    send_cmd('display image {}'.format(img_filename))
    return 'ok'


@application.route('/delete/<img_filename>', methods=['POST'])
def delete(img_filename):
    '''Admittedly not very REST-y...'''
    filename = secure_filename(img_filename)
    full_path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(full_path):
        abort(404)
    os.unlink(full_path)
    return 'ok'


@application.route('/clear', methods=['POST'])
def clear():
    send_cmd('clear')
    return 'ok'


if __name__ == '__main__':
    application.run(host='0.0.0.0')
