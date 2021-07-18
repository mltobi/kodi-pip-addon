#!/usr/bin/python3
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import shutil
import json
import os
import subprocess

# addon infos
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')


# settings
m3ufile = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')) + "resources/data/channels.m3u"


# parse m3u file to dict
def parse_m3u(filename):

  name2link = {}

  # open m3u file and read all lines to a list
  fobj = open(filename, 'r', encoding='utf-8')
  lines = fobj.readlines()

  # #EXTINF:-1 logo="http://192.168.144.67:9981/imagecache/13" tvg-id="efa6b645f9399cc41becd20cceb0d2c2" tvg-chno="1",Das Erste HD
  # http://192.168.144.67:9981/stream/channelid/1169598191?profile=pass

  for i, line in enumerate(lines):
    # loop line list
    if line.find("tvg-chno=") != -1:
      # if line contains the channel label extract it
      parts = line.split("\",")

      if len(parts) > 1:
        # create a loopup dictionary key=channel-label and value=url-link
        name = parts[1].replace('\n', '')
        name2link[name] = lines[i+1].replace('\n', '')

  # return dictionary
  return name2link


# main
if __name__ == '__main__':

  xbmc.log('[pip-set-channel] Starting', xbmc.LOGINFO)

  if os.path.exists('/tmp/thumb.png'):
    # check if a captured image exists and remove it to clear a current running picture in picture display
    xbmc.log("Disabling current PIP display", xbmc.LOGINFO)
    try:
      os.remove('/tmp/thumb.png')
    except FileNotFoundError:
      pass
    try:
      os.remove('/tmp/channel.pip')
    except FileNotFoundError:
      pass

  else:
    # get all channels as dict: number -> http-url-link
    name2link = parse_m3u(m3ufile)

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
      xbmc.log("Enabling new PIP display", xbmc.LOGINFO)

      chnname = result['result']['item']['label']
      xbmc.log("Current channel: '%s'" % str(chnname), xbmc.LOGINFO)

      chnlink = name2link[chnname]
      xbmc.log("Channel link: '%s'" % str(chnlink), xbmc.LOGINFO)

      fobj = open('/tmp/channel.pip', 'w')
      fobj.write(chnlink)
      fobj.close()

      xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Channel: %s" % chnname, 3000, __icon__))

    except KeyError:
      pass

  del __addon__
  xbmc.log('[set-pip-channel] Finished', xbmc.LOGINFO)
