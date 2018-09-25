import sys
import logging
import yaml

with open('mixorama.yaml') as cfg_file:
    cfg = yaml.load(cfg_file)

loglevel = cfg.get('logging', {}).get('level', 'INFO')
logging.basicConfig(stream=sys.stdout, level=getattr(logging, loglevel))
logging.error('test error')

from mixorama.factory import create_bartender, create_bar, create_menu, create_shelf
from mixorama.gui import gui, is_gui_available, config
from mixorama.ui import cli, bind_hw_buttons
from mixorama.io import cleanup

shelf = create_shelf(cfg.get('shelf'))
bar = create_bar(shelf, cfg.get('bar'))
bartender = create_bartender(bar, cfg.get('bartender'))
menu = create_menu(shelf, cfg.get('menu'))

try:
    bind_hw_buttons(menu, bartender, cfg.get('buttons', {}))

    if is_gui_available():
        config(cfg.get('kivy', {}))
        gui(menu, bartender)
    else:
        cli(menu, bartender)

finally:
    cleanup()
