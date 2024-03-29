# Logitech G600 Driver For Linux

This repo contains scripts for a valid parser for the [Logitech G600 mouse](https://www.amazon.com/Logitech-Gaming-Backlit-Programmable-Buttons/dp/B0086UK7IQ). While most of the *mousing* is handled bu USB being itself, the 12 Button (+ G-Shift button) need proprietary [Logitech drivers](https://www.logitechg.com/en-us/innovation/g-hub.html) that aren't maintained for non Windows and Mac distributions. This aims to fix that. 

- [Logitech G600 Driver For Linux](#logitech-g600-driver-for-linux)
  - [Installation](#installation)
  - [G600D Unix Socket Protocol](#g600d-unix-socket-protocol)
    - [State](#state)
    - [Keycode](#keycode)
  - [G600 Profile Manager](#g600-profile-manager)
    - [Examples](#examples)
  - [Troubleshooting](#troubleshooting)
    - [I'm getting unintentional keyboard presses!](#im-getting-unintentional-keyboard-presses)

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

I created a profile manager to accompany this driver. It runs a command for every G button. The config file is a JSON file layed out like this:

```json
[
  {
    "name": "profile name",
    "color": "the color to show on the led panel e.x. #89abcd",
    "normal": { // actions to be performed without the G-Shift button
      "key code": {
        "key": "the key to press", // or
        "cmd": "a command to run"
      }
      // .
      // .
      // .
    },
    "mod": { // actions to be performed with the G-Shift button
      "key code": {
        "key": "the key to press", // or
        "cmd": "a command to run"
      }
      // .
      // .
      // .
    }
  }
]
```

### Examples

```json
[ 
  {
    "name": "i3",
    "color": "ff7869",
    "normal": {
      "10": { "key": "Super_L+f" },
      "11": { "key": "Shift_L+Super_L+Right" },
      "12": { "key": "Super_L+w" },
      "13": { "key": "Super_L+Return" },
      "14": { "key": "Super_L+c" },
      "16": { "key": "Super_L+Shift_L+space" },
      "17": { "key": "Super_L+h" },
      "18": { "key": "alt+backslash" },
      "19": { "cmd": "./.asciishrug.sh" },
      "20": { "key": "Super_L+Shift_L+r" },
      "9": { "key": "Shift_L+Super_L+Left" }
    },
    "mod": {
      "10": { "key": "Super_L+q" },
      "11": { "key": "Control_L+Super_L+Right" },
      "9": { "key": "Control_L+Super_L+Left" },
      "17": { "key": "Super_L+v" },
      "20": { "key": "Super_L+Shift_L+x" },
      "18": { "key": "Super_L+Shift_L+x" },
      "13": { "key": "playerctl play-pause" },
      "14": { "key": "playerctl next" },
      "12": { "key": "playerctl previous" }
    }
  },
]
```

## Troubleshooting

### I'm getting unintentional keyboard presses!

Easy solution:

1. Run `xinput` annd identify the id of the mouse's keyboard:

```bash
$ xinput 
⎡ Virtual core pointer                    	id=2	[master pointer  (3)]
⎜   ↳ Virtual core XTEST pointer              	id=4	[slave  pointer  (2)]
⎜   ↳ Logitech Gaming Mouse G600              	id=9	[slave  pointer  (2)]
⎜   ↳ Gaming KB  Gaming KB  Consumer Control  	id=13	[slave  pointer  (2)]
⎣ Virtual core keyboard                   	id=3	[master keyboard (2)]
    ↳ Virtual core XTEST keyboard             	id=5	[slave  keyboard (3)]
    ↳ Power Button                            	id=6	[slave  keyboard (3)]
    ↳ Power Button                            	id=7	[slave  keyboard (3)]
    ↳ USB PnP Audio Device                    	id=8	[slave  keyboard (3)]
    ↳ Gaming KB  Gaming KB                    	id=11	[slave  keyboard (3)]
    ↳ Gaming KB  Gaming KB  System Control    	id=12	[slave  keyboard (3)]
    ↳ Gaming KB  Gaming KB  Keyboard          	id=14	[slave  keyboard (3)]
    ↳ UVC Camera (046d:0825)                  	id=15	[slave  keyboard (3)]
    ↳ DAC-X6 DAC-X6                           	id=16	[slave  keyboard (3)]
    ↳ Gaming KB  Gaming KB  Consumer Control  	id=17	[slave  keyboard (3)]
    ↳ Logitech Gaming Mouse G600 Keyboard     	id=10	[slave  keyboard (3)] <-- It's this one
```

2. Run `xinput disable [the id of the mouse's keyboard device]`

This should disable the device as a keyboard but should still be avaliable for the daemon process.