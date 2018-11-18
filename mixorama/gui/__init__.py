import os
import sys
import logging
logger = logging.getLogger(__name__)

# cmdline arguments, logger and config setup are handled by mixorama
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_NO_CONFIG"] = "1"

# kivy thinks too much of itself, really...
sys_stderr = sys.stderr
logging_root = logging.root
kivy_logger_setlevel = logging.getLogger('kivy').setLevel
logging.getLogger('kivy').setLevel = lambda level: None

from kivy.config import Config

# restoring fucked up python settings
sys.stderr = sys_stderr
logging.root = logging_root
logging.getLogger('kivy').setLevel = kivy_logger_setlevel

from os import path
from typing import Dict
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from mixorama.bartender import Bartender
from mixorama.gui.main import MainWidget
from mixorama.gui.settings import SettingsWidget
from mixorama.recipes import Recipe


def is_gui_available():
    try:
        from kivy.core.window import Window
        return Window is not None
    except Exception:
        return False


def gui_config(config: Dict[str, Dict[str, str]]):
    for section, section_settings in config.items():
        for option, value in section_settings.items():
            Config.set(section, option, value)


def gui_run(menu, bartender):
    BartenderGuiApp(menu, bartender).run()


class BartenderGuiApp(App):
    def __init__(self, menu: Dict[str, Recipe], bartender: Bartender, **kwargs):
        super(BartenderGuiApp, self).__init__(**kwargs)
        self.menu = menu
        self.bartender = bartender

    def build(self):
        dir = path.dirname(__file__)
        sm = ScreenManager()

        Builder.load_file(path.join(dir, 'main.kv'))
        sm.add_widget(MainWidget(self.menu, self.bartender, name='main'))

        Builder.load_file(path.join(dir, 'settings.kv'))
        sm.add_widget(SettingsWidget(self.bartender, name='settings'))

        return sm
