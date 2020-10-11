#!/usr/bin/env python3
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

import logging
import socket
import sys
import os
import argparse
import subprocess
import configparser
import asyncio

parser = argparse.ArgumentParser(description="The user process for Logitech G600")

parser.add_argument('-u', '--unix-socket', help="Path to UNIX socket", default='/var/socket/g600', metavar='unixsocket')
parser.add_argument('-l', '--log-file', help="Path to log file", default='/var/log/g600.log', metavar='logfile')
parser.add_argument('-c', '--config-file', help="Path to config file", required=True, metavar="configfile")

args = parser.parse_args()

def claimLockfile():
  lockfile = open('/var/lock/g600', 'w')
  lockfile.write(str(os.getpid()))
  lockfile.close()

if os.path.exists('/var/lock/g600'):
  lockfile = open('/var/lock/g600', 'r')
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

config = configparser.ConfigParser()
config.read(args.config_file)
Selected_Profile=0
Enable_Modifier=False

def partialMatch(d, m, n=False):
  return { k : d[k] for k in d.keys() if (True in [i in k for i in m]) != n}

def getSelectedProfile(item=None):
  global Selected_Profile
  if item:
    block = config[config.sections()[Selected_Profile]]
    return partialMatch(block, item)
  else:
    return config.sections()[Selected_Profile]

def first(d):
  return d[list(d.keys())[0]]

def setColor():
  color = first(getSelectedProfile(['color']))
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
  Selected_Profile = Selected_Profile + d
  lenSection = len(config.sections()) - 1

  if Selected_Profile > lenSection:
    Selected_Profile = 0

  if Selected_Profile < 0:
    Selected_Profile = lenSection

  info('Switching to ' + getSelectedProfile())
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
    config.read(args.config_file)
    for i in range(3):
      flickLight()

observer = Observer()
observer.schedule(Event(), args.config_file, recursive=True)
observer.start()

def readSocket():
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  sock.connect(args.unix_socket)

  buffer = bytearray()
  while True:
    l = sock.recv(1)
    if l in b'\n':
      yield buffer.decode("utf8")
      buffer = bytearray()
    else:
      buffer += l

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
    c = getSelectedProfile(['down' if pressed else 'up', code])
    if len(c) > 0:
      c = partialMatch(c, ['mod'], not Enable_Modifier)

      if len(c) > 0:
        verb = list(c.keys())[0].split('_')[-1]
        cmd = c[list(c.keys())[0]]

        if verb == 'cmd' and pressed:
          info('Running command: ' + cmd)
          asyncio.run(RunCommand(cmd))
        
        if verb == "key":
          os.system("xdotool %s %s" % ("keydown" if pressed else "keyup", cmd))
          continue
    
  except Exception as inst:
    error(str(inst))