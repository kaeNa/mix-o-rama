import logging
from typing import Dict

from mixorama.bartender import Bartender
from mixorama.io import Valve, io_init
from mixorama.recipes import Component, Recipe
from mixorama.scales import Scales
from mixorama.util import DefaultFactoryDict

logger = logging.getLogger(__name__)


class ComponentNotAvailable(Exception):
    pass


def create_bartender(bar, config):
    logger.debug('Initializing GPIO')
    io_init()
    logger.debug('Initializing scales')

    scales = Scales(**config.get('scales', dict(dout_pin=4,  pd_sck_pin=3)))  # dout=7, sck=5
    logger.debug('Initializing compressor')
    compressor = Valve(config.get('compressor', 26))  # 37

    logger.debug('Waking up the bartender')
    bartender = Bartender(bar, compressor, scales)

    return bartender


def create_shelf(config):
    shelf = DefaultFactoryDict(lambda n: Component(name=n))
    for name, properties in config.items():
        shelf[name] = Component(name=name, **properties)
    return shelf


def create_bar(shelf, config):
    logger.debug('Initializing components')
    bar = {}
    for component_name, pin in config.items():
        bar[shelf[component_name]] = Valve(pin)
    return bar


def create_menu(bar, config: Dict[str, Dict[str, int]]):
    recipes = {}
    for recipe_name, sequence in config.items():
        meta = sequence.pop('meta') if 'meta' in sequence else {}

        try:
            component_sequence = []
            for component_name, volume in sequence.items():
                if component_name not in bar:
                    raise ComponentNotAvailable(component_name)

                component_sequence.append((bar[component_name], volume))

            recipes[recipe_name] = Recipe(recipe_name, component_sequence, **meta)
        except ComponentNotAvailable as e:
            logger.warning('Cannot add {} to the menu, as it is not in the bar'.format(e.args[0]))

    return recipes
