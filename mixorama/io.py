from RPi import GPIO


class Button():
    def __init__(self, channel, callback=lambda: None):
        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(channel, GPIO.FALLING, callback=self._callback, bouncetime=400)
        self.cb = callback

    def _callback(self, channel):
        self.cb()


class Valve():
    def __init__(self, channel):
        self.channel = channel
        GPIO.setup(self.channel, GPIO.OUT)

    def open(self):
        GPIO.output(self.channel, 1)

    def close(self):
        GPIO.output(self.channel, 0)
