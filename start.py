#!/usr/bin/perl
# -*- coding:utf-8 -*-

import subprocess
import pexpect
import time
from flask import Flask, request

MAC = 'FC:65:DE:AA:E2:6B'

class BluetoothCtl():
  def __init__(self):
    p = pexpect.spawn('bluetoothctl', echo=False)
    p.expect(['$'])
    self.process = p
  
  def send(self, command):
    self.process.send('{command}\n'.format(command=command))
  
  def info(self, dev):
    p = self.process
    info = {}
    self.send('info {dev}'.format(dev=dev))
    while True:
      result = p.expect([
        'Device (.+?)\r\n', 
        '\t+UUID: (.+?) +?\((.+?)\)\r\n',
        '\t+(.+?):(.+?)\r\n',
        '# $'
      ])
      if result == 1:
        key = p.match.group(1).decode()
        value = p.match.group(2).decode()
        info['UUID ' + key.strip()] = value.strip()
      elif result == 2:
        key = p.match.group(1).decode()
        value = p.match.group(2).decode()
        info[key.strip()] = value.strip()
      elif result == 3:
        break
      else:
        pass
    return info
  
  def connect(self, dev):
    self.send('connect {dev}'.format(dev=dev))
    pass
  
  def disconnect(self, dev):
    self.send('disconnect {dev}'.format(dev=dev))
    pass
  
  def quit(self):
    self.send('quit')

app = Flask(__name__)

def jtalk(outwav, speech):
  command = [
    '/usr/bin/open_jtalk',
    '-x', '/var/lib/mecab/dic/open-jtalk/naist-jdic',
    '-m', '/usr/share/hts-voice/miku/miku.htsvoice',
    '-ow', outwav
  ]
  p = subprocess.Popen(command, stdin=subprocess.PIPE)
  p.stdin.write(speech.encode('utf-8'))
  p.stdin.close()
  p.wait()
  return True

def aplay(wav):
  command = ['aplay', '-q', wav]
  subprocess.Popen(command)
  return True

def say(speech):
  wav = 'miku.wav'
  jtalk(wav, speech)
  aplay(wav)
  return speech

def ensureConnect():
  try:
    btctl = BluetoothCtl()
    info = btctl.info(MAC)
    if 'Connected' in info:
      if info['Connected'] == 'yes':
        return None
      else:
        btctl.connect(MAC)
        time.sleep(4)
        info = btctl.info(MAC)
        if info['Connected'] == 'yes':
          return '話せるようになったよ。'
        else:
          return 'スピーカーに接続できませんでした。'
    else:
      return 'スピーカーが見つかりません。'
  finally:
    btctl.quit()

@app.route('/say', methods=['POST'])
def handleSay():
  speech = request.form['speech']
  reconnected = ensureConnect()
  if reconnected:
    say(reconnected)
    time.sleep(3)
    speech = 'では、改めまして。' + speech
  return say(speech)

def main():
  app.run('127.0.0.1')

if __name__ == '__main__':
  main()
