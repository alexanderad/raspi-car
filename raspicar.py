#!/usr/bin/python
__version__ = "0.0.1"

import atexit
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
MENU_TIMEOUT = 10
VIDEO_LENGTH = 5 # in minutes



# quality chart for YouTube: https://support.google.com/youtube/answer/2853702?hl=uk
"""
 	        240p	    360p	    480p	    720p        1080p
Resolution	426 x 240	640 x 360   854x480	    1280x720    1920x1080	  	  	  	  
Maximum     700 Kbps    1000 Kbps   2000 Kbps   4000 Kbps   6000 Kbps
Recommended	400 Kbps	750 Kbps	1000 Kbps   2500 Kbps   4500 Kbps
Minimum     300 Kbps    400 Kbps    500 Kbps    1500 Kbps   3000 Kbps
"""


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
def get_free_disk_space(short=True):
    if short:
        df = get_system_output("df -h %s | grep -v 'Filesystem' | awk '{ print $4 }'" % ROOT_DEVICE)
    else:
        df = get_system_output("""df -h %s | awk '{ print $3 " " $4 " " $5}'""" % ROOT_DEVICE)
        
    df = df.strip()
    return df

def get_ip_address():
    return get_system_output("hostname -I")

def show_message(message):
    lcd.home()
    lcd.clear()
    lcd.message(message)
    
def set_video_length(mins):
    VIDEO_LENGTH = mins * 60

def show_info_network_screen():
    show_message('IP: %s' % get_ip_address())
    
def show_info_df_screen():
    show_message(get_free_disk_space(short=False))
    
def show_info_version_screen():
    show_message("raspi-car\n"
                 "Version: %s" % __version__)

def start_recording(quality, bitrate):
    print "going to start recording at", quality, "at bitrate", bitrate

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
    state = "idle"
    message = "Ready"
    menu_timer = Timer(0, lambda x: x, None)

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
                    {"name": "1080p @ 6 Mbps", "description": "High Q", "call": start_recording, "args": ['1080p', 6]},
                    {"name": "1080p @ 4.5 Mbps", "description": "Normal Q", "call": start_recording, "args": ['1080p', 4.5]},
                    {"name": "1080p @ 3 Mbps", "description": "Low Q", "call": start_recording, "args": ['1080p', 3]},
                    
                    {"name": "720p @ 4 Mbps", "description": "High Q", "call": start_recording, "args": ['720p', 4]},
                    {"name": "720p @ 2.5 Mbps", "description": "Normal Q", "call": start_recording, "args": ['720p', 2.5]},
                    {"name": "720p @ 1.5 Mbps", "description": "Low Q", "call": start_recording, "args": ['720p', 1.5]},
                    
                    {"name": "480p @ 2 Mbps", "description": "High Q", "call": start_recording, "args": ['480p', 2]},
                    {"name": "480p @ 1 Mbps", "description": "Normal Q", "call": start_recording, "args": ['480p', 1]},
                    {"name": "480p @ 0.5 Mbps", "description": "Low Q", "call": start_recording, "args": ['480p', 0.5]},
                ]
            },
            {
                "name": "Music",
            },
            {
                "name": "Info",
                "selected": 0,
                "items": [
                    {"name": "Network", "call": show_info_network_screen, "args": []},
                    {"name": "Disk space", "call": show_info_df_screen, "args": []},
                    {"name": "Version", "call": show_info_version_screen, "args": []},
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
                            {"name": "White", "call": lcd.backlight, "args": [lcd.WHITE]},
                            {"name": "Green", "call": lcd.backlight, "args": [lcd.GREEN]},
                            {"name": "Teal", "call": lcd.backlight, "args": [lcd.TEAL]},
                            {"name": "Yellow", "call": lcd.backlight, "args": [lcd.YELLOW]},
                            {"name": "Red", "call": lcd.backlight, "args": [lcd.RED]},
                            {"name": "Violet", "call": lcd.backlight, "args": [lcd.VIOLET]},
                            {"name": "Blue", "call": lcd.backlight, "args": [lcd.BLUE]},
                            {"name": "Off", "call": lcd.backlight, "args": [lcd.OFF]},
                        ]
                    },
                    {
                        "name": "Video",
                        "selected": 0,
                        "items": [
                            {"name": "5 mins", "call": set_video_length, "args": [5]},
                            {"name": "10 mins", "call": set_video_length, "args": [10]},
                            {"name": "20 mins", "call": set_video_length, "args": [20]},
                            {"name": "30 mins", "call": set_video_length, "args": [30]},
                            {"name": "60 mins", "call": set_video_length, "args": [60]},
                        ]
                    }
                ]
            }
        ]
    }
    
    # CRAP menu with global states
    def hide_menu():
        # boooooo
        global state
        global menu_timer
        state = "idle"
    
    def show_menu():
        # boooooo
        global state
        global menu_timer
        state = "menu"
        redraw_menu(None)
    
    def redraw_menu(btn):
        # boooooo
        global state
        global menu_timer
        
        if state != "menu": show_menu()
        
        # timers
        menu_timer.cancel()
        menu_timer = Timer(MENU_TIMEOUT, hide_menu)
        menu_timer.start()
        
        stop_select_propagation = False
        
        # first, allow to go up if it's possible and requested
        if btn == "up":
            if menu["level"]:
                menu["level"].pop()
                
        # second, go down to the selected item
        item, prev_item = menu, menu
        for level in menu["level"]:
            prev_item = item
            item = item["items"][level]
            
        # third, allow to go even lower, if it's possible and requested
        if btn in ["down", "select"]:
            if "items" in item["items"][item["selected"]]:
                menu["level"].append(item["selected"])
                prev_item = item
                item = item["items"][item["selected"]]
                stop_select_propagation = True
            
        # allow to go through items of this level
        if btn in ["left", "right"]:
            if "left" == btn:
                delta = -1
            if "right" == btn:
                delta = +1
            item["selected"] = (item["selected"] + delta) % len(item["items"])
        
        # prepare item meta to be printed to screen
        prev_name = ''
        name = item["items"][item["selected"]]["name"]
        description = item["items"][item["selected"]].get("description", "")
        if not description:
            if item != prev_item:
                prev_name = '%s%s' % (lcd.CHAR_ARROW_UP, prev_item["items"][prev_item["selected"]]["name"])
        position = '%s%d/%d%s' % (lcd.CHAR_ARROW_LEFT,
                                  item["selected"] + 1, len(item["items"]),
                                  lcd.CHAR_ARROW_RIGHT)
        
        lcd.home()
        lcd.clear()
        line1 = '%-16s' % (name, )
        line2 = '%-11s%5s' % (description or prev_name, position)
        lcd.message('%s\n%s' % (line1, line2))
        
        # finally process SELECT
        if btn == "select" and not stop_select_propagation:
            selected_item = item["items"][item["selected"]]
            if "call" in selected_item:
                func, args = selected_item["call"], selected_item["args"]
                func(*args)
            else:
                print "don't know what to do", selected_item
    
    # finall calls before going into main cycle
    show_menu()   
    
    # at exit
    def atexit_handler():
        global menu_timer
        menu_timer.cancel()
        lcd.clear()
        lcd.stop()
    
    atexit.register(atexit_handler)
    
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
            redraw_menu("select")
        
        if state == "idle":
            # update status message
            lcd.home()
            lcd.message(status_screen(message))
    
        # throttle frame rate, keeps screen legible
        while True:
            t = time.time()
            if (t - lastTime) > (1.0 / MAX_FPS): break
        lastTime = t
    

