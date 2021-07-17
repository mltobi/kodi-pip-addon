# kodi-pip-addon

## Description
PIP kodi addon provides a picture in picture feature for television channels from a tvheadend PVR server.

## Usage

### Show picture in picture
* if key "p" is pressed "long" during a television channel is displayed a picture in picture window is created at top left position.
* if the channels are switch the picture stays at the top left position and shows every second a new snapshot of the previous channel the "p" key was pressed.

### Hide picture in picture
* if key "p" is pressed a second time the picture in picuture windows is hidden again.

## Installation
* copy the two addon folders "service.pip" and "script.pip.setchannel" to "/storage/.kodi/addons"
* restart kodi
* after restart, kodi ask you to install the two new found addons

## How it works

### Installation
* a user keymap file "pipkeymap.xml" is added to "/storage/.kodi/userdata/keymaps"
* a "autostart.sh" file is added or appended to "/storage/.config" that starts a script the control starting ffmpeg processes

### Function
* service addon "service.pip"
  * installs keymap and autostart.sh
    * TODO: append to autostart.sh if file already exists
  * creates windows handle to add an image control
  * two image controls are used to allow update of the capture image every 0.5 seconds
    * TODO: get new list of channels from tvheadend server using curl
* script addon "script.pip.setcahnnel"
  * script is called every long key press of "p"
  * a rpccmd is used to get the current channel label of the current shown channel
  * evals channel list file from tvheadend server and creates a lookup dictionary "channel name/label" -> "url link"
  * starts a ffmpeg process with the current url
  * kills running process if necessary, e.g. "p" key pressed a second time

### Parameters
* currently hardcoded ;-)
  * TODO: position and size of image
  * TODO: username and password for tvheadend access
  * TODO: tvheadend server address

## Necessary tools
* ffmpeg version 4.4+
* tvheadend server version 4.3+

## Restriction
* probably runs only wiht Libreelec 19.1+

