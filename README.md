## raspi-car

Raspberry Pi car camera coder with Adafruit LCD.

*Note*: I'm not sure if this project is usable anywhere outside my home dev environment.
Actually, it is not designed to be reusable and/or redistributable.

### Required hardware
* [Raspberry Pi Model B](http://www.raspberrypi.org/)
* [Adafruit 16x2 LCD with keypad](http://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/overview)
* [Raspberry Pi Camera](http://www.raspberrypi.org/camera)

### Installation
1. Make sure you have all required modules (for proper LCD functioning) loaded and I2C tools installed according to this [article](http://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage)
2. Checkout source code
3. Add raspicar.py to startup, i.e. simply into `/etc/rc.local`

### Todo
1. Recording
 * stop video from menu, well, that's what really needed
 * sync disk when recording is finished
 * select stabilization and w/b mode for camera

2. Menu
 * [Finite state machine](http://en.wikipedia.org/wiki/Finite-state_machine) for whole application: menu and state transitions, etc.
 * upload video to YouTube using menu (heh, that means that we need to authenticate somehow to youtube API and against user account)
 * delete/protect video from deletion from menu

3. Settings
 * auto save/load settings

4. Audio player
 * 16 x 2 mpd interface (play, pause, stop, next, previous)
 * automount usb stick (add to mpd collection, clean up mpd collection on removal)

5. Also
 * add RTC clock 

6. Fix bugs
 * for some reason video recording longer then 30 mins does not stop (raspivid bug?)
