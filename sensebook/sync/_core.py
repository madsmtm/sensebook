import attr
import requests

from typing import Dict

from .. import sansio, __version__

__all__ = ("State",)


@attr.s(slots=True, kw_only=True)
class State(sansio.State):
    _session = attr.ib(type=requests.Session)

    @_session.default
    def default_session(self):
        session = requests.Session()
        session.headers["User-Agent"] = sansio._utils.default_user_agent()
        return session

    @property
    def cookies(self):
        return self._session.cookies

    def request(self, method, url, **kwargs):
        self._session.params = self.params
        if url.startswith("/"):
            url = "https://facebook.com" + url
        return self._session.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self._session.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._session.request("POST", url, **kwargs)
