import abc
from typing import ClassVar, Dict, Iterable
from ._utils import build_url

__all__ = ("ABCRequest", "ABCGetRequest")


class ABCRequest(metaclass=abc.ABCMeta):
    __slots__ = ()

    @abc.abstractmethod
    @property
    def method(self) -> ClassVar[str]:
        raise NotImplementedError

    @abc.abstractmethod
    @property
    def host(self) -> ClassVar[str]:
        raise NotImplementedError

    @abc.abstractmethod
    @property
    def target(self) -> ClassVar[str]:
        raise NotImplementedError

    @property
    def url(self) -> str:
        return build_url(host=self.host, target=self.target, params=self.get_params())

    @abc.abstractmethod
    def get_params(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def send_data(self) -> Iterable[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_headers(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def recv_data(self, data: bytes) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_result(self) -> Any:
        raise NotImplementedError


class ABCGetRequest(ABCRequest):
    __slots__ = ("_recieved_data",)
    method = "GET"

    def send_data(self):
        return ()

    def get_headers(self):
        return {}

    @abc.abstractmethod
    def parse(self, data: bytes) -> None:
        pass

    def recv_data(self, data: bytes) -> None:
        if not hasattr(self, "_recieved_data"):
            self._recieved_data = b""
        self._recieved_data += data

    def get_result(self) -> Any:
        return self.parse(self._recieved_data)
