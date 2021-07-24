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
keymapfile = "pipkeymap.xml"
imagefile = "/tmp/thumb.png"


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
    def __init__(self, username, password, ipaddress, port):
        self.username = username
        self.password = password
        self.ipaddress = ipaddress
        self.port = port
        self.channels = None
        self.channel2url = {}
        self.url = ""
        self.channel = ""


    # download m3u as pipe from tvheadend server
    def download(self):

        url = 'http://%s:%s/playlist/channels.m3u?profile=pass' % (self.ipaddress, self.port)

        # get m3u channel file from tvheadend server
        cmd = ['curl', '-u', '%s:%s' % (self.username, self.password), url]

        # run curl command to get channels as m3u file
        proc = subprocess.Popen(cmd,
          stdout = subprocess.PIPE,
          stderr = open('/tmp/pipcurl_stderr.log', 'a'))
        channels = proc.communicate()

        self.channels = channels[0].decode("utf-8").split("\n")
        xbmc.log("[pip-service] download %d channel urls from %s." % (len(self.channels), url), xbmc.LOGINFO)


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


'''
Class FFMPEG
controls ffmpeg process
'''
class FFMpeg():

    # constructor
    def __init__(self, imagefile, username, password):
        self.imagefile = imagefile
        self.username = username
        self.password = password
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
            cmd = ['ffmpeg', '-i', urlauth, '-ss', '00:00:08.000',  '-f', 'image2', '-vf', 'fps=1,scale=320:-1', '-y', '-update', '1', self.imagefile]
            
            # create and run ffmpeg process with the defined command
            self.proc = subprocess.Popen(cmd,
              stdout = open('/tmp/pipffmpeg_stdout.log', 'w'),
              stderr = open('/tmp/pipffmpeg_stderr.log', 'a'))
            self.flgStarted = True

            # remember current link in order to wait for next new channel request
            self.urlold = url


'''
Class PIP
controls display of picture-in-picture
'''
class PIP():

    # constructor
    def __init__(self, imagefile, keymapfile):
        self.imagefile = imagefile
        self.keymapfile = keymapfile
        self.once = True
        self.settings = {}
        self.winHdl = None
        self.imgHdl = None
        self.imgHdl2 = None


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
        self.settings['ipaddress'] = str(__addon__.getSetting('ipaddress'))
        self.settings['port'] = str(__addon__.getSetting('port'))
        self.settings['username'] = str(__addon__.getSetting('username'))
        self.settings['password'] = str(__addon__.getSetting('password'))

        return self.settings


    # display picture-in-picture image if avaiable
    def show_image(self):

        # get settings
        self.get_settings()

        # get current windows ID
        winId = xbmcgui.getCurrentWindowId()

        # if video fullscreen window ID
        if winId == 12005:

            # wait 0.5 seconds
            xbmc.sleep(500)

            if self.once:
                # get windows handle just once
                self.winHdl = xbmcgui.Window(winId)
                self.once = False
            else:
                try:
                    # remove 2nd image control
                    self.winHdl.removeControl(self.imgHdl2)
                    del self.imgHdl2
                except:
                    pass

            # get dimensions
            wwin = self.winHdl.getWidth()
            hwin = self.winHdl.getHeight()
            w = self.settings['width']
            h = self.settings['height']
            if self.settings['left']:
                x = self.settings['xgap']
            else:
                x = wwin - self.settings['xgap'] - w
            if self.settings['top']:
                y = self.settings['ygap']
            else:
                y = hwin - self.settings['ygap'] - h

            # create 1st image control
            self.imgHdl = xbmcgui.ControlImage(x, y, w, h, self.imagefile)

            # add 1st control to windows handle
            self.winHdl.addControl(self.imgHdl)

            # wait 0.5 seconds
            xbmc.sleep(500)

            # create 2nd image control
            self.imgHdl2 = xbmcgui.ControlImage(x, y, w, h, self.imagefile)

            # add 2nd control to windows handle
            self.winHdl.addControl(self.imgHdl2)

            # remove 1st control
            try:
                self.winHdl.removeControl(self.imgHdl)
                del self.imgHdl
            except:
                pass
        else:
            # remove handle if windows ID has changed
            try:
                self.winHdl.removeControl(self.imgHdl)
                del self.imgHdl
            except:
                pass
            try:
                self.winHdl.removeControl(self.imgHdl2)
                del self.imgHdl2
            except:
                pass

'''
Main function
'''
if __name__ == '__main__':

    # init pip
    xbmc.log('[pip-service] Starting', xbmc.LOGINFO)
    pip = PIP(imagefile, keymapfile)

    # get settings
    settings = pip.get_settings()

    # init m3u
    m3u = M3U(settings['username'], settings['password'], settings['ipaddress'], settings['port'])

    # download and parse channels
    m3u.download()
    m3u.parse()
    
    # start a xbmc monitor
    monitor = XBMCMonitor()

    # init ffmpeg
    ffmpeg = FFMpeg(imagefile, settings['username'], settings['password'])


    # loop until monitor reports an abort
    while not monitor.waitForAbort(1):

        if monitor.get_keystatus():
            if ffmpeg.started():
                # stop picture in picture capturing
                ffmpeg.stop()
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Stopping ...", 2000, __icon__))
                xbmc.log("[pip-service] stopped ffmpeg process.", xbmc.LOGDEBUG)

            else:
                # start picture in picture capturing using ffmpeg
                url, channel = m3u.get_url()
                ffmpeg.start(url, False)
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, "Starting ...", 5000, __icon__))
                xbmc.log("[pip-service] started ffmpeg process.", xbmc.LOGDEBUG)

        if ffmpeg.started() and not ffmpeg.running():
            # restart ffmpeg
            ffmpeg.start(url, True)
            xbmc.log("[pip-service] re-started ffmpeg process for %s." % url, xbmc.LOGWARNING)

        # display picture-in-picture if a capture image from ffmpeg process is available
        pip.show_image()


    # stop ffmpeg process if running
    ffmpeg.stop()

    # clean up the rest
    del ffmpeg
    del m3u
    del monitor
    del pip
    del __addon__

    xbmc.log('[pip-service] Finished, exiting', xbmc.LOGINFO)
