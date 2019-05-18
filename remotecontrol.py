from selectors import DefaultSelector, EVENT_READ

import redis
from evdev import InputDevice, categorize, ecodes

import options


class RemoteControl:
    COMMAND_MAP = {
        'KEY_UP': 'next_mode',
        'KEY_DOWN': 'prev_mode',
        'KEY_RIGHT': 'mode next',
        'KEY_LEFT': 'mode prev',
        'KEY_HOME': 'clear',
    }

    def __init__(self):
        self.redis_cli = redis.from_url(options.REDIS_URL)

    def send_command(self, cmd):
        self.redis_cli.lpush(
            options.REDIS_QUEUE,
            cmd.encode('utf-8')
        )

    def loop(self):
        arrow_buttons = InputDevice('/dev/input/event0')
        control_buttons = InputDevice('/dev/input/event1')

        selector = DefaultSelector()
        selector.register(arrow_buttons, EVENT_READ)
        selector.register(control_buttons, EVENT_READ)

        while True:
            for key, mask in selector.select():
                device = key.fileobj
                for event in device.read():
                    if event.type != ecodes.EV_KEY:
                        continue
                    event_cat = categorize(event)
                    if event_cat.keystate != 0:
                        continue
                    try:
                        self.send_command(self.COMMAND_MAP[event_cat.keycode])
                    except KeyError:
                        pass


def main():
    rc = RemoteControl()
    rc.loop()


if __name__ == '__main__':
    main()
