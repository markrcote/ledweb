#!/usr/bin/python

import logging
import os

import redis
from flask import (
    abort,
    Flask,
    request,
)
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png'])
IMAGES_DIR = os.getenv('LEDWEB_IMAGES_DIR', '/tmp/ledweb_img')
MAX_NUM_IMAGES = int(os.getenv('LEDWEB_MAX_NUM_IMAGES', 100))
REDIS_QUEUE = 'matrix'

application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = IMAGES_DIR
application.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # probably too high

cli = redis.from_url('redis://localhost')

if not os.path.exists(IMAGES_DIR):
    os.mkdir(IMAGES_DIR)


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


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
    saved_files = [os.path.join(IMAGES_DIR, x) for x in os.listdir(IMAGES_DIR)]
    # Order oldest to newest.
    saved_files.sort(cmp=lambda x, y: int(os.stat(y).st_mtime) - int(os.stat(x).st_mtime))
    while len(saved_files) > MAX_NUM_IMAGES:
        os.remove(saved_files.pop())

    return 'success'


@application.route('/display/<img_filename>', methods=['POST'])
def display(img_filename):
    cli.lpush(REDIS_QUEUE, 'display {}'.format(img_filename))
    return 'ok  '


@application.route('/clear', methods=['POST'])
def clear():
    cli.lpush(REDIS_QUEUE, 'clear')
    return 'ok'


if __name__ == '__main__':
    application.run(host='0.0.0.0')