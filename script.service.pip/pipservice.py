#!/usr/bin/python3
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import os
import shutil
import json
import subprocess


# addon infos
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
 

# pathes and files
resourcepath = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')) + "resources/data/"
keymappath = xbmcvfs.translatePath("special://home/userdata/keymaps/")
keymapfile = "pipkeymap.xml"
imagefile = "/tmp/thumb.png"


# xbmc monitor with on notification handler
class XBMCMonitor( xbmc.Monitor ):

  flgStartFfmpeg = False

  def start_ffmpeg(self):
    return self.flgStartFfmpeg

  def onNotification(self, sender, method, data):

    xbmc.log("Notification detected! %s, %s, %s" % (str(sender), str(method), str(data)), xbmc.LOGDEBUG)
    if sender == "service.pip":
      if method == "Other.toggle_pip":
        if self.flgStartFfmpeg:
          self.flgStartFfmpeg = False
        else:
          self.flgStartFfmpeg = True


# handle m3u download, parsing and url request
class M3U():

  def __init__(self, username, password, ipaddress, port):
    self.username = username
    self.password = password
    self.ipaddress = ipaddress
    self.port = port
    self.channels = None
    self.channel2url = {}
    self.url = ""
    self.channel = ""


  def download(self):

    # get m3u channel file from tvheadend server
    cmd = ['curl', '-u', '%s:%s' % (self.username, self.password), 'http://%s:%s/playlist/channels.m3u?profile=pass' % (self.ipaddress, self.port)]

    # run curl command to get channels as m3u file
    proc = subprocess.Popen(cmd,
      stdout = subprocess.PIPE,
      stderr = open('/tmp/pipcurl_stderr.log', 'a'))
    channels = proc.communicate()

    self.channels = channels[0].decode("utf-8").split("\n")


  # parse m3u file to dict
  def parse(self):

    # #EXTINF:-1 logo="http://192.168.144.67:9981/imagecache/13" tvg-id="efa6b645f9399cc41becd20cceb0d2c2" tvg-chno="1",Das Erste HD
    # http://192.168.144.67:9981/stream/channelid/1169598191?profile=pass

    for i, line in enumerate(self.channels):
      # loop line list
      if line.find("tvg-chno=") != -1:
        # if line contains the channel label extract it
        parts = line.split("\",")

        if len(parts) > 1:
          # create a loopup dictionary key=channel-label and value=url-link
          name = parts[1].replace('\n', '')
          self.channel2url[name] = self.channels[i+1].replace('\n', '')


  # get current active channel the url of it
  def get_url(self):

    # get information for current player item as json reponse
    rpccmd = {
      "jsonrpc": "2.0", 
      "method": "Player.GetItem", 
      "params": { 
        "properties": ["art", "title", "album", "artist", "season", "episode", "duration", 
                        "showtitle", "tvshowid", "thumbnail", "file", "fanart","streamdetails"], 
        "playerid": 1 }, 
      "id": "OnPlayGetItem"}
    rpccmd = json.dumps(rpccmd)
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    try:
      # if a channel label exists create a new channel.pip file that contains the url link
      self.channel = result['result']['item']['label']
      self.url = self.channel2url[self.channel]

    except KeyError:
      self.url = ""

    return self.url, self.channel


# class to control FFMPEG 
class FFMpeg():

  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.proc = ""
    self.urlold = ""

  # check if ffmpeg process is running
  def running(self):
    try:
      ret = self.proc.poll() == None
    except AttributeError:
      ret = False
    return ret


  # stop ffmpeg process if running
  def stop(self):
    self.urlold = ""
    if self.running():
      self.proc.kill()


  # start a ffmpeg process
  def start(self, url):
    
    # if no current channel link is requested terminate last existing ffmpeg process
    if url == "":
      self.stop()

    if url != self.urlold and url != "":
      # if a new current link is requested generate url with username and password
      urlauth = url.replace('http://', 'http://%s:%s@' % (self.username, self.password))

      # terminate process that may be still running
      self.stop()

      # create ffmpeg command to capture very second a new image from the IPTV url
      cmd = ['ffmpeg', '-i', urlauth, '-ss', '00:00:08.000',  '-f', 'image2', '-vf', 'fps=1,scale=320:-1', '-y', '-update', '1', '/tmp/thumb.png']
      
      # create and run ffmpeg process with the defined command
      self.proc = subprocess.Popen(cmd,
        stdout = open('/tmp/pipffmpeg_stdout.log', 'w'),
        stderr = open('/tmp/pipffmpeg_stderr.log', 'a'))

      # remember current link in order to wait for next new channel request
      self.urlold = url


# get addon settings
def get_settings():

  settings = {}

  # get addon settings and convert them to a dictionary
  if __addon__.getSetting('top') == 'true':
    settings['top'] = True
  else:
    settings['top'] = False

  if __addon__.getSetting('left') == 'true':
    settings['left'] = True
  else:
    settings['left'] = False

  settings['xgap'] = int(__addon__.getSetting('xgap'))
  settings['ygap'] = int(__addon__.getSetting('ygap'))
  settings['width'] = int(__addon__.getSetting('width'))
  settings['height'] = int(__addon__.getSetting('height'))
  settings['ipaddress'] = str(__addon__.getSetting('ipaddress'))
  settings['port'] = str(__addon__.getSetting('port'))
  settings['username'] = str(__addon__.getSetting('username'))
  settings['password'] = str(__addon__.getSetting('password'))

  return settings


# main
if __name__ == '__main__':

  Once = True 

  xbmc.log('[pip-service] Starting', xbmc.LOGINFO)

  # just during installation
  if not os.path.exists(keymappath + keymapfile):
    # add keymap
    shutil.copy(resourcepath + keymapfile, keymappath + keymapfile)

  # remove "old" thumb.png
  if os.path.exists(imagefile):
    os.remove(imagefile)

  # get settings
  settings = get_settings()

  # init m3u
  m3u = M3U(settings['username'], settings['password'], settings['ipaddress'], settings['port'])

  # download and parse channels
  m3u.download()
  m3u.parse()
  
  # start a xbmc monitor
  monitor = XBMCMonitor()

  # init ffmpeg
  ffmpeg = FFMpeg(settings['username'], settings['password'])


  # loop until monitor reports an abort
  while not monitor.waitForAbort(1):

    # get settings
    settings = get_settings()

    if monitor.start_ffmpeg():
      # start picture in picture capturing using ffmpeg
      if not ffmpeg.running():
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Starting ...", 3000, __icon__))
        url, channel = m3u.get_url()
        ffmpeg.start(url)

    else:
      # stop picture in picture capturing
      if ffmpeg.running():
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Stopping ...", 3000, __icon__))
        ffmpeg.stop()

      # remove "old" thumb.png
      if os.path.exists(imagefile):
        os.remove(imagefile)


    # get current windows ID
    winId = xbmcgui.getCurrentWindowId()

    # if video fullscreen window ID
    if winId == 12005:

      # wait 0.5 seconds
      xbmc.sleep(500)

      if Once:
        # get windows handle just once
        winHdl = xbmcgui.Window(winId)
        Once = False
      else:
        try:
          # remove 2nd image control
          winHdl.removeControl(imgHdl2)
          del imgHdl2
        except:
          pass

      # get dimensions
      wwin = winHdl.getWidth()
      hwin = winHdl.getHeight()
      w = settings['width']
      h = settings['height']
      if settings['left']:
        x = settings['xgap']
      else:
        x = wwin - settings['xgap'] - w
      if settings['top']:
        y = settings['ygap']
      else:
        y = hwin - settings['ygap'] - h

      # create 1st image control
      imgHdl = xbmcgui.ControlImage(x, y, w, h, imagefile)

      # add 1st control to windows handle
      winHdl.addControl(imgHdl)

      # wait 0.5 seconds
      xbmc.sleep(500)

      # create 2nd image control
      imgHdl2 = xbmcgui.ControlImage(x, y, w, h, imagefile)

      # add 2nd control to windows handle
      winHdl.addControl(imgHdl2)

      # remove 1st control
      try:
        winHdl.removeControl(imgHdl)
        del imgHdl
      except:
        pass
    else:
      # remove handle if windows ID has changed
      try:
        winHdl.removeControl(imgHdl)
        del imgHdl
      except:
        pass
      try:
        winHdl.removeControl(imgHdl2)
        del imgHdl2
      except:
        pass

  # clean up windows objects
  try:
    winHdl.removeControl(imgHdl)
    del imgHdl
  except:
    pass
  try:
    winHdl.removeControl(imgHdl2)
    del imgHdl2
  except:
    pass

  # clean up the rest
  ffmpeg.stop()
  del ffmpeg
  del m3u
  del monitor
  del __addon__

  xbmc.log('[pip-service] Finished, exiting', xbmc.LOGINFO)
