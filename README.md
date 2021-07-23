# kodi-pip-addon

## Description
PIP kodi addon provides a picture in picture feature for television channels from a tvheadend PVR server.

## Usage

### Show picture in picture
* if key "p" is pressed "long" during a television channel is displayed a picture in picture window is created at top left position.
* if the channels are switch the picture stays at configured position and shows every second a new snapshot image of the previous channel where "p" key was pressed.

### Hide picture in picture
* if key "p" is pressed a second time the picture in picuture windows is hidden again.

## Installation
* copy the one addon folders "service.pip" to "/storage/.kodi/addons"
* restart kodi
* after restart, kodi ask you to install the one new found addons

## How it works

### Installation
* a user keymap file "pipkeymap.xml" is added to "/storage/.kodi/userdata/keymaps"

### Function
* service addon "service.pip"
  * installs keymap
  * creates windows handle to add an image control
  * two image controls are used to allow update of the capture image every 0.5 seconds
  * monitor detects a notifyAll event if "p" key is press (see pipkeymap.xml)
  * a rpccmd is used to get the current channel label of the current shown channel
  * evals channel list file from tvheadend server and creates a lookup dictionary "channel name/label" -> "url link"
  * start a ffmpeg process with the url (on first "p" press)
  * stop a ffmpeg process (on seconed "p" press)

### Parameters
* PIP settings: position and size of image
* Tvheadend settings: username, password, server address and port

## Necessary tools
* ffmpeg version 4.4+ (e.g. from Libreelec addon repo)
* tvheadend server version 4.3+

