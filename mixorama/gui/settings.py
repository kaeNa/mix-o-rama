import os

from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from mixorama.bartender import Bartender


class SettingsWidget(Screen):
    components = ObjectProperty(None)
    ''':type: kivy.uix.stacklayout.StackLayout'''
    reboot_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''

    def __init__(self, bartender: Bartender, **kw):
        super().__init__(**kw)
        self.bartender = bartender
        self.reboot_btn.bind(on_press=lambda *a: os.system('sudo reboot now'))

    def on_transition_state(self, screen, state):
        if state == 'in':
            self.refresh()

    def refresh(self):
        self.components.clear_widgets()

        for component in self.bartender.components.keys():
            label = Label(size_hint=(1 / 8, 1 / 6), text=component.name)
            label.bind(width=lambda bt, w: setattr(bt, 'text_size', (w*.85, None)))

            slider = Slider(size_hint=(7 / 8, 1 / 6), min=0, max=component.volume,
                            value=component.volume - component.spent)
            slider.component = component
            slider.bind(value=lambda s, v: s.component.refill(v))

            self.components.add_widget(label)
            self.components.add_widget(slider)
