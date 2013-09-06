# -*- coding: utf-8 -*-
import subprocess
from datetime import datetime

from utils.watchdog import Watchdog
from devel.mocks import subprocess


class VideoRecorder(object):
    """ Pi Video Recoder class """
    _working_directory = ''
    _active = False
    _pid = None
    _timer_id = None
    
    _quality_map = {
        '1080p': {'w': 1920, 'h': 1080},
        '720p': {'w': 1280, 'h': 720},
        '480p': {'w': 854, 'h': 480},
    }
    
    def __init__(self, working_directory):
        self._working_directory = working_directory
        
    def _run_and_get_pid(self, command):
        """ Run command and return PID """
        process = subprocess.Popen(command, shell=True)
        return process.pid

    def stop(self):
        """ Stop video recoding immediately """
        self._run_and_get_pid('kill -TERM %s' % self._pid)
        self._active = False
        print 'recoder stopped'

    def start(self, quality, bitrate, duration):
        """ Start recording a video of quality and duration """
        # organize params for raspivid command
        filename = '%s/%s_%smbps_%s.h264' % (self._working_directory,
                                      quality,
                                      bitrate,
                                      datetime.now().strftime('%Y.%m.%d_%H%M'))
        params = {'filename': filename,
                  't': int(duration * 1000),
                  'b': int(bitrate * 10**6)}
        params.update(self._quality_map[quality])
        raspivid_command = 'raspivid --hflip --vflip --vstab --width %(w)s --height %(h)s --framerate 25 --bitrate %(b)s --timeout %(t)s --output %(filename)s' % params
    
        self._pid = self._run_and_get_pid(raspivid_command)
        print 'pid is', self._pid
        self._active = True
    
        # don't interrupt raspivid, it will finish itself
        # we're just interested when recording is finished
        self._timer_id = Watchdog.set_timeout(duration + 1, self.stop)
        print 'recorder started'

    def is_active(self):
        return self._active
