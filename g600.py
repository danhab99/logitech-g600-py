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
    else:
      claimLockfile()
  else:
    claimLockfile()
else:
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

def getSelectedProfile(item=None):
  global Selected_Profile
  if item:
    return config[config.sections()[Selected_Profile]][item]
  else:
    return config.sections()[Selected_Profile]

def setColor():
  color = getSelectedProfile('color')
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

class Event(LoggingEventHandler):
  def dispatch(self, event):
    info("Config changed")
    config.read(args.config_file)
    for i in range(3):
      flickLight()

observer = Observer()
observer.schedule(Event(), args.config_file, recursive=True)
observer.start()

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(args.unix_socket)

setColor()
flickLight()
info('Ready')

while True:
  line = sock.recv(10)
  line = line.decode("utf-8").strip()

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

  cmdSelector = '%s_%s' % ('PRESSED' if pressed else 'RELEASED', code)

  if isModifer and pressed:
    Enable_Modifier = True
    info('Modifier enabled')
    continue

  if Enable_Modifier:
    cmdSelector = 'MODIFIED_' + cmdSelector

  if isModifer and not pressed:
    Enable_Modifier = False
    info('Modifier disabled')
    continue

  try:
    info('Selecting %s from %s' % (cmdSelector, getSelectedProfile()))
    cmd = getSelectedProfile(cmdSelector)
    info('Running command: ' + cmd)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    
    while True:
      output = process.stdout.readline()
      if process.poll() is not None:
        break
      if output:
        info('Subprocess: ' + str(output).strip())
    info('Subprocess exited with code ' + str(process.poll()))
      
  except Exception as inst:
    error(str(inst))