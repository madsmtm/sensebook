import attr
import requests

from .. import sansio

__all__ = ("Session",)


@attr.s(slots=True, kw_only=True)
class State(sansio.State):
    _session = attr.ib(factory=requests.Session, type=requests.Session)

    @property
    def cookies(self):
        return self._session.cookies

    def request(self, method, url, **kwargs):
        self._session.params = self.params
        return self._session.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self._session.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._session.request("POST", url, **kwargs)
