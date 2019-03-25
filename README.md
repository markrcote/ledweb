# ledweb: A web service for controlling an LED matrix :bulb:

This is a Python web service to control an LED matrix such as
Adafruit's [64x32 RGB LED matrix][].

This app is released under the GPLv2 because its main [dependency][]
is also released under the GPLv2.

There are two main components and some auxiliary files:

* `ledservice.py`: This is a service that listens for messages from a
  Redis server and controls the LED matrix.

* `ledweb.py`: This is a Flask app that supports uploading of images
  and passes commands to ledservice.

* `wsgi.py`, `ledweb.ini`: Simple NGINX WSGI server for ledweb.

* `requirements_ledweb.txt`, `requirements_ledservice.txt`: Python
  packages required for the respective services.

This app depends on a newish version of Henner Zeller's [rpi-rgb-led-matrix][]
library.  See in particular the part about building and installing
the [Python extension][].

Both `ledweb.py` and `ledservice.py` require a number of other Python
packages.  You'll probably want to use virtualenvs and install all
requirements in there.

You can run `ledweb.py` as a systemd service (e.g. for [Raspbian][])
by creating a file, `/etc/systemd/system/ledweb.service`, which
contains something like this:

```
[Unit]
Description=uWSGI instance to serve ledweb
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=<path to ledweb directory>
Environment="PATH=<path to bin/ directory of ledweb's virtualenv>"
ExecStart=<path to bin/ directory of ledweb's virtualenv>/uwsgi --ini ledweb.ini

[Install]
WantedBy=multi-user.target
```

Enable the service with `sudo systemctl enable ledweb.service` and
start it with `sudo systemctl start ledweb.service`.

You can then serve the app from NGINX with a config entry like this:

```
location /led {
        include uwsgi_params;
        uwsgi_pass unix:<path to ledweb directory>/ledweb.sock;
        uwsgi_param SCRIPT_NAME /led;
        uwsgi_modifier1 30;
}
```

Unfortunately, my attempts at running `ledservice.py` as a systemd
service have resulted in my Raspberry Pi locking up shortly after the
service has started.  I'm guessing it's somehow related to execution
environment, but as of yet I have been unable to figure out the cause.
For now, I run the service in a screen session, as root, from the
`rpi-rgb-led-matrix` directory (see note above about why we have to
run from this directory), via `venv/bin/python ledservice.py` (replace
`venv/bin` with your virtualenv's `bin` directory if installed
somewhere other than `venv`).

Unfortunately this means that `ledservice.py` has to be started
manually after a reboot.  Perhaps switching to the main
rpi-rgb-led-matrix codebase will fix this.

[dependency]: https://github.com/adafruit/rpi-rgb-led-matrix
[64x32 RGB LED matrix]: https://www.adafruit.com/product/2279
[rpi-rgb-led-matrix]: https://github.com/hzeller/rpi-rgb-led-matrix
[Python extension]: https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python
[Raspbian]: https://www.raspbian.org/
