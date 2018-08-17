import threading
from datetime import datetime
from multiprocessing import Queue
from threading import Thread
import statistics

from RPi import GPIO
from hx711 import HX711


class ScalesTimeoutException(Exception):
    pass


class WaitingForWeightAbortedException(Exception):
    pass


class Scales:
    tare = 0

    def __init__(self,
                 dout_pin=5,
                 pd_sck_pin=6,
                 channel='A',
                 gain=64):
        self._abort_event = threading.Event()
        self.hx711 = HX711(dout_pin=dout_pin, pd_sck_pin=pd_sck_pin, channel=channel, gain=gain)

    def reset(self):
        self.tare = self.measure()

    def measure(self):
        try:

            self.hx711.reset()   # Before we start, reset the HX711 (not obligate)
            measures = self.hx711.get_raw_data()
            return statistics.mean(measures) - self.tare

        finally:
            GPIO.cleanup()  # always do a GPIO cleanup in your scripts!

    def wait_for_weight(self, target, timeout=10000, tolerance=2):
        self._abort_event.clear()
        result_queue = Queue()

        def poller():
            starttime = datetime.now().timestamp()

            def time_is_out():
                return datetime.now().timestamp() > starttime + timeout

            def value_is_in_window(v):
                return target - target/100 * tolerance < v < target + target / 100 * tolerance

            v = self.measure()
            while not value_is_in_window(v):
                if self._abort_event.is_set():
                    result.put(WaitingForWeightAbortedException())
                if time_is_out():
                    result.put(ScalesTimeoutException(v))
                v = self.measure()

            return v

        Thread(target=poller).start()

        result = result_queue.get(block=True)

        if isinstance(result, Exception):
            raise result

        return result

    def abort_waiting_for_weight(self):
        self._abort_event.set()
