import time

from rgbmatrix import RGBMatrix

from ledweb import options


class LedServiceMode:
    MODE_NAME = None
    BACKGROUND_POLL_TIME = None

    def __init__(self):
        self.matrix = None
        self.setup()
        self.last_bg_poll = None

    def setup(self):
        pass

    def handle_command(self, cmd):
        return True

    def iterate(self):
        pass

    def activate(self):
        '''Called when this mode is foregrounded.'''
        self.matrix = RGBMatrix(options=options.matrix_options())
        self.do_activate()

    def deactivate(self):
        '''Called when this mode is removed from the foreground.'''
        self.do_deactivate()
        self.matrix.Clear()
        self.matrix = None

    def do_activate(self):
        pass

    def do_deactivate(self):
        pass

    def background_poll(self):
        if self.BACKGROUND_POLL_TIME is None:
            return

        now = time.time()
        if (not self.last_bg_poll or
                now - self.last_bg_poll >= self.BACKGROUND_POLL_TIME):
            self.last_bg_poll = now
            self.background_job()

    def background_job(self):
        pass
