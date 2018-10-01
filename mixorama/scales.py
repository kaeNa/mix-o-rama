import logging
import os
from multiprocessing import Queue
from threading import Thread, Event
import statistics

from serial import Serial

from mixorama.util import make_timeout, BoolStabilizer

logger = logging.getLogger(__name__)


class ScalesTimeoutException(Exception):
    pass


class WaitingForWeightAbortedException(Exception):
    pass


class ScalesImpl:
    def __init__(self, portname, *args, **kwargs):
        self.port = Serial(portname, 115200, timeout=1)

    def reset(self):
        if not self.port.is_open:
            self.port.open()

        self.port.write('c1'.encode('ascii'))
        with self.port as p:
            l = 'waiting'
            while 'complete' not in l:
                logger.debug('serial scales: %s', l)
                l = p.readline().decode('ascii')

    def get_raw_data(self, n):
        data = []
        if not self.port.is_open:
            self.port.open()

        with self.port as p:
            for _ in range(n):
                l = p.readline().decode('ascii')
                if l.startswith('#'):
                    continue
                data.append(float(l))
        return data


if 'MIXORAMA_MOCK_SCALES' in os.environ:
    from random import randint

    logger.warning('Using mocked scales!')

    class MockScalesImpl:
        counter = 0

        def __init__(self, *args, **kwargs):
            pass

        def reset(self):
            self.counter = 0

        def get_raw_data(self, n):
            window = []

            for _ in range(n):
                v = self.counter - randint(50, 100)
                window.append(v)

            self.counter = window[-1]
            return window

    ScalesImpl = MockScalesImpl


def reject_outliers(data, stdev_multiplier=2):
    m = statistics.mean(data)
    s = statistics.stdev(data)
    filtered = [e for e in data if (m - stdev_multiplier * s < e < m + stdev_multiplier * s)]
    return filtered


class Scales:
    tare = 0

    def __init__(self,
                 portname='/dev/ttyACM0',
                 calibrated_1g=-2000.0
                 ):
        self._abort_event = Event()
        self.calibrated_1g = calibrated_1g
        self.scales = ScalesImpl(portname)

    def reset(self, tare=None):
        self.scales.reset()
        self.tare = tare or self._raw_measure()
        logger.info('set tare to %f', self.tare)

    def _raw_measure(self):
        measures = self.scales.get_raw_data(6)
        logger.debug('received measures at: %s', measures)

        mean = statistics.mean(measures)
        logger.debug('mean measurements: %f', mean)
        return mean

    def measure(self):
        try:
            no_tare = self._raw_measure() - self.tare
            logger.debug('no_tare: %f', no_tare)

            weight_in_gr = no_tare / self.calibrated_1g
            logger.debug('weight_in_gr: %f', weight_in_gr)

            return weight_in_gr

        except TimeoutError as e:
            raise ScalesTimeoutException from e

    def wait_for_weight(self, target, timeout=30000, stable_timeout=1000, on_progress=lambda d, s: None):
        self._abort_event.clear()
        result_queue = Queue()

        def poller():
            is_stable = BoolStabilizer(stable_timeout)
            time_is_out = make_timeout(timeout)

            v = self.measure()
            while not is_stable(v > target if target > 0 else v < target):
                if self._abort_event.is_set():
                    return result_queue.put(WaitingForWeightAbortedException())

                if time_is_out():
                    return result_queue.put(ScalesTimeoutException(v))

                v = self.measure()
                logger.info('got measurement: %f', v)
                on_progress(min(v, target), target)

            result_queue.put(v)

        Thread(target=poller, daemon=True).start()

        logger.info('waiting for a target weight of %f', target)
        result = result_queue.get(block=True)

        if isinstance(result, Exception):
            raise result

        return result

    def abort_waiting_for_weight(self):
        self._abort_event.set()
