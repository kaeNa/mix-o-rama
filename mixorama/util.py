from collections import defaultdict
from datetime import datetime
import logging


def make_timeout(delay_ms):
    starttime = datetime.now().timestamp()

    def time_is_out():
        return datetime.now().timestamp() > starttime + (delay_ms/1000)

    return time_is_out


class BoolStabilizer:
    starttime = None

    def __init__(self, timeout=1000):
        self.timeout = timeout/1000

    def __call__(self, v):
        logger = logging.getLogger(__class__.__name__)

        timestamp = datetime.now().timestamp()
        if not v or not self.starttime:
            logger.debug('not true, resetting')
            self.starttime = timestamp
            return False
        elif timestamp - self.starttime < self.timeout:
            logger.info('not stable, waiting %f sec. more', self.timeout - (timestamp - self.starttime))
            return False

        logger.debug('finally stable')
        return True


class DefaultFactoryDict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError((key,))
        self[key] = value = self.default_factory(key)
        return value
