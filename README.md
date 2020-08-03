# Logitech G600 Driver For Linux

This repo contains scripts for a valid parser for the [Logitech G600 mouse](https://www.amazon.com/Logitech-Gaming-Backlit-Programmable-Buttons/dp/B0086UK7IQ). While most of the *mousing* is handled bu USB being itself, the 12 Button (+ G-Shift button) need proprietary [Logitech drivers](https://www.logitechg.com/en-us/innovation/g-hub.html) that aren't maintained for non Windows and Mac distributions. This aims to fix that. 

- [Logitech G600 Driver For Linux](#logitech-g600-driver-for-linux)
  - [Installation](#installation)
  - [G600D Unix Socket Protocol](#g600d-unix-socket-protocol)
    - [State](#state)
    - [Keycode](#keycode)
  - [G600 Profile Manager](#g600-profile-manager)
    - [Examples](#examples)

## Installation

1. This driver uses [libratbag](https://github.com/libratbag/libratbag) to interface with the mouse. Please follow [these instructions](https://github.com/libratbag/libratbag/wiki/Installation) to install `libratbag` and `ratbagctl`.

2. Then run `make install`. **BEWARE: THIS STEP WILL DESTROY ANY EXISTING BUTTON CONFIGURATION (your dpi settings should be safe)**

3. I recommend setting up `g600Daemon.py` as a systemd service add this service file to `/etc/systemd/system/g600.service`

```ini
[Unit]
Description=G600 keypad parser

[Service]
ExecStart=/usr/bin/python3 /[PATH TO REPO]/g600Daemon.py --user [YOUR USERNAME HERE]
Restart=on-failure
Type=simple

[Install]
WantedBy=multi-user.target
```

4. Setup the service like this:

```bash
sudo systemctl daemon-reload
sudo systemctl start g600.service
sudo systemctl enable g600.service
```

5. `g600.py` should be run at the user terminal level. Personally I have it setup in my i3 config.

## G600D Unix Socket Protocol

```bash
python3 g600Daemon.py --help
usage: g600Daemon.py [-h] [-u unixsocket] [-l logfile] [-d devfile] [--user USER]

The daemon process for reading inputs from a Logitech G600's programmable buttons to a unix socket

optional arguments:
  -h, --help            show this help message and exit
  -u unixsocket, --unix-socket unixsocket
                        Path to UNIX socket
  -l logfile, --log-file logfile
                        Path to log file
  -d devfile, --device-file devfile
                        Path to device file
  --user USER           Demote socket owner for this user
```

`g600Daemon.py` will open a [unix socket](https://en.wikipedia.org/wiki/Unix_domain_socket#:~:text=A%20Unix%20domain%20socket%20or,the%20same%20host%20operating%20system.) at `/var/socket/g600` (by default). Every line sent on the socket is formatted like this:

```
[State][Keycode]\n
```

### State

| Symbol | State |
|-|-|
| - | Key pressed |
| + | Key released |

### Keycode

| Keycode | Button |
|-|-|
| #9..22 | G9 through G20 |
| UP | The up button under the scroll wheel |
| DOWN | The down button under the scroll wheel |
| MOD | The G-Shift button next to right click |

## G600 Profile Manager

```bash
python3 g600.py --help 
usage: g600.py [-h] [-u unixsocket] [-l logfile] -c configfile

The user process for Logitech G600

optional arguments:
  -h, --help            show this help message and exit
  -u unixsocket, --unix-socket unixsocket
                        Path to UNIX socket
  -l logfile, --log-file logfile
                        Path to log file
  -c configfile, --config-file configfile
                        Path to config file
```

I created a profile manager to accompany this driver. It runs a command for every G button. The config file is laid out like this:

### Examples

```ini
[INSERT PROFILE NAME HERE]
color="ffaa11" #A hexadecimal color code to change the LEDs to when this profile is selected
[EVENT]=Command

# Examples:
PRESSED_9=notify-send 'test' # Posts a notification when G9 is pressed
MODIFIED_RELEASED_9=notify-send 'mod test' # Posts a notification when G-Shift is down and G9 is released

[Gaming Profile]
color="ffa200"
PRESSED_10=xdotool key r # G10 for reload
PRESSED_13=xdotool keydown v # Push to talk
RELEASED_13=xdotool keyup v # Stop push to talk
```

Config events work like this:

```
[MODIFIED/nothing for not modified]_[PRESSED/RELEASED]_[KEYCODE]=Command
```