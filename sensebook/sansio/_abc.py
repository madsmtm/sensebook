import abc
from typing import Dict, Any, Optional

from ._utils import build_url

__all__ = ("ABCRequest",)


class ABCRequest(metaclass=abc.ABCMeta):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def method(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def host(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def target(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def params(self) -> Dict[str, Any]:
        raise NotImplementedError

    @property
    def read_timeout(self) -> Optional[float]:
        return None

    @property
    def connect_timeout(self) -> Optional[float]:
        return None

    @property
    def url(self) -> str:
        return build_url(host=self.host, target=self.target, params=self.params)
