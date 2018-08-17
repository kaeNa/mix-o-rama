from time import sleep

from RPi import GPIO

from mixorama.bartender import Bartender
from mixorama.io import Button, Valve
from mixorama.recipes import Component, GIN_TONIC, CUBA_LIBRE
from mixorama.scales import Scales

GPIO.setmode(GPIO.BCM)

components = {
    Component.GIN: Valve(11),
    Component.TONIC: Valve(13),
    Component.RUM: Valve(15),
    Component.COLA: Valve(19),
    # Component.XXXX: Valve(21),
    # Component.YYYY: Valve(23),
}

scales = Scales(0, 1)

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


abort_btn = Button(40, lambda: bar.abort() and print('Please discard the glass contents'))
gin_tonic_btn = Button(18, request_drink(GIN_TONIC))
cuba_libre_btn = Button(23, request_drink(CUBA_LIBRE))

Button(24, lambda: print('not assigned'))
Button(25, lambda: print('not assigned'))
Button(8, lambda: print('not assigned'))
Button(7, lambda: print('not assigned'))


while True:
    sleep(5)
