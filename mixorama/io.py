import logging
import warnings
from RPi import GPIO

logger = logging.getLogger(__name__)


class Button:
    def __init__(self, channel, callback=lambda: None):
        with warnings.catch_warnings(record=True) as w:
            GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            if len(w) > 0:
                logger.warn('{} ...when trying to setup button on channel {}'.format(w[0].message, channel))

        GPIO.add_event_detect(channel, GPIO.FALLING, callback=self._callback, bouncetime=200)
        self.cb = callback

    def _callback(self, channel):
        self.cb()


class Valve:
    def __init__(self, channel):
        self.channel = channel
        with warnings.catch_warnings(record=True) as w:
            GPIO.setup(self.channel, GPIO.OUT)
            if len(w) > 0:
                logger.warn('{} ...when trying to setup valve on channel {}'.format(w[0].message, self.channel))

        self.close()

    def open(self):
        GPIO.output(self.channel, 0)

    def close(self):
        GPIO.output(self.channel, 1)
