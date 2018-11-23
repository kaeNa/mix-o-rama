import os

from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from mixorama.bartender import Bartender


def refill_for_label(label, touch):
    if label.collide_point(*touch.pos):
        label.component.refill()
        label.slider.set_norm_value(1.0)


class SettingsWidget(Screen):
    components = ObjectProperty(None)
    ''':type: kivy.uix.stacklayout.StackLayout'''
    restart_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    reboot_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    shutdown_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''

    def __init__(self, bartender: Bartender, **kw):
        super().__init__(**kw)
        self.bartender = bartender
        self.restart_btn.bind(on_press=lambda *a: os.system('sudo service mixorama restart'))
        self.reboot_btn.bind(on_press=lambda *a: os.system('sudo reboot now'))
        self.shutdown_btn.bind(on_press=lambda *a: os.system('sudo shutdown now'))

    def on_transition_state(self, screen, state):
        if state == 'in':
            self.refresh()

    def refresh(self):
        self.components.clear_widgets()

        rows = len(self.bartender.components)

        for component in self.bartender.components.keys():
            slider = Slider(size_hint=(7 / 8, 1 / rows), min=0, max=component.volume,
                            value=component.volume - component.spent)
            slider.component = component
            slider.bind(value=lambda s, v: s.component.refill(v))

            label = Label(size_hint=(1 / 8, 1 / rows), text=component.name)
            label.bind(width=lambda bt, w: setattr(bt, 'text_size', (w*.85, None)))

            label.component = component
            label.slider = slider
            label.bind(on_touch_move=refill_for_label)
            label.bind(on_touch_up=refill_for_label)

            self.components.add_widget(label)
            self.components.add_widget(slider)
