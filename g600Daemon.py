#!/usr/bin/env python3
from evdev import InputDevice, categorize, ecodes
import threading
import logging
import socket
import sys
import os
import argparse

parser = argparse.ArgumentParser(description="The daemon process for reading inputs from a Logitech G600's programmable buttons to a unix socket")

parser.add_argument('-u', '--unix-socket', help="Path to UNIX socket", default='/var/socket/g600', metavar='unixsocket')
parser.add_argument('-l', '--log-file', help="Path to log file", default='/var/log/g600d.log', metavar='logfile')
parser.add_argument('-d', '--device-file', help="Path to device file", default='/dev/input/by-id/usb-Logitech_Gaming_Mouse_G600_FED1B7EDC0960017-if01-event-kbd', metavar='devfile')
parser.add_argument('--user', help='Demote socket owner for this user')

args = parser.parse_args()

if not os.geteuid() == 0:
  sys.exit("\nOnly root can run this script\n")

logging.basicConfig(
  format="%(asctime)s [%(levelname)s] %(message)s", 
  level=logging.INFO, 
  handlers=[
    logging.FileHandler(args.log_file),
    logging.StreamHandler()
  ]
)

info = logging.info
warn = logging.warn
error = logging.error

device = InputDevice(args.device_file)
server_address = args.unix_socket

keymap = {
  'KEY_A': '9', # G9
  'KEY_B': '10',
  'KEY_C': '11',
  'KEY_D': '12',
  'KEY_E': '13',
  'KEY_F': '14',
  'KEY_G': '15',
  'KEY_H': '16',
  'KEY_I': '17',
  'KEY_J': '18',
  'KEY_K': '19',
  'KEY_L': '20', # G20
  'KEY_M': 'UP', # Up
  'KEY_N': 'DOWN', # Down
  'KEY_P': 'MOD', # MOD
}

try:
  info('Unlinking old socket')
  os.unlink(server_address)
except OSError:
  if os.path.exists(server_address):
    warn('Socket still exists')
    raise

sockets = []

def sendAll(data):
  for socket in sockets:
    try:
      socket.sendall(data.encode())
    except Exception as e:
      socket.close()
      sockets.remove(socket)
      error(e)

def readDevice():
  info('Reading device')
  try:
    for event in device.read_loop():
      if event.type == ecodes.EV_KEY:
        cat = categorize(event)
        if cat.keystate != 2:
          if cat.keystate == 1:
            state = '-'
          else:
            state = '+'
          key = keymap[cat.keycode]

          gEvent = state + key + '\n'
          info(gEvent)
          sendAll(str(gEvent))
  except Exception as e:
    error(str(e))

def socketListener():
  info('Setting up socket')
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  sock.bind(server_address)
  sock.listen(1)

  if args.user:
    os.system('chown -R ' + args.user + ':' + args.user + ' ' + args.unix_socket)

  info('Listening')

  while True:
    try:
      conn, addr = sock.accept()
      info('New socket')
      sockets.append(conn)
    except Exception as e:
      error(str(e))

socketThread = threading.Thread(target=socketListener)
readingThread = threading.Thread(target=readDevice)

socketThread.start()
readingThread.start()

socketThread.join()
readingThread.join()
info('Ready!')
