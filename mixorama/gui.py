import os
import sys
from os import path
from threading import Thread
from typing import Dict
import logging
logger = logging.getLogger(__name__)

from mixorama.bartender import Bartender, BartenderState, CocktailAbortedException
from mixorama.recipes import Recipe
from mixorama.statemachine import InvalidStateMachineTransition

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
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

# restoring fucked up python settings
sys.stderr = sys_stderr
logging.root = logging_root
logging.getLogger('kivy').setLevel = kivy_logger_setlevel

# Left-hand grid size constants
MENU_ROWS = 6
MENU_COLS = 3


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
        tpl_path = path.join(path.dirname(__file__), 'gui/layout.kv')
        Builder.load_file(tpl_path)
        return MainWidget(self.menu, self.bartender)


class TouchableButton(Button):
    def collide_point(self, x, y):
        parent = super(TouchableButton, self).collide_point(x, y)
        print('colliding touchable button @ ', x, y)
        return parent


class MainWidget(BoxLayout):
    menu_buttons = ObjectProperty(None)
    ''':type: kivy.uix.gridlayout.GridLayout'''
    image = ObjectProperty(None)
    ''':type: kivy.uix.image.Image'''
    total_progress = ObjectProperty(None)
    ''':type: kivy.uix.progressbar.ProgressBar'''
    step_progress = ObjectProperty(None)
    ''':type: kivy.uix.progressbar.ProgressBar'''
    abort_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    make_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    info_ul = ObjectProperty(None)
    ''':type: kivy.uix.label.Label'''
    info_ur = ObjectProperty(None)
    ''':type: kivy.uix.label.Label'''
    info_bl = ObjectProperty(None)
    ''':type: kivy.uix.label.Label'''
    info_br = ObjectProperty(None)
    ''':type: kivy.uix.label.Label'''

    staged_recipe = None
    ''':type: Recipe'''

    def __init__(self, menu: Dict[str, Recipe], bartender: Bartender, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.bartender = bartender
        self.menu = menu

        bartender.on_sm_transitions(
            enum=BartenderState,
            IDLE=self.on_idle,
            MAKING=self.on_making,
            READY=self.on_ready,
            POURING_PROGRESS=self.on_pouring_progress,
            ABORTED=self.on_abort
        )

        self.build_cocktail_buttons(menu)
        self.abort_btn.bind(on_press=self.on_abort_btn_press)
        self.make_btn.bind(on_press=self.on_make_btn_press)

        self.on_idle()
        self.stage_recipe(list(menu.values())[0])

    def build_cocktail_buttons(self, menu):
        for key, recipe in menu.items():
            b = Button(text=recipe.name,
                       size_hint=(1 / MENU_COLS, 1 / MENU_ROWS),
                       halign='center',
                       on_press=lambda *a, r=recipe: self.stage_recipe(r))

            # set text width to 85% of the button width
            b.bind(width=lambda bt, w: setattr(bt, 'text_size', (w*.85, None)))

            self.menu_buttons.add_widget(b)

    def stage_recipe(self, recipe: Recipe):
        self.staged_recipe = recipe
        self.set_cocktail_info(recipe)
        self.set_description_text(recipe.description)

        if recipe.image:
            self.image.source = recipe.image
        else:
            self.image.source = "mixorama/gui/logo.png"

    def set_cocktail_info(self, recipe: Recipe):
        self.info_ul.text = "Volume: {} ml\nStrength: {:.1f}%".format(
            recipe.volume(), recipe.strength())
        # self.info_ul.text = 'Volume: {} ml'.format(recipe.volume())
        # self.info_bl.text = 'Strength: {:.1f}%'.format(recipe.strength())

    def set_description_text(self, text):
        self.info_ur.text = text or ''

    def set_status_text(self, text):
        self.info_bl.text = text or ''

    def reset_progress(self, total=0, step=0):
        self.total_progress.value = total
        self.step_progress.value = step

    def on_abort_btn_press(self, target):
        try:
            self.bartender.abort()
        except InvalidStateMachineTransition as e:
            logger.exception(e)

    def on_make_btn_press(self, target):
        if self.staged_recipe:
            def maker():
                try:
                    self.bartender.make_drink(self.staged_recipe.sequence)
                    self.bartender.serve()
                except CocktailAbortedException:
                    self.bartender.discard()
                except Exception:
                    logger.exception('unhandled exception on_make_btn_press()-> maker()')

            Thread(daemon=True, target=maker).start()

    def on_idle(self):
        self.make_btn.disabled = False
        self.abort_btn.disabled = True
        self.set_status_text('Ready!')
        self.reset_progress()

    def on_making(self):
        self.make_btn.disabled = True
        self.abort_btn.disabled = False
        self.set_status_text('Making the drink..')
        self.reset_progress()

    def on_ready(self):
        self.reset_progress(100, 100)
        self.set_status_text('Take the glass')

    def on_abort(self):
        self.set_status_text("Cocktail aborted\nTake the glass")

    def on_pouring_progress(self, recipe, component, done, volume):
        recipe_progress = [c[0] for c in recipe].index(component) / len(recipe)
        self.total_progress.value = recipe_progress * 100
        self.step_progress.value = done / volume * 100
