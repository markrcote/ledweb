# ledweb: A web service for controlling an LED matrix :bulb:

This is a Python web service to control an LED matrix such as
Adafruit's [64x32 RGB LED matrix][].  It requires Python 3.

This app is released under the GPLv2 because its main [dependency][]
is also released under the GPLv2.

There are two main components and some auxiliary files:

* `ledservice.py`: Service that listens for messages from a
  Redis server and controls the LED matrix.

* `ledweb.py`: Flask app that supports uploading of images
  and passes commands to ledservice.

* `remotecontrol.py`: Service that receives commands from a remote
  control.  This was specifically written for the [OSMC remote control][]
  but likely works with others.

* `wsgi.py`, `ledweb.ini`: Simple NGINX WSGI server for ledweb.

* `requirements_ledweb.txt`, `requirements_ledservice.txt`: Python
  packages required for the respective services.

This app depends on a newish version of Henner Zeller's [rpi-rgb-led-matrix][]
library.  See in particular the part about building and installing
the [Python extension][].

Both `ledweb.py` and `ledservice.py` require a number of other Python
packages.  You'll probably want to use virtualenvs and install all
requirements in there.  Note that because you likely built the
`rgbmatrix` package locally, you'll have to use the
`--system-site-packages` argument to `virtualenv`.  You may want to
install the rest of the requirements with `pip -I` so that it
will not use local copies for anything else.  You may also wish to
create separate virtualenvs for `ledweb.py` and `ledservice.py`,
since the latter has to run as root.

Both services require access to a directory to hold images.  By
default this is `/var/run/ledweb/`.  You'll have to create that
directory and ensure it is readable and writeable by both services.

You can run `ledweb.py` as a systemd service (e.g. for [Raspbian][])
by creating a file, `/etc/systemd/system/ledweb.service`, which
contains something like this:

```
[Unit]
Description=uWSGI instance to serve ledweb
After=network.target
Wants=redis.service

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
}
```

Note that if you serve this app at a different path, you will also have to
update the `mount` variable in `ledweb.ini`.

Similarly, you can set up a systemd service for `ledservice.py`.  Note that
it must run as root to be able to talk to the LED panel.

```
[Unit]
Description=Redis-backed service to control an LED matrix
Wants=redis.service

[Service]
User=root
Group=root
WorkingDirectory=<path to ledweb directory>
Environment="PATH=<path to bin/ directory of ledservice's virtualenv>"
ExecStart==<path to bin/ directory of ledservices's virtualenv>/python ledservice.py

[Install]
WantedBy=multi-user.target
```

[dependency]: https://github.com/adafruit/rpi-rgb-led-matrix
[64x32 RGB LED matrix]: https://www.adafruit.com/product/2279
[OSMC remote control]: https://osmc.tv/store/product/osmc-remote-control/
[rpi-rgb-led-matrix]: https://github.com/hzeller/rpi-rgb-led-matrix
[Python extension]: https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python
[Raspbian]: https://www.raspbian.org/
