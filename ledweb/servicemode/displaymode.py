import os

from PIL import Image

from ledweb import options
from ledweb.servicemode.ledservicemode import LedServiceMode


def to_int(i):
    try:
        i = int(i)
    except ValueError:
        i = 0
    return i


class DisplayMode(LedServiceMode):
    MODE_NAME = 'display'

    def setup(self):
        self.current_image = None

    @property
    def images(self):
        return sorted(os.listdir(options.IMAGES_DIR))

    def display_image(self, img_filename, x=0, y=0):
        # We want x and y to be the location in the image that is mapped to
        # the top left of the panel.  This means offsetting by the negative
        # values of x and y.
        x = to_int(x) * -1
        y = to_int(y) * -1

        path = os.path.join(options.IMAGES_DIR, os.path.basename(img_filename))
        if not os.path.isfile(path):
            return False
        image = Image.open(path)
        image.load()
        self.matrix.Clear()
        self.matrix.SetImage(image.convert('RGB'), x, y)
        self.current_image = img_filename

    def next_image(self, incr):
        cur_images = self.images
        try:
            next_image = cur_images[
                (cur_images.index(self.current_image) + incr)
                % len(cur_images)
            ]
        except ValueError:
            next_image = cur_images[0]
        self.display_image(next_image)

    def handle_command(self, cmd):
        if not self.images:
            return
        if not cmd:
            self.display_image(self.images[0])
        elif cmd[0] == 'image':
            self.display_image(*cmd[1:4])
        elif cmd[0] == 'next':
            self.next_image(1)
        elif cmd[0] == 'prev':
            self.next_image(-1)
        return True
