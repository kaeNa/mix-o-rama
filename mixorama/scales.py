from multiprocessing import Queue
from threading import Thread, Event
import statistics
import warnings

from RPi import GPIO
from hx711 import HX711

from mixorama.util import make_timeout


class TimeoutFriendlyHX711(HX711):
    get_raw_data_timeout = None
    def get_raw_data(self, times=5, timeout=1000):
        self._validate_measure_count(times)

        data_list = []
        self.get_raw_data_timeout = self.get_raw_data_timeout or make_timeout(timeout)
        while len(data_list) < times:
            if self.get_raw_data_timeout():
                raise TimeoutError()

            data = self._read()
            if data not in [False, -1]:
                data_list.append(data)

        return data_list


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
        self._abort_event = Event()
        with warnings.catch_warnings(record=True) as w:
            self.hx711 = TimeoutFriendlyHX711(dout_pin=dout_pin, pd_sck_pin=pd_sck_pin, channel=channel, gain=gain)
            if len(w) > 0:
                print('{} ...when trying to setup scales on channels {} and {}'.format(w[0].message, dout_pin, pd_sck_pin), w[0])

    def reset(self):
        self.tare = self.measure()

    def measure(self):
        try:
            self.hx711.reset()   # Before we start, reset the HX711 (not obligate)
            measures = self.hx711.get_raw_data()
            return statistics.mean(measures) - self.tare
        except TimeoutError as e:
            raise ScalesTimeoutException from e

        finally:
            GPIO.cleanup()  # always do a GPIO cleanup in your scripts!

    def wait_for_weight(self, target, timeout=10000, tolerance=2):
        self._abort_event.clear()
        result_queue = Queue()

        def poller():

            def value_is_in_window(v):
                return target - target/100 * tolerance < v < target + target / 100 * tolerance

            time_is_out = make_timeout(timeout)
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
