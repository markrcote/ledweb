from rgbmatrix import RGBMatrixOptions


def matrix_options():
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
