import time

from ledweb.servicemode.ledservicemode import LedServiceMode


class DrawMode(LedServiceMode):

    MODE_NAME = 'draw'
    BLINK_ON = 1
    BLINK_OFF = 0.5

    def setup(self):
        self.offscreen = None
        self.pos = (0, 0)
        self.next_time = time.time()
        self.cursor_on = False
        self.colour = (127, 0, 0)

    def iterate(self):
        now = time.time()
        if now > self.next_time:
            self.cursor_on = not self.cursor_on
            self.blink()
            if self.cursor_on:
                self.next_time = now + self.BLINK_ON
            else:
                self.next_time = now + self.BLINK_OFF

    def blink(self):
        if self.cursor_on:
            colour = self.colour
        else:
            colour = (0, 0, 0)
        print('setting pixel')
        self.offscreen.SetPixel(
            self.pos[0],
            self.pos[1],
            *colour
        )
        self.offscreen = self.matrix.SwapOnVSync(self.offscreen)

    def do_activate(self):
        self.offscreen = self.matrix.CreateFrameCanvas()
        self.next_time = time.time()

    def do_deactivate(self):
        self.offscreen = None

