#!/usr/bin/perl
# -*- coding:utf-8 -*-

import os
import random
import subprocess
import pexpect
import time
from flask import Flask, request

if 'SPEAKER_MAC' not in os.environ:
  print('Environment SPEAKER_MAC must be set.')
  exit(1)

if 'PLAYLIST' not in os.environ:
  print('Environment PLAYLIST must be set.')
  exit(1)

MAC = os.environ['SPEAKER_MAC']
LIST_SONGS = os.environ['PLAYLIST']
VOLUME_SPEECH = -10
VOLUME_SING = -20

if 'TERM' not in os.environ:
  os.environ['TERM'] = 'xterm'

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

def mplay(audioFile, volume=0):
  command = ['mplayer',
             '-msglevel', 'all=0',
             '-af', 'volume={volume}'.format(volume=volume),
             '-nolirc', '-noconsolecontrols', audioFile]
  subprocess.Popen(command)
  return True

def say(speech):
  wav = 'miku.wav'
  jtalk(wav, speech)
  mplay(wav, volume=VOLUME_SPEECH)
  return speech

def sing(song):
  mplay(song, volume=VOLUME_SING)
  return song

def loadPlaylist(listFile):
  with open(listFile, 'r') as file:
    lines = file.readlines()
    songs = (line.split('\t') for line in lines)
    songs = {k.strip():v.strip() for k, v in songs}
    return songs

def requestSong(keyword=None, index=None):
  songs = loadPlaylist(LIST_SONGS)
  targets = [name for name in songs
             if keyword is None or keyword in name]
  if len(targets) > 0:
    if index is None:
      index = int(random.random() * len(targets))
    else:
      index = min(index, len(targets) - 1)
    name = targets[index]
    say(name)
    time.sleep(5)
    sing(songs[name])
    return name
  return 'no song'

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

@app.route('/sing', methods=['POST'])
def handleSing():
  keyword = None
  index = None
  if 'keyword' in request.form:
    keyword = request.form['keyword']
  if 'index' in request.form:
    try:
      index = int(request.form['index'])
    except ValueError as e:
      pass
  reconnected = ensureConnect()
  if reconnected:
    say(reconnected)
    time.sleep(3)
    speech = 'では、歌います。'
    say(speech)
  return requestSong(keyword=keyword, index=index)

def main():
  app.run('127.0.0.1')

if __name__ == '__main__':
  main()
