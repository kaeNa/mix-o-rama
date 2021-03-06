"""All the config file interpreting, instance creation and configuring must be done in this module."""
import logging
from collections import OrderedDict
from typing import Dict

from mixorama.bartender import Bartender
from mixorama.io import Valve, io_init
from mixorama.recipes import Component, Recipe
from mixorama.scales import Scales
from mixorama.usage import UsageManager, configure_db
from mixorama.util import DefaultFactoryDict

logger = logging.getLogger(__name__)


class ComponentNotAvailable(Exception):
    pass


def create_bartender(bar, config):
    logger.debug('Initializing scales')
    scales = Scales(**config.get('scales', dict(port='/dev/ttyACM0', baudrate=115200)))

    logger.debug('Initializing compressor')
    compressor = Valve(config.get('compressor', 26))  # 37

    logger.debug('Waking up the bartender')
    bartender = Bartender(bar, compressor, scales)

    return bartender


def create_usage_manager(bartender, config):
    assert isinstance(config, dict)
    logger.debug('Connecting to usage db')
    db_url = config.get('db_url', 'sqlite:///usage.sqlite3')
    assert configure_db(db_url), 'can connect to usage db'
    usage_manager = UsageManager(bartender)
    return usage_manager


def create_shelf(config):
    shelf = DefaultFactoryDict(lambda n: Component(name=n))
    for name, properties in config.items():
        shelf[name] = Component(name=name, **properties)
    return shelf


def create_bar(shelf, config):
    logger.debug('Initializing GPIO')
    io_init()

    logger.debug('Initializing components')
    bar = {}
    for component_name, pin in config.items():
        bar[shelf[component_name]] = Valve(pin)
    return bar


def create_menu(bar, config: Dict[str, Dict[str, int]]):
    recipes = OrderedDict()
    available_components = dict([(c.name, c) for c in bar.keys()])
    for recipe_name, sequence in config.items():
        meta = sequence.pop('meta') if 'meta' in sequence else {}
        meta['name'] = meta.get('name', recipe_name)

        try:
            component_sequence = []
            for component_name, volume in sequence.items():
                if component_name not in available_components:
                    raise ComponentNotAvailable(component_name)

                component_sequence.append((available_components[component_name], volume))

            recipes[recipe_name] = Recipe(sequence=component_sequence, **meta)
        except ComponentNotAvailable as e:
            logger.warning('Cannot add {} to the menu, as it is not in the bar'.format(e.args[0]))

    return recipes
