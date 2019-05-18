import os

ALLOWED_EXTENSIONS = {'png'}
IMAGES_DIR = os.getenv('LEDWEB_IMAGES_DIR', '/var/run/ledweb')
MAX_NUM_IMAGES = int(os.getenv('LEDWEB_MAX_NUM_IMAGES', 100))
REDIS_URL = 'redis://localhost:6379'
REDIS_QUEUE = 'matrix'


def matrix_options():
    # Put this include within the function so that the rest of this file can
    # be imported by ledweb, which doesn't necessarily have `rgbmatrix`
    # available in its environment.
    from rgbmatrix import RGBMatrixOptions

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

    return options
