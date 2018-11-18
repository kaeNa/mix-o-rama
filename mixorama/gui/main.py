import logging
from threading import Thread
from typing import Dict

from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from mixorama.bartender import Bartender, BartenderState, CocktailAbortedException
from mixorama.recipes import Recipe
from mixorama.statemachine import InvalidStateMachineTransition

logger = logging.getLogger(__name__)

# Left-hand grid size constants
MENU_ROWS = 4
MENU_COLS = 3


class MainWidget(Screen):
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
        super().__init__(**kwargs)
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

    def on_transition_state(self, screen, state):
        if state == 'in':
            self.on_idle()

    def build_cocktail_buttons(self, menu):
        for key, recipe in menu.items():
            b = Button(text=recipe.name,
                       size_hint=(1 / MENU_COLS, 1 / MENU_ROWS),
                       halign='center',
                       on_press=lambda b: self.stage_recipe(b.recipe))
            b.recipe = recipe

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
                    logger.info('Cocktail making or serving was aborted')
                    self.bartender.discard()
                except Exception:
                    logger.exception('Unhandled exception on_make_btn_press()-> maker()')

            Thread(daemon=True, target=maker).start()

    def on_idle(self):
        self.make_btn.disabled = False
        self.abort_btn.disabled = True

        for b in self.menu_buttons.children:
            b.disabled = not self.bartender.can_make_drink(b.recipe)

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
        recipe_progress = ([c[0] for c in recipe].index(component) + 1) / len(recipe)
        self.total_progress.value = recipe_progress * 100
        self.step_progress.value = done / volume * 100