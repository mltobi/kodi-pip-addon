#!/usr/bin/python3
import xbmc
import xbmcgui
import os
import shutil

# installation settings
resourcepath = "/storage/.kodi/addons/service.pip/resources/"
configpath = "/storage/.config/"
keymappath = "/storage/.kodi/userdata/keymaps/"
keymapfile = "pipkeymap.xml"
autostartfile = "autostart.sh"

# run settings
imagefile = "/tmp/thumb.png"
x = 20
y = 110
w = 280
h = 160

# main
if __name__ == '__main__':

  # just during installation
  if not os.path.exists(keymappath + keymapfile):
    shutil.copy(resourcepath + keymapfile, keymappath + keymapfile)

  if not os.path.exists(configpath + autostartfile):
    shutil.copy(resourcepath + autostartfile, configpath + autostartfile)
  else:
    fobj = open(configpath + autostartfile, "r")
    data = fobj.read()
    fobj.close()
    if data.find("pipffmpeg.sh") == -1:
      pass
      # TODO: append autostart.sh

  xbmc.log('[pip-service] Starting', xbmc.LOGINFO)
  Once = False 

  # start a xbmc monitor
  monitor = xbmc.Monitor()

  # loop until monitor reports an abort
  while not monitor.waitForAbort(1):

    # get current windows ID
    winId = xbmcgui.getCurrentWindowId()

    # if video fullscreen window ID
    if winId == 12005:

      # wait 0.5 seconds
      xbmc.sleep(500)

      if Once:
        # get windows handle just once
        winHdl = xbmcgui.Window(winId)
        Once = True
      else:
        # remove 2nd image control
        winHdl.removeControl(imgHdl2)
        del imgHdl2

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
      winHdl.removeControl(imgHdl)
      del imgHdl

    else:
      # remove handle if windows ID has changed
      try:
        winHdl.removeControl(imgHdl)
        del imgHdl
        Once = True
      except:
        pass
      try:
        winHdl.removeControl(imgHdl2)
        del imgHdl2
        Once = True
      except:
        pass

  # clean up al objects
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
  xbmc.log('[refresh-pip] Finished, exiting', xbmc.LOGINFO)

