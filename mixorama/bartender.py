from enum import IntEnum, unique
from typing import List, Dict, Tuple
import logging
from mixorama.io import Valve
from mixorama.recipes import Component
from mixorama.scales import Scales, ScalesTimeoutException, WaitingForWeightAbortedException
from mixorama.statemachine import sm_transition, StateMachineCallbacks, CoreStates

GLASS_WEIGHT = 150  # grams
USER_TAKE_GLASS_TIMEOUT = 60  # sec


logger = logging.getLogger(__name__)


@unique
class BartenderState(IntEnum):
    IDLE = 1
    MAKING = 2
    POURING = 4
    POURING_PROGRESS = 8
    READY = 16


class CocktailAbortedException(Exception):
    pass


class Bartender(StateMachineCallbacks):
    _sm_state = BartenderState.IDLE
    _abort = None

    def __init__(self, components: Dict[Component, Valve], compressor: Valve, scales: Scales):
        self.components = components
        self.scales = scales
        self.compressor = compressor

    @sm_transition(allowed_from=BartenderState.IDLE, when_done=BartenderState.READY,
                   while_working=BartenderState.MAKING)
    def make_drink(self, recipe: List[Tuple[Component, int]]):
        for component, volume in recipe:
            if component not in self.components:
                raise ValueError('We do not currently have {}'.format(component.name))

        for component, volume in recipe:
            if self._abort:
                return False
            self._pour(component=component, volume=volume)
        return True

    @sm_transition(allowed_from=BartenderState.MAKING, while_working=BartenderState.POURING,
                   when_done=BartenderState.MAKING)
    def _pour(self, component, volume):
        try:
            self.scales.reset()
        except ScalesTimeoutException:
            logger.info('Error resetting scales')
            raise

        self.compressor.open()
        try:
            self.components[component].open()

            self.scales.wait_for_weight(
                volume * component.density,
                on_progress=lambda done, volume:
                    self._sm_state == BartenderState.POURING and
                    self._pour_progress(
                        component=component,
                        done=done,
                        volume=volume
                    )
            )

        except ScalesTimeoutException:
            logger.info('Target weight is not reached within timeout.'
                        'Is something wrong with the valve?')
            raise
        except WaitingForWeightAbortedException as e:
            logger.info('Cocktail making aborted')
            raise CocktailAbortedException from e
        finally:
            self.components[component].close()
            self.compressor.close()

    @sm_transition(allowed_from=BartenderState.POURING, while_working=BartenderState.POURING_PROGRESS,
                   when_done=BartenderState.POURING)
    def _pour_progress(self, component, done, volume):
        pass

    @sm_transition(allowed_from=BartenderState.READY, when_done=BartenderState.IDLE)
    def serve(self):
        return self._wait_for_glass_lift()

    @sm_transition(allowed_from=CoreStates.EXCEPTION, when_done=BartenderState.IDLE)
    def discard(self):
        self._wait_for_glass_lift()
        self._abort = False

    def abort(self):
        self._abort = True
        self.scales.abort_waiting_for_weight()
        return True

    def _wait_for_glass_lift(self):
        logger.info('waiting for the user to retrieve the glass')
        self.scales.reset()
        try:
            self.scales.wait_for_weight(GLASS_WEIGHT * -1, USER_TAKE_GLASS_TIMEOUT * 1000)
            logger.info('weight lifted')
            return True
        except ScalesTimeoutException:
            logger.info('giving up waiting for the user to retrieve the glass')
