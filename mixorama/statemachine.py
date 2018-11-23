from collections import defaultdict
from enum import Enum
from typing import Union


class CoreStates(Enum):
    ALL = 0
    UNDEFINED = 1
    EXCEPTION = 2


class InvalidStateMachineTransition(AttributeError):
    def __init__(self, operation, current_state, allowed_states):
        super().__init__('Operation {} is not allowed from State {}, only from {}'.format(
            operation, current_state, allowed_states))


def sm_transition(allowed_from: Union[list, Enum],
                  when_done: Enum,
                  while_working: Enum = None,
                  on_exception: Enum = None):

    allowed_from = [allowed_from] if not type(allowed_from) in (tuple, list) else allowed_from
    on_exception = on_exception or CoreStates.EXCEPTION

    def decorate(f):
        def check_transition_and_run(self, *args, **kwargs):
            operation_name = f.__name__
            current_state = getattr(self, '_sm_state', CoreStates.UNDEFINED)

            if current_state not in allowed_from and current_state is not CoreStates.ALL:
                raise InvalidStateMachineTransition(operation_name, repr(current_state), allowed_from)

            if while_working is not None:
                _notify_callbacks(self, while_working, self._sm_state, args, kwargs)
                self._sm_state = while_working

            try:
                result = f(self, *args, **kwargs)
            except Exception as e:
                kwargs.update({'_e': e})
                _notify_callbacks(self, on_exception, self._sm_state, args, kwargs)
                self._sm_state = on_exception
                raise

            _notify_callbacks(self, when_done, self._sm_state, args, kwargs)
            self._sm_state = when_done

            return result
        return check_transition_and_run
    return decorate


class StateMachineCallbacks:
    _sm_callbacks = defaultdict(lambda: dict())

    def on_sm_transition(self, callback, tostate=CoreStates.ALL):
        self._sm_callbacks[tostate][callback] = callback

    def unsubscribe_sm_transition(self, callback, state=None):
        del self._sm_callbacks[state][callback]

    def on_sm_transitions(self, map=None, enum: Enum=None, **kwargs):
        map = map or {}
        map.update({enum[k]: cb for k, cb in kwargs.items()})

        for state, cb in map.items():
            self.on_sm_transition(cb, state)


def _notify_callbacks(self, tostate, fromstate, args, kwargs):
    if isinstance(self, StateMachineCallbacks):
        cb_kwargs = dict(target=self, tostate=tostate, fromstate=fromstate, args=args)
        cb_kwargs.update(kwargs)

        _notify_callback(self._sm_callbacks[CoreStates.ALL], cb_kwargs)
        _notify_callback(self._sm_callbacks[tostate], cb_kwargs)


def function_args(cb):
    args = cb.__code__.co_varnames[:cb.__code__.co_argcount]
    return [k for k in args if k != 'self']


def _notify_callback(cbdict, all_kwargs):
    for cb in cbdict.values():
        cb_kwargs = {k: all_kwargs[k] for k in function_args(cb) if k in all_kwargs}
        cb(**cb_kwargs)
