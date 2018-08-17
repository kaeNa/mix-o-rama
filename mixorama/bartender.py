from enum import IntEnum, auto, unique
from typing import List, Dict, Tuple

from mixorama.io import Valve
from mixorama.recipes import Component
from mixorama.scales import Scales, ScalesTimeoutException, WaitingForWeightAbortedException
from mixorama.statemachine import sm_transition


@unique
class BartenderState(IntEnum):
    IDLE = auto()
    POURING = auto()
    READY = auto()


class Bartender:
    _sm_state = BartenderState.IDLE
    abort = None

    def __init__(self, components: Dict[Component, Valve], scales: Scales):
        self.components = components
        self.scales = scales

    @sm_transition(allowed_from=BartenderState.IDLE, when_done=BartenderState.READY,
                   while_working=BartenderState.POURING)
    def make_drink(self, recipe: List[Tuple[Component, int]]):
        for component, volume in recipe:
            if self.abort:
                return False

            self.scales.reset()
            self.components[component].open()
            try:
                self.scales.wait_for_weight(volume * component.density)
            except ScalesTimeoutException:
                print('something is wrong with the valve')
                raise
            except WaitingForWeightAbortedException:
                print('cocktail aborted')
                return False
            finally:
                self.components[component].close()

        return True

    @sm_transition(allowed_from=(BartenderState.POURING, BartenderState.READY), when_done=BartenderState.IDLE)
    def abort(self):
        self.abort = True
        self.scales.abort_waiting_for_weight()
