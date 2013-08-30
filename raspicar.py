#!/usr/bin/python
import time
import subprocess

from datetime import datetime
from random import choice
from threading import Timer

from adafruit import Adafruit_CharLCDPlate
from cacher import cache


# a bit of settings
VIDEO_DESTINATION = "/home/pi/video"
ROOT_DEVICE = "/dev/root"
MAX_FPS = 6


def get_system_output(command):
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE,
                               shell=True)
    out, err = process.communicate()
    return out

def get_current_time():
    now = datetime.now()
    separator = ":" if now.second % 2 else " "
    return '%s%s%s' % (now.strftime("%H"), separator, now.strftime("%M"))

@cache(timeout=15)
def get_temperature():
    temp = get_system_output("/opt/vc/bin/vcgencmd measure_temp")
    temp = temp.replace('temp=', '').strip()
    return temp

@cache(timeout=60)
def get_free_disk_space():
    df = get_system_output("df -h %s | grep -v 'Filesystem' | awk '{ print $4 }'" % ROOT_DEVICE)
    df = df.strip()
    return df

def get_ip_address():
    return get_system_output("hostname -I")

def status_screen(message=''):
    """ Status screen """
    current_time = get_current_time()
    temp = get_temperature()
    disk_space = get_free_disk_space()

    line1 = '%-11s%5s' % (message[:10], current_time)
    line2 = '%-8s%8s' % (temp, disk_space)
    return '%s\n%s' % (line1, line2)

def network_status_screen():
    """ Network status screen """
    return '%s' % get_ip_address()

class VideoRecorder():
    _active = False
    _pid = None
    _timer = None
    _quality_map = {
        '1080.15': {'h': 1080, 'w': 1920, 'b': '15000000'},
        '720p.5': {'h': 720, 'w': 1280, 'b': '5000000'},
        '720p.2': {'h': 720, 'w': 1280, 'b': '2000000'},
        '720p.5': {'h': 720, 'w': 1280, 'b': '5000000'},
        '480p.4': {'h': 480, 'w': 854, 'b': '4000000'},
    }

    def _run_and_get_pid(self, command):
        """ Run command and return PID """
        process = subprocess.Popen(command, shell=True)
        return process.pid

    def stop(self):
        """ Stop video recoding immediately """
        self._timer.cancel()
        self._run_and_get_pid("kill -TERM %s" % self._pid)
        self._active = False
        print "recoder stopped"

    def start(self, quality, duration):
        """ Start recording a video of quality and duration """
        # organize params for raspivid command
        filename = '%s/%s_%s.h264' % (VIDEO_DESTINATION,
                                      quality,
                                      datetime.now().strftime("%Y.%m.%d_%H%M"))
        params = {"t": duration * 1000,
                  "filename": filename}
        params.update(self._quality_map.get(quality))
        raspivid = "raspivid -hf -vf -vs -w %(w)s -h %(h)s -fps 25 -b %(b)s -t %(t)s -o %(filename)s" % params
        print "raspivid command!", raspivid
    
        self._pid = self._run_and_get_pid("sleep 10")
        print "pid is", self._pid
        self._active = True
    
        # don't interrupt raspivid, it will finish itself
        # we're just interested when recording is finished
        self._timer = Timer(duration + 1, self.stop)
        self._timer.start()
        print "recorder started"

    def is_active(self):
        return self._active

if __name__ == '__main__':
    # initialize LCD
    lcd = Adafruit_CharLCDPlate.Adafruit_CharLCDPlate()
    lcd.begin(16, 2)

    # a bit of fancy colors
    colors = (lcd.ON , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.GREEN)

    # some variables to be set once
    lastTime = 0
    message = "Ready"

    # set random backlight color
    lcd.backlight(choice(colors))
    lcd.clear()

    #recorder = VideoRecorder()
    #recorder.start('720p', 5)

    # main cylce
    while True:
        # poll all buttons once, avoids repeated I2C traffic for different cases
        b = lcd.buttons()
        btn_up = b & (1 << lcd.UP)
        btn_down = b & (1 << lcd.DOWN)
        btn_left = b & (1 << lcd.LEFT)
        btn_right = b & (1 << lcd.RIGHT)
        btn_select = b & (1 << lcd.SELECT)
        
        if btn_up:
            message = "up"
        elif btn_down:
            message = "down"
        elif btn_left:
            message = "left"
        elif btn_right:
            message = "right"
        elif btn_select:
            message = "select"
        
        # update status message
        lcd.home()
        lcd.message(status_screen(message))
    
        # throttle frame rate, keeps screen legible
        while True:
            t = time.time()
            if (t - lastTime) > (1.0 / MAX_FPS): break
        lastTime = t
    

