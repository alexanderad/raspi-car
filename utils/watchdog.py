# -*- coding: utf-8 -*-
import time


class Watchdog(object):
    """
    Simple and very imprecise timer, which depends on main cycle frequency.
    It supposes that you have main loop on each tick of which you invoke
    process_timeouts() function. It also means that timeout will not be processed
    until processing function is called, i.e.: if you set timeout like 0.0001 and
    your main cycle tick occurs each 0.01 then your timer handler will be invoked
    100 (!) 0.0001's later than you expected :-)
    Still, it's usefull for not critical timeouts which count in seconds and simple
    enough not to deal with threads.
    """
    _timers = {}
    
    @classmethod
    def set_timeout(cls, timeout, func, *args, **kwargs):
        timer_id = len(cls._timers) + 1
        timer_data = {"func": func, 
                      "timeout": timeout,
                      "time_set": time.time(),
                      "args": args,
                      "kwargs": kwargs}
        cls._timers.update({timer_id: timer_data})
        return timer_id
        
    @classmethod
    def clear_timeout(cls, timer_id):
        if timer_id in cls._timers:
            cls._timers.pop(timer_id)

    @classmethod
    def process_timeouts(cls):
        time_now = time.time()
        for timer_id, timer_data in cls._timers.items():
            if (time_now - timer_data["time_set"]) > timer_data["timeout"]:
                timer_data["func"](*timer_data["args"], **timer_data["kwargs"])
                cls._timers.pop(timer_id)
