#!/usr/bin/python3

'''
Copyright (C) 2021 mltobi

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import xbmc

import json
import urllib
from urllib.request import Request


'''
Class M3u
handles m3u download, parsing and url request
'''
class M3u:

    # constructor
    def __init__(self, username, password, ipaddress, port, profile):
        self.update_settings(username, password, ipaddress, port, profile)
        self.m3ulines = None
        self.channel2url = {}
        self.channel2number = {}
        self.number2channel = {}
        self.number2url = {}
        self.channel2id = {}
        self.url = ""
        self.channel = ""


    # update settings
    def update_settings(self, username, password, ipaddress, port, profile):
        self.username = username
        self.password = password
        self.ipaddress = ipaddress
        self.port = port
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
        self.channel2number = {}
        self.number2url = {}
        self.number2channel = {}
        if self.m3ulines != None:
            for i, line in enumerate(self.m3ulines):
                # loop line list
                if line.find("logo=") != -1 and line.find("tvg-id=") != -1 and line.find("tvg-chno=") != -1:
                    # split line by tvg-chno
                    parts = line.split("tvg-chno=")

                    if len(parts) > 1:
                        # split line by '",' to get channel name
                        pparts = parts[1].split("\",")

                        if len(pparts) > 1:
                            # create a loopup dictionary key=channel-name and value=url-link
                            name = pparts[1].replace('\n', '')
                            self.channel2url[name] = self.m3ulines[i+1].replace('\n', '')

                            # create a loopup dictionary key=channel-name and value=number
                            number = pparts[0].replace('"', '')
                            self.channel2number[name] = int(number)
                            self.number2channel[int(number)] = name
                            self.number2url[int(number)] = self.channel2url[name]

            xbmc.log("[pip-service] parsed %d channels." % len(self.channel2url), xbmc.LOGINFO)
            if len(self.channel2url) == 0:
                xbmc.log("[pip-service] check m3u file format to be:", xbmc.LOGDEBUG)
                xbmc.log("[pip-service] #EXTINF:-1 logo=\"...\" tvg-id=\"...\" tvg-chno=\"...\",[channel name]", xbmc.LOGDEBUG)
                xbmc.log("[pip-service] http://192.168.1.1:9981/stream/channelid/[....]?profile=%s" % self.profile, xbmc.LOGDEBUG)


    # get pip channel name
    def get_channel_name(self):
        return self.channel


    # set new channel name depending on channel number
    def set_channel_name(self, channelnumber):
        self.channel = self.number2channel[channelnumber]


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


    # get all channel ids
    def get_channel_ids(self):

        rpccmd = {"jsonrpc":"2.0","method": "PVR.GetChannels","params": {"channelgroupid": "alltv"},"id": 1}
        rpccmd = json.dumps(rpccmd)
        result = xbmc.executeJSONRPC(rpccmd)
        result = json.loads(result)

        channels = result['result']['channels']
        self.channel2id = {}
        for channel in channels:
            self.channel2id[channel['label']] = channel['channelid']


    # switch to channel
    def switch_channel(self, channelname):

        # get information for current player item as json reponse
        rpccmd = {"id" : 1,
                  "jsonrpc" : "2.0",
                  "method" : "Player.Open",
                  "params" : {
                      "item" : { "channelid" : self.channel2id[channelname] }
                   }
                 }
        rpccmd = json.dumps(rpccmd)
        xbmc.executeJSONRPC(rpccmd)
