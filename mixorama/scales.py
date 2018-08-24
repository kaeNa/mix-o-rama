import logging
from multiprocessing import Queue
from threading import Thread, Event
import statistics
import warnings

from hx711 import HX711

from mixorama.util import make_timeout

logger = logging.getLogger(__name__)


class ScalesTimeoutException(Exception):
    pass


class WaitingForWeightAbortedException(Exception):
    pass


def reject_outliers(data, stdev_multiplier=2):
    m = statistics.mean(data)
    s = statistics.stdev(data)
    filtered = [e for e in data if (m - stdev_multiplier * s < e < m + stdev_multiplier * s)]
    return filtered


class Scales:
    tare = 0

    def __init__(self,
                 dout_pin=5,
                 pd_sck_pin=6,
                 channel='A',
                 gain=128,
                 calibrated_1g=-2000.0
                 ):
        self._abort_event = Event()
        self.calibrated_1g = calibrated_1g
        with warnings.catch_warnings(record=True) as w:
            self.hx711 = HX711(dout_pin=dout_pin, pd_sck_pin=pd_sck_pin, channel=channel, gain=gain)
            if len(w) > 0:
                logger.warn('%s ...when trying to setup scales on channel %d',
                            w[0].message, pd_sck_pin if w[0].lineno == 60 else dout_pin)

    def reset(self, tare=None):
        self.hx711.reset()   # Before we start, reset the HX711 (not obligate)
        self.tare = tare or self._raw_measure()
        logger.info('set tare to %f', self.tare)

    def _raw_measure(self):
        measures = self.hx711.get_raw_data(6)
        logger.debug('received measures at: %s', measures)

        no_spikes = reject_outliers(measures)
        logger.debug('removed spikes: %s', no_spikes)

        mean = statistics.mean(no_spikes)
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

    def wait_for_weight(self, target, timeout=30000, tolerance=2):
        self._abort_event.clear()
        result_queue = Queue()

        def poller():
            def value_is_in_window(v):
                lval = target - target / 100 * tolerance
                rval = target + target / 100 * tolerance
                retval = abs(lval) < abs(v) < abs(rval)
                logger.info('%f < %f < %f = %s', lval, v, rval, retval)
                return retval

            time_is_out = make_timeout(timeout)

            v = self.measure()
            while not value_is_in_window(v):
                if self._abort_event.is_set():
                    result_queue.put(WaitingForWeightAbortedException())
                if time_is_out():
                    result_queue.put(ScalesTimeoutException(v))
                v = self.measure()
                logger.debug('got measurement: %f', v)

            result_queue.put(v)

        Thread(target=poller).start()

        logger.info('waiting for a target weight of %f', target)
        result = result_queue.get(block=True)

        if isinstance(result, Exception):
            raise result

        return result

    def abort_waiting_for_weight(self):
        self._abort_event.set()
