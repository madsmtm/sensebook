import attr
import requests
import time

from typing import Any, Iterable, Optional

from .. import sansio
from . import State


@attr.s(slots=True, kw_only=True)
class Listener:
    _state = attr.ib(type=State)
    _listener = attr.ib(factory=sansio.Listener, type=sansio.Listener)

    def _sleep(self) -> None:
        delay = self._listener.get_delay()

        if delay is not None:
            print("Sleeping for {} seconds.".format(delay))
            time.sleep(delay)

    def _step(self) -> Iterable[Any]:
        request = self._listener.next_request()

        try:
            r = self._state.request(
                request.method,
                request.url,
                timeout=(request.connect_timeout, request.read_timeout),
            )
        except requests.exceptions.ConnectionError:
            self._listener.handle_connection_error()
        except requests.exceptions.ConnectTimeout:
            self._listener.handle_connect_timeout()
        except requests.exceptions.ReadTimeout:
            self._listener.handle_read_timeout()
        else:
            yield from self._listener.handle(r.status_code, r.content)

    def pull(self) -> Iterable[Any]:
        while True:
            self._sleep()
            yield from self._step()
