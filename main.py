from time import sleep

from RPi import GPIO

from mixorama.bartender import Bartender
from mixorama.io import Button, Valve
from mixorama.recipes import Component, GIN_TONIC, CUBA_LIBRE
from mixorama.scales import Scales

GPIO.setmode(GPIO.BOARD)

components = {
    Component.GIN: Valve(1),
    Component.TONIC: Valve(2),
    Component.RUM: Valve(3),
    Component.COLA: Valve(4),
}

scales = Scales(5, 6)

bar = Bartender(components, scales)

gin_tonic_btn = Button(12, lambda: bar.make_drink(GIN_TONIC) or print('Could not make gin & tonic'))
cuba_libre_btn = Button(13, lambda: bar.make_drink(CUBA_LIBRE) or print('Could not make cuba libre'))

while True:
    sleep(5)
