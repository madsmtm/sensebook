import attr
import logging
import requests
import time

from typing import Any, Iterable, Optional

from .. import sansio

__all__ = ("Listener",)

log = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True)
class Listener:
    _session = attr.ib(type=requests.Session)
    _listener = attr.ib(factory=sansio.Listener, type=sansio.Listener)

    def _sleep(self) -> None:
        delay = self._listener.get_delay()

        if delay is not None:
            print("Sleeping for {} seconds.".format(delay))
            time.sleep(delay)

    def _step(self) -> Iterable[Any]:
        request = self._listener.next_request()

        try:
            r = self._session.request(
                request.method,
                request.url,
                timeout=(request.connect_timeout, request.read_timeout),
            )
        except requests.ConnectionError:
            self._listener.handle_connection_error()
        except requests.ConnectTimeout:
            self._listener.handle_connect_timeout()
        except requests.ReadTimeout:
            self._listener.handle_read_timeout()
        else:
            yield from self._listener.handle(r.status_code, r.content)

    def pull(self) -> Iterable[Any]:
        while True:
            self._sleep()
            yield from self._step()
