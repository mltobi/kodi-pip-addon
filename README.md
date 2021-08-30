# kodi-pip-addon <img src="https://github.com/mltobi/kodi-pip-addon/blob/main/script.service.pip/resources/icon.png" width="50"/>

**It is __highly recommended__ to use a ramdisk as temporary folder where the ffmpeg-captured images are stored!**
**If you do not use a ramdisk your lifetime of your harddisc will suffer!**

## Description
PIP kodi addon provides a picture in picture feature for television channels from a tvheadend PVR server.
          
## Usage

### Show and hide picture in picture
* if a user defined key (shift+p) is pressed during television channel is displayed a picture in picture window is created at a definable position.
* if the channel is switched to another channel the picture stays at configured position and shows with some frames per second a new snapshot image of the previous channel where "p" key was pressed.

### Hide picture in picture
* if the user defined key (shift+p) is pressed a second time the picture in picuture windows is hidden again and the current channel is kept.
* if another user defined key (shift+b) is pressed the picture in picture channel is hidden and the the player is switched back to this channel.

## Installation
* use "repositor.mltobi" to install the addon:
https://github.com/mltobi/repository.mltobi/archive/refs/tags/repository.mltobi-1.0.0.zip

## How it works

### Function
* service addon "script.service.pip"
  * monitor detects a notifyAll event on the user defined keys
  * requests a rpccmd to get the current channel name of the current displaced channel
  * evals channel list file from tvheadend server and creates a lookup dictionary "channel name/label" -> "url link"
  * starts a ffmpeg process with the url (on first key press)
  * creates windows handle to add an image control
  * image control is update with new captured images
  * stops a ffmpeg process (on second key press)

### Parameters
* PIP settings: position and size of image
* Tvheadend settings: username, password, server address and port
* Temporay folder to store the captured images (on linux /dev/shm is used because it is a user accessible ramdisk)
  * It is **highly recommended** to use a ramdisk as temporary folder where the ffmpeg-captured images are stored!
    * every captured image is stored to the temporary folder!
    * **if you do not use a ramdisk your lifetime of your harddisc will suffer!**
* Key definition (results in a keymap.xml file)

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


## Debugging / Logging
* check .kodi/temp/kodi.log
* check /dev/shm/pipffmpeg_stderr.log
* check thumb[uuid].png files in /dev/shm folder


## Successfully tested on
* Ubuntu 20.04.2 LTS 
  * kodi 20.0-ALPHA1 (19.90.101) Git:20210721-3fdf4542d2
  * ffmpeg 4.2.4-1ubuntu0.1
* Raspberry Pi4
  * LibreELEC (community): nightly-20210524-40e1be9 (RPi4.arm)
  * kodi 19.1 (19.1.0) Git:20210524-eea10b669c
  * ffmpeg version 4.4
