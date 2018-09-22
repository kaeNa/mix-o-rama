import logging
import warnings

logger = logging.getLogger(__name__)

try:
    from RPi import GPIO

    def io_init():
        GPIO.setmode(GPIO.BCM)

    gpio_in = GPIO.IN
    gpio_out = GPIO.OUT
    gpio_pud_up = GPIO.PUD_UP
    gpio_falling = GPIO.FALLING
    gpio_setup = GPIO.setup
    gpio_add_event_callback = GPIO.add_event_callback
    gpio_add_event_detect = GPIO.add_event_detect
    gpio_output = GPIO.output
    cleanup = GPIO.cleanup

except RuntimeError:
    logger.warning('Could not import RPi.GPIO, using a mock!')

    stub = lambda name: lambda *args, **kwargs: \
        print('[stub] '+name, *args, *[k+':'+str(v)
                                              for k, v in kwargs.items()])

    gpio_in = gpio_out = gpio_pud_up = gpio_falling = None
    io_init = stub('io_init')
    gpio_setup = stub('gpio_setup')
    gpio_add_event_callback = stub('add_event_callback')
    gpio_add_event_detect = stub('add_event_detect')
    gpio_output = stub('output')
    cleanup = stub('cleanup')


class Button:
    def __init__(self, channel, callback=lambda: None):
        with warnings.catch_warnings(record=True) as w:
            gpio_setup(channel, gpio_in, pull_up_down=gpio_pud_up)
            if len(w) > 0:
                logger.warning('{} ...when trying to setup button on channel {}'.format(w[0].message, channel))

        gpio_add_event_detect(channel, gpio_falling, callback=self._callback, bouncetime=200)
        self.cb = callback

    def _callback(self, channel):
        self.cb()


class Valve:
    def __init__(self, channel):
        self.channel = channel
        with warnings.catch_warnings(record=True) as w:
            gpio_setup(self.channel, gpio_out)
            if len(w) > 0:
                logger.warning('{} ...when trying to setup valve on channel {}'.format(w[0].message, self.channel))

        self.close()

    def open(self):
        gpio_output(self.channel, 0)

    def close(self):
        gpio_output(self.channel, 1)
