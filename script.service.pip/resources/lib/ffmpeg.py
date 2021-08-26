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

import os
import subprocess


'''
Class Ffmpeg
controls ffmpeg process
'''
class Ffmpeg:

    # constructor
    def __init__(self, imagefilename, tmpfolder, username, password, fps, addoptions, width):
        self.update_settings(tmpfolder, username, password, fps, addoptions, width)
        self.imagefile = tmpfolder + "/" + imagefilename
        self.proc = ""
        self.urlold = ""
        self.flgStarted = False

        # remove "old" image file
        if os.path.exists(self.imagefile):
            os.remove(self.imagefile)


    # update settings
    def update_settings(self, tmpfolder, username, password, fps, addoptions, width):
        self.tmpfolder = tmpfolder
        self.username = username
        self.password = password
        self.fps = fps
        self.addopts = addoptions
        self.width = width


    # test if ffmpeg is available
    def test(self):
        ret = False
        try:
            process = subprocess.Popen( ['ffmpeg', '-version'],
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
            process.communicate()
            exit_code = process.wait()
            if exit_code == 0:
                ret = True
            else:
                ret = False
        except FileNotFoundError:
            ret = False

        return ret


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

