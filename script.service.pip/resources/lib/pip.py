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
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import shutil
import uuid


'''
Class PIP
controls display of picture-in-picture
'''
class PIP:

    # constructor
    def __init__(self, imagefilename, keymapfile):

        self.imagefilename = imagefilename
        self.imagefile = "/tmp/" + imagefilename
        self.keymapfile = keymapfile
        self.uuidfile = None

        self.settings = {}
        self.imgHdl = None
        self.img = False
        self.labelHdl = None
        self.channelnumber = 1

        self.x = 20
        self.y = 110
        self.w = 320
        self.h = 260

        self.winId = 12005
        self.winHdl = xbmcgui.Window(self.winId)


    # install keymap file
    def install(self):

        # path evaluation
        resourcepath = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')) + "resources/data/"
        keymappath = xbmcvfs.translatePath("special://home/userdata/keymaps/")

        # copy or overwrite keymap xml
        shutil.copy(resourcepath + self.keymapfile, keymappath + self.keymapfile)


    # get addon settings
    def get_settings(self, addon):

        # get addon settings and convert them to a dictionary
        if addon.getSetting('top') == 'true':
            self.settings['top'] = True
        else:
            self.settings['top'] = False

        if addon.getSetting('left') == 'true':
            self.settings['left'] = True
        else:
            self.settings['left'] = False

        self.settings['xgap'] = int(addon.getSetting('xgap'))
        self.settings['ygap'] = int(addon.getSetting('ygap'))
        self.settings['width'] = int(addon.getSetting('width'))
        self.settings['height'] = int(addon.getSetting('height'))
        self.settings['fps'] = int(addon.getSetting('fps'))
        self.settings['ipaddress'] = str(addon.getSetting('ipaddress'))
        self.settings['port'] = str(addon.getSetting('port'))
        self.settings['username'] = str(addon.getSetting('username'))
        self.settings['password'] = str(addon.getSetting('password'))
        self.settings['profile'] = str(addon.getSetting('profile'))
        self.settings['tmpfolder'] = str(addon.getSetting('tmpfolder'))
        self.settings['ffmpegopts'] = str(addon.getSetting('ffmpegopts'))

        self.imagefile = "%s/%s" % (self.settings['tmpfolder'], self.imagefilename)

        # return settings as dictionary
        return self.settings


    # display picture-in-picture image if avaiable
    def show_image(self):

        # get current windows ID
        winId = xbmcgui.getCurrentWindowId()

        # if video fullscreen window ID
        if winId == self.winId and os.path.exists(self.imagefile):
            if not self.img:
                # define dimensions
                wwin = self.winHdl.getWidth()
                hwin = self.winHdl.getHeight()
                xbmc.log("[pip-service] windows size: %d x %d" % (wwin, hwin), xbmc.LOGINFO)
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
                xbmc.log("[pip-service] x and y: %d x %d" % (self.x, self.y), xbmc.LOGINFO)

                # create image control
                self.imgHdl = xbmcgui.ControlImage(self.x, self.y, self.w, self.h, self.imagefile)
                self.imgHdl.setAnimations([('visible', 'effect=fade end=100 time=300 delay=300',)])

                # add image control to windows handle
                self.winHdl.addControl(self.imgHdl)

                # add channel number label control to windows handle
                self.labelHdl = xbmcgui.ControlLabel(self.x + 5, self.y, 125, 125, str(self.channelnumber))
                self.winHdl.addControl(self.labelHdl)

                self.img = True


            # set channel number label text
            self.labelHdl.setLabel(str(self.channelnumber))

            # add to latest captured image a unique id in order to force reload the image via setImage function
            olduuidfile = self.uuidfile
            self.uuidfile = self.imagefile.replace(".png", "%s.png" % str(uuid.uuid4()))
            try:
                # copy thumb.png to thumb[uuid].png
                shutil.copy(self.imagefile, self.uuidfile)

                # set new image file
                self.imgHdl.setImage(self.uuidfile, useCache = False)
            except FileNotFoundError:
                pass

            # remove already set image file if it exists
            if olduuidfile != None:
                if os.path.exists(olduuidfile):
                    os.remove(olduuidfile)


    def hide_image(self):
        # remove handle if windows ID has changed
        if self.img:
            self.winHdl.removeControl(self.imgHdl)
            del self.imgHdl
            self.winHdl.removeControl(self.labelHdl)
            del self.labelHdl
            self.img = False


    def set_channel_number(self, number):
        self.channelnumber = number
