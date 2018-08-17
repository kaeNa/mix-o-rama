from enum import Enum, auto
from typing import Union


class CoreStates(Enum):
    UNDEFINED = auto()
    EXCEPTION = auto()


class InvalidStateMachineTransition(AttributeError):
    def __init__(self, operation, current_state, allowed_states):
        super().__init__('Operation {} is not allowed from State {}, only from {}'.format(
            operation, current_state, allowed_states))


def sm_transition(allowed_from: Union[list, Enum], when_done: Enum, while_working: Enum = None, on_exception: Enum = None):
    allowed_from = [allowed_from] if not type(allowed_from) in (tuple, list) else allowed_from
    on_exception = on_exception or CoreStates.EXCEPTION

    def decorate(f):
        def check_transition_and_run(self, *args, **kwargs):
            operation_name = f.__name__
            current_state = getattr(self, '_sm_state', CoreStates.UNDEFINED)

            if current_state not in allowed_from:
                raise InvalidStateMachineTransition(current_state, operation_name, allowed_from)

            if while_working is not None:
                self._sm_state = while_working

            try:
                result = f(self, *args, **kwargs)
            except Exception:
                self._sm_state = on_exception
                raise

            self._sm_state = when_done

            return result
        return check_transition_and_run
    return decorate
