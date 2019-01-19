from ._core import State
from ._listen import Listener


def login(email: str, password: str) -> State:
    return State.login(email, password)
