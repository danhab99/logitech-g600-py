#!/usr/bin/env python3
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

import logging
import socket
import os
import argparse
import subprocess
import json
import asyncio

parser = argparse.ArgumentParser(description="The user process for Logitech G600")

parser.add_argument('-u', '--unix-socket', help="Path to UNIX socket", default='/tmp/g600.socket', metavar='unixsocket')
parser.add_argument('-l', '--log-file', help="Path to log file", default='/var/log/g600.log', metavar='logfile')
parser.add_argument('-c', '--config-file', help="Path to config file", required=True, metavar="configfile")

args = parser.parse_args()

LOCK_FILE="/tmp/g600.lock"

def claimLockfile():
  lockfile = open(LOCK_FILE, 'w')
  lockfile.write(str(os.getpid()))
  lockfile.close()

if os.path.exists(LOCK_FILE):
  lockfile = open(LOCK_FILE, 'r')
  oldpid = lockfile.readline()
  lockfile.close()
  if oldpid != '':
    try:
      os.kill(int(oldpid), 19)
    except OSError as e:
      if e.strerror == 'No such process': 
        claimLockfile()
      else:
        print('Unable to claim process lock, exiting')
        exit(1)

claimLockfile()

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

config=list()
Selected_Profile=0
Enable_Modifier=False

def readConfig():
  global config
  with open(args.config_file, 'r') as f:
    config = json.load(f)

def getSelectedProfile():
  global Selected_Profile
  global config
  return config[Selected_Profile]

def setColor():
  color = getSelectedProfile()["color"]
  info('Setting color to ' + color)
  subprocess.run('ratbagctl "Logitech Gaming Mouse G600" profile 0 led 0 set color ' + color, shell=True)

def setLight(state='on'):
  info('Turninng lights ' + state)
  subprocess.run('ratbagctl "Logitech Gaming Mouse G600" profile 0 led 0 set mode ' + state, shell=True)

def flickLight():
  setLight('off')
  setLight('on')

def changeProfile(d=1):
  global Selected_Profile
  global config
  Selected_Profile = Selected_Profile + d
  lenSection = len(config) - 1

  if Selected_Profile > lenSection:
    Selected_Profile = 0

  if Selected_Profile < 0:
    Selected_Profile = lenSection

  info('Switching to ' + getSelectedProfile()["name"])
  setColor()

async def RunCommand(cmd):
  proc = await asyncio.create_subprocess_shell(
    cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE)

  stdout, stderr = await proc.communicate()

  logging.info(f'[{cmd!r} exited with {proc.returncode}]')
  if stdout:
    logging.info(f'[stdout]\n{stdout.decode()}')
  if stderr:
    logging.info(f'[stderr]\n{stderr.decode()}')

class Event(LoggingEventHandler):
  def dispatch(self, event):
    info("Config changed")
    readConfig()
    for _ in range(3):
      flickLight()

readConfig()
observer = Observer()
observer.schedule(Event(), args.config_file, recursive=True)
observer.start()

def readSocket():
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  sock.connect(args.unix_socket)

  sockFile = sock.makefile()

  with sockFile:
    while True:
      yield sockFile.readline().strip()

setColor()
flickLight()
info('Ready')

for line in readSocket():
  pressed = line[0] == '-'
  code = line[1:]
  isModifer = code == 'MOD'

  info('code=%s pressed=%s isModifier=%s' % (code, str(pressed), str(isModifer)))

  if pressed and code == 'UP':
    changeProfile(1)
    continue
  
  if pressed and code == 'DOWN':
    changeProfile(-1)
    continue

  if isModifer:
    Enable_Modifier = pressed
    info('Modifier ' + str(pressed))
    continue

  try:
    profile = getSelectedProfile()
    
    if Enable_Modifier:
      keySet = profile["mod"]
    else:
      keySet = profile["normal"]

    action = keySet[code]

    if action:
      if "key" in action:
        if pressed:
          info("Pressed key " + action["key"])
          os.system("xdotool keydown %s" % (action["key"]))
        else:
          info("Released key " + action["key"])
          os.system("xdotool keyup %s" % (action["key"]))
      elif "cmd" in action:
        cmd = action["cmd"]
        info('Running command: ' + cmd)
        asyncio.run(RunCommand(cmd))
  except Exception as inst:
    error(str(inst))
