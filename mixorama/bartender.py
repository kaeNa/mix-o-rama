from enum import IntEnum, unique
from typing import List, Dict, Tuple

from mixorama.io import Valve
from mixorama.recipes import Component
from mixorama.scales import Scales, ScalesTimeoutException, WaitingForWeightAbortedException
from mixorama.statemachine import sm_transition

GLASS_WEIGHT = 150  # grams
USER_TAKE_GLASS_TIMEOUT = 60  # sec


@unique
class BartenderState(IntEnum):
    IDLE = 1
    POURING = 2
    READY = 4


class Bartender:
    _sm_state = BartenderState.IDLE
    _abort = None

    def __init__(self, components: Dict[Component, Valve], scales: Scales):
        self.components = components
        self.scales = scales

    @sm_transition(allowed_from=BartenderState.IDLE, when_done=BartenderState.READY,
                   while_working=BartenderState.POURING)
    def make_drink(self, recipe: List[Tuple[Component, int]]):
        for component, volume in recipe:
            if self._abort:
                return False

            try:
                self.scales.reset()
            except ScalesTimeoutException:
                print('error resetting scales')
                raise

            try:
                self.components[component].open()
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
        self._abort = True
        self.scales.abort_waiting_for_weight()
        return True

    @sm_transition(allowed_from=BartenderState.READY, when_done=BartenderState.IDLE)
    def serve(self):
        self.scales.reset()
        try:
            self.scales.wait_for_weight(GLASS_WEIGHT * -1, USER_TAKE_GLASS_TIMEOUT * 1000)
        except ScalesTimeoutException:
            print('giving up waiting for the user to retrieve the glass')
