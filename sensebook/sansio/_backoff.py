import attr
import random

from typing import Optional, ClassVar, Callable

__all__ = ("Backoff",)


@attr.s(slots=True, kw_only=True)
class Backoff:
    func = attr.ib(type=Callable[[float], float])
    jitter = attr.ib(type=Callable[[float], float])

    _tries = attr.ib(0, type=int)
    _delay_override = attr.ib(None, type=float)

    @classmethod
    def expo(cls, *, max_time, factor, **kwargs) -> "Backoff":
        def func(tries: float) -> float:
            return min(factor * 2 ** max(0, tries - 1), max_time)

        return cls(func=func, **kwargs)

    @property
    def tries(self):
        return self._tries

    def do(self) -> None:
        self._tries += 1

    def reset(self) -> None:
        self._tries = 0

    def override(self, value: float) -> None:
        self._delay_override = value

    def reset_override(self) -> None:
        self._delay_override = None

    def get_delay(self) -> Optional[float]:
        if self._delay_override:
            return self._delay_override
        if self.tries > 0:
            return self._compute_delay(self.tries)
        return None

    def get_randomized_delay(self) -> Optional[float]:
        delay = self.get_delay()
        if delay is None:
            return None
        return self.jitter(delay)
