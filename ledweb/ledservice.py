#!/usr/bin/env python3

import time

import redis

from ledweb import options
from ledweb.servicemode.displaymode import DisplayMode
from ledweb.servicemode.timeweathermode import TimeWeatherMode


def redis_retry(ex):
    def wrap(func):
        def wrapper(*arg):
            while True:
                try:
                    func(*arg)
                except ex as e:
                    print('Error connecting to redis: {}'.format(e))
                    print('Sleeping for 5 seconds...')
                    time.sleep(5)
        return wrapper
    return wrap


class LedService:
    LOOP_SLEEP = 0.1

    def __init__(self, redis_cli, modes):
        self.redis_cli = redis_cli
        self.modes = [x() for x in modes]
        self.mode_map = {mode.MODE_NAME: i for i, mode in
                         enumerate(self.modes)}
        self.current_mode = None
        self.current_mode_idx = None

    def switch_mode(self, mode_idx, cmd=None):
        if self.current_mode:
            self.current_mode.deactivate()

        self.current_mode_idx = mode_idx
        if self.current_mode_idx is None:
            self.current_mode = None
        else:
            self.current_mode = self.modes[self.current_mode_idx]
            self.current_mode.activate()
            if cmd:
                self.current_mode.handle_command(cmd)

    def next_mode(self, incr):
        if self.modes:
            if self.current_mode_idx is None:
                new_mode_idx = 0 if incr > 0 else len(self.modes) - 1
            else:
                new_mode_idx = self.current_mode_idx + incr
            new_mode_idx %= len(self.modes)

            self.switch_mode(new_mode_idx, [])

    @redis_retry(redis.exceptions.ConnectionError)
    def loop(self):
        while True:
            while self.redis_cli.llen(options.REDIS_QUEUE) == 0:
                if self.current_mode:
                    self.current_mode.iterate()
                for mode in self.modes:
                    mode.background_poll()

                time.sleep(self.LOOP_SLEEP)
            msg = self.redis_cli.brpop([options.REDIS_QUEUE])

            cmd = msg[1].decode('utf-8').split()
            print('got cmd: {}'.format(cmd))
            if cmd[0] == 'next_mode':
                self.next_mode(1)
            elif cmd[0] == 'prev_mode':
                self.next_mode(-1)
            elif cmd[0] == 'off' or cmd[0] == 'clear':
                self.switch_mode(None)
            elif self.current_mode and (
                cmd[0] == self.current_mode.MODE_NAME or
                cmd[0] == 'mode'
            ):
                self.current_mode.handle_command(cmd[1:])
            elif cmd[0] in self.mode_map:
                self.switch_mode(self.mode_map[cmd[0]], cmd[1:])
            else:
                print('unknown command {}'.format(cmd))


def main():
    redis_cli = redis.from_url(options.REDIS_URL)
    modes = [DisplayMode, TimeWeatherMode]
    led_service = LedService(redis_cli, modes)
    led_service.loop()


if __name__ == '__main__':
    main()
