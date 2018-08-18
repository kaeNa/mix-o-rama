from time import sleep

from RPi import GPIO

from mixorama.bartender import Bartender
from mixorama.io import Button, Valve
from mixorama.recipes import Component, GIN_TONIC, CUBA_LIBRE
from mixorama.scales import Scales

#                               pin #3 is usable as output     which is BCM 2
#                               pin #5 is usable as output     which is BCM 3
# pin #7 is usable as input     pin #7 is usable as output     which is BCM 4
# pin #8 is usable as input     pin #8 is usable as output     which is BCM 14
# pin #10 is usable as input    pin #10 is usable as output    which is BCM 15
# pin #11 is usable as input    pin #11 is usable as output    which is BCM 17

# pin #12 is usable as input    pin #12 is usable as output    which is BCM 18
# pin #13 is usable as input    pin #13 is usable as output    which is BCM 27
# pin #15 is usable as input    pin #15 is usable as output    which is BCM 22
# pin #16 is usable as input    pin #16 is usable as output    which is BCM 23
# pin #18 is usable as input    pin #18 is usable as output    which is BCM 24
# pin #19 is usable as input    pin #19 is usable as output    which is BCM 10
# pin #21 is usable as input    pin #21 is usable as output    which is BCM 9
# pin #22 is usable as input    pin #22 is usable as output    which is BCM 25
# pin #23 is usable as input    pin #23 is usable as output    which is BCM 11
# pin #24 is usable as input    pin #24 is usable as output    which is BCM 8
# pin #26 is usable as input    pin #26 is usable as output    which is BCM 7
# pin #29 is usable as input    pin #29 is usable as output    which is BCM 5
# pin #35 is usable as input                                   which is BCM 19

GPIO.setmode(GPIO.BCM)
components = {
    Component.GIN: Valve(18),  # 12
    Component.TONIC: Valve(27),  # 13
    Component.RUM: Valve(22),  # 15
    Component.COLA: Valve(23),  # 16
    2: Valve(24),  # 18
    1: Valve(10),  # 19
}

scales = Scales(9, 25)  # pins 21, 22

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


abort_btn = Button(11, lambda: bar.abort() and print('Please discard the glass contents'))  # 23
gin_tonic_btn = Button(8, request_drink(GIN_TONIC))  # 24
cuba_libre_btn = Button(7, request_drink(CUBA_LIBRE))  # 26

Button(5, lambda: print('not assigned'))  # 29
Button(19, lambda: print('not assigned'))  # 35
# Button(15, lambda: print('not assigned'))  # 10
# Button(17, lambda: print('not assigned'))  # 11


print('Ready to make cocktails!')


while True:
    sleep(5)
