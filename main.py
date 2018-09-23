import sys
import logging
import yaml

from mixorama.factory import create_bartender, create_bar, create_menu, create_shelf
from mixorama.ui import cli, bind_hw_buttons
from mixorama.io import cleanup

with open('mixorama.yaml') as cfg_file:
    cfg = yaml.load(cfg_file)

loglevel = cfg.get('logging', {}).get('level', 'INFO')
logging.basicConfig(stream=sys.stdout, level=loglevel)

shelf = create_shelf(cfg.get('shelf'))
bar = create_bar(shelf, cfg.get('bar'))
bartender = create_bartender(bar, cfg.get('bartender'))
menu = create_menu(shelf, cfg.get('menu'))

try:
    bind_hw_buttons(menu, bartender, cfg.get('buttons', {}))
    cli(menu, bartender)
finally:
    cleanup()
