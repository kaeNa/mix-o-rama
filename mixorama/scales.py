import logging
import os
from multiprocessing import Queue
from threading import Thread, Event
from random import randint
import statistics

from serial import Serial

from mixorama.util import make_timeout

SCALES_RESET_TIMEOUT = 5000
logger = logging.getLogger(__name__)


class ScalesException(Exception):
    pass


class ScalesTimeoutException(ScalesException):
    pass


class WaitingForWeightAbortedException(ScalesException):
    pass


class ScalesImpl:
    def __init__(self, *args, **kwargs):
        self.port = Serial(**kwargs)

    def reset(self):
        logger.debug('scales reset()')

        if not self.port.is_open:
            self.port.open()
            logger.debug('port open')

        self.port.flushInput()
        logger.debug('reset() complete')

    def get_raw_data(self, n):
        data = []
        if not self.port.is_open:
            self.port.open()
            logger.debug('port open')

        timeout = make_timeout(self.port.timeout * 1000)
        while len(data) < n:
            if timeout():
                raise ScalesTimeoutException('could not get raw data')

            raw_data = self.port.readline()
            logger.debug('get_data_raw() rcv: %s', raw_data)

            try:
                raw_line = raw_data.decode('ascii')
                if raw_line.startswith('#'):
                    continue

                data.append(float(raw_line))
            except ValueError:
                logger.exception('could not parse received data')
        return data

    def stop(self):
        logger.debug('port closed')
        self.port.close()


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

    def stop(self):
        pass


def reject_outliers(data, stdev_multiplier=2):
    m = statistics.mean(data)
    s = statistics.stdev(data)
    filtered = [e for e in data if (m - stdev_multiplier * s < e < m + stdev_multiplier * s)]
    return filtered


class Scales:
    tare = 0

    def __init__(self, port, calibrated_1g=-2000.0, measurements=1, **kwargs):
        self._abort_event = Event()
        self.calibrated_1g = calibrated_1g
        self.measurements = measurements

        if 'MOCK_SCALES' in os.environ:
            logger.warning('Using mocked scales!')
            self.scales = MockScalesImpl()
        else:
            self.scales = ScalesImpl(port=port, **kwargs)

    def reset(self, tare=None):
        self.scales.reset()
        self._raw_measure(6)  # skipping some data to stabilize
        self.tare = tare or self._raw_measure()
        logger.info('set tare to %f', self.tare)

    def _raw_measure(self, measurements=None):
        measures = self.scales.get_raw_data(measurements or self.measurements)
        mean = statistics.mean(measures)
        #logger.debug('mean measurements: %f', mean)
        return mean

    def measure(self):
        try:
            no_tare = self._raw_measure() - self.tare
            #logger.debug('no_tare: %f', no_tare)

            weight_in_gr = no_tare / self.calibrated_1g
            #logger.debug('weight_in_gr: %f', weight_in_gr)

            return weight_in_gr

        except TimeoutError as e:
            raise ScalesTimeoutException from e

    def wait_for_weight(self, target, timeout=20000, on_progress=lambda d, s: None):
        self._abort_event.clear()
        result_queue = Queue()

        def poller():
            logger.debug('started scales poller')
            time_is_out = make_timeout(timeout)
            try:
                v = self.measure()
                while not (v > target if target > 0 else v < target):
                    if self._abort_event.is_set():
                        return result_queue.put(WaitingForWeightAbortedException())

                    if time_is_out():
                        return result_queue.put(ScalesTimeoutException(v))

                    v = self.measure()
                    logger.debug('got measurement: %f', v)
                    on_progress(min(v, target), target)

                result_queue.put(v)
            except Exception as e:
                result_queue.put(e)
                raise

        Thread(target=poller, daemon=True).start()

        logger.info('waiting for a target weight of %f', target)
        result = result_queue.get(block=True)

        self.scales.stop()
        if isinstance(result, Exception):
            raise result

        return result

    def abort_waiting_for_weight(self):
        self._abort_event.set()
