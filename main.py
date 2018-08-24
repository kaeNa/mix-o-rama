import sys
import time
from RPi import GPIO
import logging
from mixorama.bartender import Bartender
from mixorama.io import Button, Valve
from mixorama.recipes import Component, GIN_TONIC, CUBA_LIBRE
from mixorama.scales import Scales

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('mixorama')

GPIO.setmode(GPIO.BCM)

scales = Scales(4, 3)  # dout=7, sck=5

components = {
    Component.GIN: Valve(5),  # 29
    Component.TONIC: Valve(6),  # 31
    Component.RUM: Valve(13),  # 33
    Component.COLA: Valve(19),  # 35
    Component.TEQUILA: Valve(26),  # 37
    Component.COINTREAU: Valve(0),  # 39
}

bar = Bartender(components, scales)


def request_drink(recipe):
    def ui():
        print('Making a {}'.format(recipe))
        if bar.make_drink(recipe):
            print('Your drink is ready! Please take it from the tray')
            bar.serve()
        else:
            print('Could not make a drink')
    return ui


Button(12, lambda: bar.abort() and print('Please discard the glass contents'))  # 32

Button(23, request_drink(GIN_TONIC))  # 16
Button(24, request_drink(CUBA_LIBRE))  # 18
Button(25, lambda: print('not assigned'))  # 22
Button(8, lambda: print('not assigned'))  # 24
Button(7, lambda: print('not assigned'))  # 26
Button(1, lambda: print('not assigned'))  # 28


logger.info('Ready to make cocktails!')
try:
    while True:
        time.sleep(5)
finally:
    GPIO.cleanup()
