import abc
import attr
from typing import Dict, Any, Optional

from ._utils import build_url


@attr.s(slots=True, kw_only=True)
class State(metaclass=abc.ABCMeta):
    """Core state storing, and methods for logging in/out of Facebook."""

    revision = attr.ib(type=str)
    fb_dtsg = attr.ib(type=str)

    @property
    @abc.abstractmethod
    def cookies(self) -> Dict[str, str]:
        raise NotImplementedError


@attr.s(slots=True, kw_only=True, frozen=True)
class Request(metaclass=abc.ABCMeta):
    """Defines a generic way of specifying HTTP requests."""

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
