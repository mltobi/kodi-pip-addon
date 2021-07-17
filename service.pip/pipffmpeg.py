#!/usr/bin/python3
import os
import subprocess
import time

# settings
username = 'hts'
password = 'ulster48'

# main
if __name__ == '__main__':

  chnlinkold = ''
  proc = None

  try:

    # run until cancelled by user
    while True:

      try:
        # open and read current picture in picture channel
        fobj = open('/tmp/channel.pip', 'r')
        chnlink = fobj.read()
        fobj.close()
      except FileNotFoundError:
        # if no current channel link is requested terminate last existing ffmpeg process
        chnlink = ""
        try:
          proc.kill()
        except:
          pass

      if chnlink != chnlinkold and chnlink != "":
        # if a new current link is requested generate url with username and password
        print('New link found: "%s"' % chnlink)
        url = chnlink.replace('http://', 'http://%s:%s@' % (username, password))

        # terminate process that may be still running
        try:
          proc.kill()
        except:
          pass

        # create ffmpeg command to capture very second a new image from the IPTV url
        cmd = ['ffmpeg', '-i', url, '-ss', '00:00:08.000',  '-f', 'image2', '-vf', 'fps=1,scale=320:-1', '-y', '-update', '1', '/tmp/thumb.png']

        # create and run ffmpeg process with the defined command
        proc = subprocess.Popen(cmd,
          stdout = open('/tmp/ffmpeg_stdout.log', 'w'),
          stderr = open('/tmp/ffmpeg_stderr.log', 'a'))

        # remember current link in order to wait for next new channel request
        chnlinkold = chnlink

      # repeat check for new link very second
      time.sleep(1)

  except KeyboardInterrupt:
    # if user cancelled the script terminate an existing ffmpeg process
    try:
      proc.kill()
    except:
      pass
