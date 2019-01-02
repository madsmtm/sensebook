import attr
import logging
import requests
import time

from typing import Any, Iterable

from . import sansio

__all__ = ("Listener",)

log = logging.getLogger(__name__)


@attr.s(slots=True, kwonly=True)
class Listener:
    _session = attr.ib(type=requests.Session)
    pull_data = attr.ib(factory=sansio.PullData, type=sansio.PullData)
    mark_alive = attr.ib(False, type=bool)

    @property
    def backoff(self):
        return self.pull_data.backoff

    def pull(self) -> Optional[]:
        pull_request = sansio.PullRequest(
            pull_data=self.pull_data, mark_alive=self.mark_alive
        )
        try:
            r = self._session.request(
                self.pull_data.method,
                "https://{}{}".format(self.pull_data.host, self.pull_data.target),
                params=self.pull_data.get_params(),
                timeout=(self.pull_data.connect_timeout, self.pull_data.read_timeout),
                **kwargs,
            )
        except (requests.ConnectionError, requests.Timeout):
            # If we lost our connection, keep trying every minute
            log.exception("Could not pull")
            self.backoff.override(60)
            return None

        if r.status_code == 503:
            # In Facebook's JS code, this delay is set by their servers on every call to
            # `/ajax/presence/reconnect.php`, as `proxy_down_delay_millis`, but we'll
            # just set a sensible default
            self.backoff.override(60)
            log.error("Server is unavailable")
            return None

        if not (200 <= r.status_code < 300):
            log.error("Response status: %s", r.status_code)
            self.backoff.override(30)
            return None

        self.backoff.reset_override()

        if not r.content:
            return None

        return pull_request.parse(r.content)

    def listen(self) -> Iterable[Any]:
        while True:
            delay = listener.get_randomized_delay()
            if delay is not None:
                time.sleep(delay)
            yield from self.pull() or ()


# class StreamingListener(Listener):
#     """Handles listening for events, using a streaming pull request"""

#     def _get_pull_params(self):
#         rtn = super()._get_pull_params()
#         rtn["mode"] = "stream"
#         rtn["format"] = "json"
#         return rtn

#     async def pull(self):
#         try:
#             r = await self._pull(stream=True)
#             return list(r.iter_json())
#         except (requests.ConnectionError, requests.Timeout):
#             # If we lost our connection, keep trying every minute
#             await trio.sleep(60)
#             return None
