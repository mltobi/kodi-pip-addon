# kodi-pip-addon <img src="https://github.com/mltobi/kodi-pip-addon/blob/main/script.service.pip/resources/icon.png" width="50"/>

## Description
PIP kodi addon provides a picture in picture feature for television channels from a tvheadend PVR server.
          
## Usage

### Show and hide picture in picture
* if key "p" is pressed "long" during a television channel is displayed a picture in picture window is created at top left position.
* if the channels are switch the picture stays at configured position and shows every second a new snapshot image of the previous channel where "p" key was pressed.

### Hide picture in picture
* if key "p" is pressed a second time the picture in picuture windows is hidden again.

## Installation
* copy the one addon folders "script.service.pip" to "/storage/.kodi/addons"
* restart kodi
* after restart, kodi ask you to install the addon

## How it works

### Function
* service addon "service.pip"
  * installs keymap "pipkeymap.xml"
  * monitor detects a notifyAll event if "p" key is press (see pipkeymap.xml)
  * requests a rpccmd to get the current channel name of the current displaced channel
  * evals channel list file from tvheadend server and creates a lookup dictionary "channel name/label" -> "url link"
  * starts a ffmpeg process with the url (on first "p" press)
  * creates windows handle to add an image control
  * image control is update with new captured images
  * stops a ffmpeg process (on seconed "p" press)

### Parameters
* PIP settings: position and size of image
* Tvheadend settings: username, password, server address and port

### M3U file format
The m3u file downloaded from tvheadend server needs to have the following format:
```
#EXTINF:-1 logo="..." tvg-id="..." tvg-chno="1",Das Erste HD
http://192.168.1.1:9981/stream/channelid/....?profile=pass
```

## Dependencies
* kodi 19.x (matrix)
* ffmpeg version 4.4+ (e.g. from Libreelec addon repo)
* tvheadend server version 4.3+ with the possibiltiy of more parallel streams, e.g. via IPTV or more than two DVB inputs -> TV adapters


## Tested on following environments
* Ubuntu 20.04.2 LTS 
  * kodi 20.0-ALPHA1 (19.90.101) Git:20210721-3fdf4542d2
  * ffmpeg 4.2.4-1ubuntu0.1
  
  --> runs good
* Raspberry Pi4
  * LibreELEC (community): nightly-20210524-40e1be9 (RPi4.arm)
  * kodi 19.1 (19.1.0) Git:20210524-eea10b669c
  * ffmpeg version 4.4
  
  --> runs good
