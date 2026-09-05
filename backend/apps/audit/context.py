from contextlib import contextmanager
from threading import local


_state = local()


def get_current_actor():
    return getattr(_state, "actor", None)


def audit_is_suppressed():
    return getattr(_state, "suppressed", False)


@contextmanager
def audit_actor(actor):
    previous = get_current_actor()
    _state.actor = actor if getattr(actor, "is_authenticated", True) else None
    try:
        yield
    finally:
        _state.actor = previous


@contextmanager
def suppress_audit():
    previous = audit_is_suppressed()
    _state.suppressed = True
    try:
        yield
    finally:
        _state.suppressed = previous
