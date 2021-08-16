#!/usr/bin/python3

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import os
import shutil
import json
import subprocess
import uuid
import urllib
from urllib.request import Request


# addon infos
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')


# files
keymapfilename = "pipkeymap.xml"
imagefilename = "thumb.png"


'''
Class XBMCMonitor
xbmc monitor with on notification handler
'''
class XBMCMonitor( xbmc.Monitor ):

    # constructor
    def __init__(self):
        self.keypressed = False


    # get last key status
    def get_keystatus(self):
        keypressed = self.keypressed
        self.keypressed = False
        return keypressed


    # call on a notification
    def onNotification(self, sender, method, data):

        if sender == "service.pip":
            if method == "Other.toggle_pip":
                xbmc.log("[pip-service] key press detected!", xbmc.LOGINFO)
                xbmc.log("[pip-service] via notifiyAll: sender=%s, method=%s, data=%s" % (str(sender), str(method), str(data)), xbmc.LOGDEBUG)
                self.keypressed = True


'''
Class M3U
handles m3u download, parsing and url request
'''
class M3U():

    # constructor
    def __init__(self, username, password, ipaddress, port, profile):
        self.username = username
        self.password = password
        self.ipaddress = ipaddress
        self.port = port
        self.m3ulines = None
        self.channel2url = {}
        self.url = ""
        self.channel = ""
        self.profile = profile


    # download m3u as pipe from tvheadend server
    def download(self):

        url = 'http://%s:%s/playlist/channels.m3u?profile=%s' % (self.ipaddress, self.port, self.profile)

        # urllib request with Digest auth
        hndlr_chain = []
        mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        mgr.add_password(None, url, self.username, self.password)
        hndlr_chain.append(urllib.request.HTTPDigestAuthHandler(mgr))

        # build request
        director = urllib.request.build_opener(*hndlr_chain)
        req = Request(url, headers={})

        try:
            # get request
            result = director.open(req)

            # read result ans split it to lines
            self.m3ulines = result.read().decode("utf-8").split("\n")
            xbmc.log("[pip-service] download m3u file with %d lines from %s." % (len(self.m3ulines), url), xbmc.LOGINFO)
        except urllib.error.HTTPError:
            xbmc.log("[pip-service] download of m3u file failed - HTTP error 403: forbidden to access %s." % (url), xbmc.LOGWARNING)
        except urllib.error.URLError:
            xbmc.log("[pip-service] download of m3u file failed - connection refused to %s." % (url), xbmc.LOGWARNING)


    # parse m3u file to dict
    def parse(self):

        # #EXTINF:-1 logo="http://192.168.144.67:9981/imagecache/13" tvg-id="efa6b645f9399cc41becd20cceb0d2c2" tvg-chno="1",Das Erste HD
        # http://192.168.144.67:9981/stream/channelid/1169598191?profile=pass

        self.channel2url = {}
        if self.m3ulines != None:
            for i, line in enumerate(self.m3ulines):
                # loop line list
                if line.find("logo=") != -1 and line.find("tvg-id=") != -1 and line.find("tvg-chno=") != -1:
                    # split line by tvg-chno
                    parts = line.split("tvg-chno")

                    if len(parts) > 1:
                        # split line by '",' to get channel name
                        parts = parts[1].split("\",")

                        if len(parts) > 1:
                            # create a loopup dictionary key=channel-name and value=url-link
                            name = parts[1].replace('\n', '')
                            self.channel2url[name] = self.m3ulines[i+1].replace('\n', '')

            xbmc.log("[pip-service] parsed %d channels." % len(self.channel2url), xbmc.LOGINFO)
            if len(self.channel2url) == 0:
                xbmc.log("[pip-service] check m3u file format to be:", xbmc.LOGDEBUG)
                xbmc.log("[pip-service] #EXTINF:-1 logo=\"...\" tvg-id=\"...\" tvg-chno=\"...\",[channel name]", xbmc.LOGDEBUG)
                xbmc.log("[pip-service] http://192.168.1.1:9981/stream/channelid/[....]?profile=%s" % self.profile, xbmc.LOGDEBUG)



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


'''
Class FFMPEG
controls ffmpeg process
'''
class FFMpeg():

    # constructor
    def __init__(self, imagefilename, tmpfolder, username, password, fps, addoptions, width):
        self.imagefile = tmpfolder + "/" + imagefilename
        self.tmpfolder = tmpfolder
        self.username = username
        self.password = password
        self.fps = fps
        self.addopts = addoptions
        self.width = width
        self.proc = ""
        self.urlold = ""
        self.flgStarted = False

        # remove "old" image file
        if os.path.exists(self.imagefile):
            os.remove(self.imagefile)


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

        # remove "old" thumb.png
        if os.path.exists(self.imagefile):
            os.remove(self.imagefile)

        self.flgStarted = False


    # started status
    def started(self):
        return self.flgStarted


    # start a ffmpeg process
    def start(self, url, restart):

        if (url != self.urlold and url != "") or restart:
            # if a new current link is requested generate url with username and password
            urlauth = url.replace('http://', 'http://%s:%s@' % (self.username, self.password))

            # terminate process that may be still running
            self.stop()

            # create ffmpeg command to capture very second a new image from the IPTV url
            cmd = ['ffmpeg',
                   '-nostdin',
                   '-i', urlauth,
                   '-an',
                   '-ss', '00:00:08.000',
                   '-f', 'image2',
                   '-vf', 'fps=%d,scale=%d:-1' % (self.fps, self.width),
                   '-qscale:v', '10',
                   '-y',
                   '-update', 'true',
                   '-vcodec', 'mjpeg',
                   '-atomic_writing', 'true',
                   self.imagefile]

            for item in self.addopts.split(' '):
                if item != '':
                    cmd.append(item)

            # create and run ffmpeg process with the defined command
            self.proc = subprocess.Popen(cmd,
              stdout = open('%s/pipffmpeg_stdout.log' % self.tmpfolder, 'w'),
              stderr = open('%s/pipffmpeg_stderr.log' % self.tmpfolder, 'a'))
            self.flgStarted = True

            # remember current link in order to wait for next new channel request
            self.urlold = url


'''
Class PIP
controls display of picture-in-picture
'''
class PIP():

    # constructor
    def __init__(self, imagefilename, keymapfile):

        self.imagefilename = imagefilename
        self.imagefile = "/tmp/" + imagefilename
        self.keymapfile = keymapfile
        self.uuidfile = None

        self.settings = {}
        self.imgHdl = None
        self.img = False

        self.x = 20
        self.y = 110
        self.w = 320
        self.h = 260

        self.winId = 12005
        self.winHdl = xbmcgui.Window(self.winId)


    # install keymap file
    def install(self):

        # path
        resourcepath = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')) + "resources/data/"
        keymappath = xbmcvfs.translatePath("special://home/userdata/keymaps/")

        # just during installation
        if not os.path.exists(keymappath + self.keymapfile):
            # add keymap
            shutil.copy(resourcepath + self.keymapfile, keymappath + self.keymapfile)


    # get addon settings
    def get_settings(self):

        # get addon settings and convert them to a dictionary
        if __addon__.getSetting('top') == 'true':
            self.settings['top'] = True
        else:
            self.settings['top'] = False

        if __addon__.getSetting('left') == 'true':
            self.settings['left'] = True
        else:
            self.settings['left'] = False

        self.settings['xgap'] = int(__addon__.getSetting('xgap'))
        self.settings['ygap'] = int(__addon__.getSetting('ygap'))
        self.settings['width'] = int(__addon__.getSetting('width'))
        self.settings['height'] = int(__addon__.getSetting('height'))
        self.settings['fps'] = int(__addon__.getSetting('fps'))
        self.settings['ipaddress'] = str(__addon__.getSetting('ipaddress'))
        self.settings['port'] = str(__addon__.getSetting('port'))
        self.settings['username'] = str(__addon__.getSetting('username'))
        self.settings['password'] = str(__addon__.getSetting('password'))
        self.settings['profile'] = str(__addon__.getSetting('profile'))
        self.settings['tmpfolder'] = str(__addon__.getSetting('tmpfolder'))
        self.settings['ffmpegopts'] = str(__addon__.getSetting('ffmpegopts'))

        self.imagefile = "%s/%s" % (self.settings['tmpfolder'], self.imagefilename)

        # define dimensions
        wwin = self.winHdl.getWidth()
        hwin = self.winHdl.getHeight()
        self.w = self.settings['width']
        self.h = self.settings['height']
        if self.settings['left']:
            self.x = self.settings['xgap']
        else:
            self.x = wwin - self.settings['xgap'] - self.w
        if self.settings['top']:
            self.y = self.settings['ygap']
        else:
            self.y = hwin - self.settings['ygap'] - self.h

        # return settings as dictionary
        return self.settings


    # display picture-in-picture image if avaiable
    def show_image(self):

        # get settings
        self.get_settings()

        # get current windows ID
        winId = xbmcgui.getCurrentWindowId()

        # if video fullscreen window ID
        if winId == self.winId and os.path.exists(self.imagefile):
            if not self.img:
                self.imgHdl = xbmcgui.ControlImage(self.x, self.y, self.w, self.h, self.imagefile)
                self.imgHdl.setAnimations([('visible', 'effect=fade end=100 time=300 delay=300',)])
                self.winHdl.addControl(self.imgHdl)
                self.img = True

            # add to latest captured image a unique id in order to force reload the image via setImage function
            olduuidfile = self.uuidfile
            self.uuidfile = self.imagefile.replace(".png", "%s.png" % str(uuid.uuid4()))
            shutil.copy(self.imagefile, self.uuidfile)

            # set new image file
            self.imgHdl.setImage(self.uuidfile, useCache = False)

            # remove already set image file if it exists
            if olduuidfile != None:
                if os.path.exists(olduuidfile):
                    os.remove(olduuidfile)


    def hide_image(self):
        # remove handle if windows ID has changed
        if self.img:
            self.winHdl.removeControl(self.imgHdl)
            del self.imgHdl
            self.img = False



'''
Main function
'''
if __name__ == '__main__':

    # init pip
    xbmc.log('[pip-service] Starting', xbmc.LOGINFO)
    pip = PIP(imagefilename, keymapfilename)

    # get settings
    settings = pip.get_settings()

    # init m3u
    m3u = M3U(settings['username'],
              settings['password'],
              settings['ipaddress'],
              settings['port'],
              settings['profile'])

    # download and parse channels
    m3u.download()
    m3u.parse()

    # start a xbmc monitor
    monitor = XBMCMonitor()

    # init ffmpeg
    ffmpeg = FFMpeg(imagefilename,
                    settings['tmpfolder'],
                    settings['username'],
                    settings['password'],
                    settings['fps'],
                    settings['ffmpegopts'],
                    settings['width'])


    # loop until monitor reports an abort
    sleeptime = float(1/settings['fps'])
    while not monitor.waitForAbort(sleeptime):

        if monitor.get_keystatus():
            if ffmpeg.started():
                # stop picture in picture capturing
                ffmpeg.stop()
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Stopping ...", 2000, __icon__))
                xbmc.log("[pip-service] stopped ffmpeg process.", xbmc.LOGDEBUG)

            else:
                # start picture in picture capturing using ffmpeg
                url, channel = m3u.get_url()
                if url == "":
                    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "No URL found ...", 1000, __icon__))
                    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Not started ...", 1000, __icon__))
                else:
                    ffmpeg.start(url, False)
                    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Starting ...", 5000, __icon__))
                    xbmc.log("[pip-service] started ffmpeg process.", xbmc.LOGDEBUG)

        if ffmpeg.started() and not ffmpeg.running():
            # restart ffmpeg
            ffmpeg.start(url, True)
            xbmc.log("[pip-service] re-started ffmpeg process for %s." % url, xbmc.LOGWARNING)

        if ffmpeg.started():
            # display picture-in-picture if a capture image from ffmpeg process is available
            pip.show_image()
        else:
            pip.hide_image()

    # stop ffmpeg process if running
    ffmpeg.stop()

    # clean up the rest
    del ffmpeg
    del m3u
    del monitor
    del pip
    del __addon__

    xbmc.log('[pip-service] Finished, exiting', xbmc.LOGINFO)
