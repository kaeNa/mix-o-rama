import os
from enum import IntEnum, unique
from time import sleep
from typing import List, Dict, Tuple
import logging
from mixorama.io import Valve
from mixorama.recipes import Component
from mixorama.util import MaxObserver
from mixorama.scales import Scales, ScalesTimeoutException, WaitingForWeightAbortedException, ScalesException
from mixorama.statemachine import sm_transition, StateMachineCallbacks

GLASS_WEIGHT = 150  # grams
USER_TAKE_GLASS_TIMEOUT = 10000 if 'MOCK_SCALES' not in os.environ else 0  # msec
MEASURING_INERTIA = 10  # grams, that the scales don't see when the valve closes
POURING_TIMEOUT_PER_ML = 200  # ms to push 1 ml

logger = logging.getLogger(__name__)


@unique
class BartenderState(IntEnum):
    IDLE = 1
    MAKING = 2
    POURING = 4
    POURING_PROGRESS = 8
    READY = 16
    ABORTED = 32


class CocktailAbortedException(Exception):
    pass


class OutOfComponent(CocktailAbortedException):
    pass


class Bartender(StateMachineCallbacks):
    _sm_state = BartenderState.IDLE
    _abort = False

    def __init__(self, components: Dict[Component, Valve], compressor: Valve, scales: Scales):
        self.components = components
        self.scales = scales
        self.compressor = compressor

    def can_make_drink(self, recipe: List[Tuple[Component, int]]):
        for component, volume in recipe:
            if component not in self.components or not component.can_use(volume):
                return False

        return True

    @sm_transition(allowed_from=BartenderState.IDLE, when_done=BartenderState.READY,
                   while_working=BartenderState.MAKING, on_exception=BartenderState.ABORTED)
    def make_drink(self, recipe: List[Tuple[Component, int]]):
        if not self.can_make_drink(recipe):
            raise OutOfComponent()

        for component, volume in recipe:
            self._pour(recipe=recipe, component=component, volume=volume)
        return True

    @sm_transition(allowed_from=BartenderState.MAKING, while_working=BartenderState.POURING,
                   when_done=BartenderState.MAKING, on_exception=BartenderState.ABORTED)
    def _pour(self, recipe, component, volume):
        try:
            self.scales.reset()
        except ScalesException:
            logger.exception('Error resetting scales')
            raise

        self.compressor.open()

        pouring_tracker = MaxObserver()
        try:
            self.components[component].open()

            target_weight = volume * component.density
            target_weight -= MEASURING_INERTIA  # the pouring system has inertia...

            if self._abort:
                raise CocktailAbortedException()

            self.scales.wait_for_weight(
                target_weight,
                timeout=volume * POURING_TIMEOUT_PER_ML,
                on_progress=lambda done, volume:
                    self._sm_state == BartenderState.POURING and
                    pouring_tracker.observe(done) and
                    self._pour_progress(
                        recipe=recipe,
                        component=component,
                        done=done,
                        volume=volume
                    )
            )

        except ScalesTimeoutException as e:
            logger.exception('Target weight is not reached within timeout. '
                             'Is something wrong with the valve?')
            raise CocktailAbortedException from e
        except WaitingForWeightAbortedException as e:
            logger.info('Cocktail making aborted')
            raise CocktailAbortedException from e
        finally:
            self.compressor.close()
            sleep(0.5)
            self.components[component].close()
            logger.info('Subtracted usage %f ml', pouring_tracker.value + MEASURING_INERTIA)
            component.use(pouring_tracker.value + MEASURING_INERTIA)

    @sm_transition(allowed_from=BartenderState.POURING, while_working=BartenderState.POURING_PROGRESS,
                   when_done=BartenderState.POURING)
    def _pour_progress(self, recipe, component, done, volume):
        pass

    @sm_transition(allowed_from=BartenderState.READY, when_done=BartenderState.IDLE,
                   on_exception=BartenderState.ABORTED)
    def serve(self):
        return self._wait_for_glass_lift()

    @sm_transition(allowed_from=BartenderState.ABORTED, when_done=BartenderState.IDLE)
    def discard(self):
        self._abort = False

    def abort(self):
        self._abort = True
        self.scales.abort_waiting_for_weight()
        return True

    def _wait_for_glass_lift(self):
        logger.info('waiting for the user to retrieve the glass')
        try:
            self.scales.reset()
            self.scales.wait_for_weight(GLASS_WEIGHT * -1, USER_TAKE_GLASS_TIMEOUT)
            logger.info('weight lifted')
            return True
        except ScalesTimeoutException as e:
            logger.info('giving up waiting for the user to retrieve the glass')
            raise CocktailAbortedException() from e
        except WaitingForWeightAbortedException as e:
            logger.info('user aborted the serve')
            raise CocktailAbortedException() from e
