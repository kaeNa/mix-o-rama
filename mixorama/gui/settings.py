import os

from kivy.clock import Clock
from kivy.input import MotionEvent
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from mixorama.bartender import Bartender, BartenderState
from mixorama.usage import UsageManager


class SettingsWidget(Screen):
    components = ObjectProperty(None)
    ''':type: kivy.uix.stacklayout.StackLayout'''
    restart_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    reboot_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    shutdown_btn = ObjectProperty(None)
    ''':type: kivy.uix.button.Button'''
    monitor_scales_chk = ObjectProperty(None)
    ''':type: kivy.uix.checkbox.CheckBox'''
    monitor_scales = ObjectProperty(None)
    ''':type: kivy.uix.label.Label'''

    scales_interval = None
    ''':type: ClockEvent'''
    scales_value = 0

    component_records = []
    ''':type: List[Tuple[mixorama.recipes.Component,Slider,Label]]'''

    def __init__(self, bartender: Bartender, usage_manager: UsageManager, **kw):
        super().__init__(**kw)
        self.bartender = bartender
        self.usage_manager = usage_manager
        self.restart_btn.bind(on_press=lambda *a: os.system('sudo service mixorama restart'))
        self.reboot_btn.bind(on_press=lambda *a: os.system('sudo reboot now'))
        self.shutdown_btn.bind(on_press=lambda *a: os.system('sudo shutdown now'))

        self.monitor_scales_chk.bind(active=self.on_monitor_scales_chk_active)
        self.monitor_scales.bind(on_touch_down=self.on_monitor_scales_press)

        self.build_component_sliders()

    def on_transition_state(self, screen, state):
        if state == 'in':
            self.refresh()
        else:
            self.monitor_scales_chk.active = False

    def on_monitor_scales_chk_active(self, chk, active):
        if active and self.bartender._sm_state == BartenderState.IDLE:
            self.scales_interval = Clock.schedule_interval(self.update_scales_monitor, 0.2)
        else:
            Clock.unschedule(self.scales_interval)

    def on_monitor_scales_press(self, lbl, t):
        """Press on the scales monitor sets the tare"""
        if not lbl.collide_point(*t.pos):
            return
        self.bartender.scales.reset(stabilize=False)
        self.update_scales_monitor()

    def update_scales_monitor(self, dt=None):
        self.scales_value = self.bartender.scales.measure(autostop=True)
        self.monitor_scales.text = '%.2f gr.' % self.scales_value

    def build_component_sliders(self):
        rows = len(self.bartender.components)

        for component in self.bartender.components.keys():
            value = component.volume - component.spent
            slider = Slider(size_hint=(7 / 8, 1 / rows), min=0, max=component.volume,
                            value=value)
            label = Label(size_hint=(1 / 8, 1 / rows), text=str(component))

            # hook for text autoresize
            label.bind(width=lambda bt, w: setattr(bt, 'text_size', (w*.85, None)))

            def update_component(target, value_or_touch, c=component, l=label, s=slider):
                if isinstance(value_or_touch, MotionEvent) and not target.collide_point(*value_or_touch.pos):
                    return

                if self.monitor_scales_chk.active:
                    value_for_label_press = self.scales_value * c.density  # scales gives us grams
                else:
                    value_for_label_press = c.volume  # ml

                value = value_or_touch if isinstance(target, Slider) else value_for_label_press

                l.text = str(c)
                c.fill(value)
                s.value = value

            slider.bind(value=update_component)
            label.bind(on_touch_move=update_component)
            label.bind(on_touch_up=update_component)
            self.component_records.append((component, slider, label))

            self.components.add_widget(label)
            self.components.add_widget(slider)

    def refresh(self):
        for c, s, l in self.component_records:
            s.value = c.volume - c.spent
