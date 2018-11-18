from collections import defaultdict
from datetime import datetime
import logging


def make_timeout(delay_ms):
    starttime = datetime.now().timestamp()

    def time_is_out():
        return datetime.now().timestamp() > starttime + (delay_ms/1000)

    return time_is_out


class DefaultFactoryDict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError((key,))
        self[key] = value = self.default_factory(key)
        return value


class MaxObserver:
    value = 0

    def observe(self, observing):
        self.value = max(self.value, observing)
        return True
