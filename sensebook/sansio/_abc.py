import abc
from typing import Dict, Any, Optional

from ._utils import build_url

__all__ = ("ABCRequest", "State")


@attr.s(slots=True, kw_only=True)
class State(metaclass=abc.ABCMeta):
    """Core state storing, and methods for logging in/out of Facebook."""

    revision = attr.ib(None, type=str)
    fb_dtsg = attr.ib(None, type=str)

    @property
    def params(self):
        return {
            "__rev": self.client_revision,
            "__user": self.cookies.get("c_user"),
            "__a": "1",
            "fb_dtsg": self.fb_dtsg,
        }

    @property
    @abc.abstractmethod
    def cookies(self) -> Dict[str, str]:
        raise NotImplementedError


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
