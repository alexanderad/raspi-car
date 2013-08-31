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

if __name__ == '__main__':
    # initialize LCD
    lcd = Adafruit_CharLCDPlate.Adafruit_CharLCDPlate()
    lcd.begin(16, 2)

    # a bit of fancy colors
    colors = (lcd.ON , lcd.GREEN, lcd.TEAL, lcd.GREEN)

    # some variables to be set once
    lastTime = 0
    state = "menu"
    message = "Ready"

    # set random backlight color
    lcd.backlight(choice(colors))
    lcd.clear()
    
    # create characters
    lcd.createChar(0, [0b0, 0b100, 0b1110, 0b11111, 0b0, 0b0, 0b0, 0b0]) # arrow up
    lcd.createChar(1, [0b0, 0b0, 0b0, 0b11111, 0b1110, 0b100, 0b0, 0b0]) # arrow down
    lcd.createChar(2, [0b0, 0b10, 0b110, 0b1110, 0b110, 0b10, 0b0, 0b0]) # arrow left
    lcd.createChar(3, [0b0, 0b1000, 0b1100, 0b1110, 0b1100, 0b1000, 0b0, 0b0]) # arrow right
    lcd.CHAR_ARROW_UP = '\x00'
    lcd.CHAR_ARROW_DOWN = '\x01'
    lcd.CHAR_ARROW_LEFT = '\x02'
    lcd.CHAR_ARROW_RIGHT = '\x03'
    
    # menu
    menu = {
        "level": [],
        "selected": 0,
        "items": [
            {
                "name": "Recording",
                "selected": 0,
                "items": [
                    {"name": "Record 1080p", "description": "15 Mbits"},
                    {"name": "Record 720p", "description": "7 Mbits"},
                    {"name": "Record 480p", "description": "4 Mbits"},
                ]
            },
            {
                "name": "Music",
            },
            {
                "name": "Information",
                "selected": 0,
                "items": [
                    {"name": "Network"},
                    {"name": "Disk space"},
                    {"name": "Version"},
                ]
            },
            {
                "name": "Settings",
                "selected": 0,
                "items": [
                    {
                        "name": "Backlight",
                        "selected": 0,
                        "items": [
                            {"name": "White", },
                            {"name": "Green", },
                            {"name": "Teal", },
                            {"name": "Yellow", },
                            {"name": "Red", },
                            {"name": "Violet", },
                            {"name": "Blue", },
                            {"name": "Off", },
                        ]
                    },
                    {
                        "name": "Video length",
                        "selected": 0,
                        "items": [
                            {"name": "5 mins"},
                            {"name": "10 mins"},
                            {"name": "20 mins"},
                            {"name": "30 mins"},
                            {"name": "60 mins"},
                        ]
                    }
                ]
            }
        ]
    }
    
    def redraw_menu(btn):
        
        # are we allowed to operate?
        if "menu" != state:
            return
        
        # first, allow to go up if it's possible and requested
        if btn == "up":
            if menu["level"]:
                menu["level"].pop()
                
        # second, go down to the selected item
        item = menu
        for level in menu["level"]:
            item = item["items"][level]
            
        # third, allow to go even lower, if it's possible and requested
        if btn in ["down", "select"]:
            if "items" in item["items"][item["selected"]]:
                menu["level"].append(item["selected"])
                item = item["items"][item["selected"]]
            
        # allow to go through items of this level
        if btn in ["left", "right"]:
            if "left" == btn:
                delta = -1
            if "right" == btn:
                delta = +1
            item["selected"] = (item["selected"] + delta) % len(item["items"])
        
        # prepare item meta to be printed to screen
        name = item["items"][item["selected"]]["name"]
        description = item["items"][item["selected"]].get("description", "")
        position = '%s%d/%d%s' % (lcd.CHAR_ARROW_LEFT,
                                  item["selected"] + 1, len(item["items"]),
                                  lcd.CHAR_ARROW_RIGHT)
        
        lcd.home()
        lcd.clear()
        line1 = '%-15s%1s' % (name, lcd.CHAR_ARROW_UP if menu["level"] else "")
        line2 = '%-11s%5s' % (description[:11], position)
        lcd.message('%s\n%s' % (line1, line2))
        
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
            redraw_menu("up")
        elif btn_down:
            redraw_menu("down")
        elif btn_left:
            redraw_menu("left")
        elif btn_right:
            redraw_menu("right")
        elif btn_select:
            message = "select"
            redraw_menu("123")
        
        if state == "idle":
            # update status message
            lcd.home()
            lcd.message(status_screen(message))
    
        # throttle frame rate, keeps screen legible
        while True:
            t = time.time()
            if (t - lastTime) > (1.0 / MAX_FPS): break
        lastTime = t
    

