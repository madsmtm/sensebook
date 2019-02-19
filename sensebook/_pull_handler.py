import attr
import random
import logging

from typing import Optional, Dict, Iterable, Any, List

from . import _utils, _abc


log = logging.getLogger(__name__)


class ProtocolError(Exception):
    """Raised if some assumption we made about Facebook's protocol is incorrect."""

    def __init__(self, msg, data=None):
        self.data = data
        if isinstance(data, dict):
            self.type = data.get("t")
        else:
            self.type = None
        super().__init__(msg)


class Backoff(Exception):
    """Raised to signal the client to wait for the time specified by `delay`."""

    max_time = 320
    factor = 5

    def __init__(self, message, *, delay):
        super().__init__(message)
        self.delay = delay

    @classmethod
    def from_tries(cls, message, *, tries):
        if tries > 0:
            # Exponential backoff
            delay = min(cls.factor * 2 ** max(0, tries - 1), cls.max_time)
            # Jitter
            delay = delay * random.uniform(1.0, 1.5)
        else:
            delay = 0
        return cls(message, delay=delay)


@attr.s(slots=True, kw_only=True, frozen=True)
class PullRequest(_abc.Request):
    """Handles polling for events."""

    params = attr.ib(type=Dict[str, Any])
    method = "GET"
    host = "0-edge-chat.facebook.com"
    target = "/pull"
    #: The server holds the request open for 50 seconds
    read_timeout = 60
    #: Slighty over a multiple of 3, see `TCP packet retransmission window`
    connect_timeout = 10  # TODO: Might be a bit too high


def parse_body(body: bytes) -> Dict[str, Any]:
    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ProtocolError("Invalid unicode data", body) from e
    try:
        return _utils.load_json(_utils.strip_json_cruft(decoded))
    except ValueError as e:
        raise ProtocolError("Invalid JSON data", decoded) from e


@attr.s(slots=True, kw_only=True)
class PullHandler:
    # _state = attr.ib(type=_abc.State)
    mark_alive = attr.ib(False, type=bool)
    _backoff_tries = attr.ib(0, type=int)
    _clientid = attr.ib(type=str)
    _sticky_token = attr.ib(None, type=str)
    _sticky_pool = attr.ib(None, type=str)
    _seq = attr.ib(0, type=int)

    @_clientid.default
    def _default_client_id(self):
        return _utils.random_hex(31)

    def _parse_seq(self, data: Any) -> int:
        # Extract a new `seq` from pull data, or return the old
        # The JS code handles "sequence regressions", and sends a `msgs_recv` parameter
        # back, but we won't bother, since their detection is broken (they don't reset
        # `msgs_recv` when `seq` resets)

        # `s` takes precedence over `seq`
        if "s" in data:
            return int(data["s"])
        if "seq" in data:
            return int(data["seq"])
        return self._seq

    def _handle_status(self, status_code, body):
        if status_code == 503:
            # In Facebook's JS code, this delay is set by their servers on every call to
            # `/ajax/presence/reconnect.php`, as `proxy_down_delay_millis`, but we'll
            # just set a sensible default
            raise Backoff("Server is unavailable", delay=60)
        else:
            raise ProtocolError(
                "Unknown server error response: {}".format(status_code), body
            )

    # Type handlers

    def _handle_type_backoff(self, data):
        self._backoff_tries += 1
        raise Backoff.from_tries(
            "Server told us to back off", tries=self._backoff_tries
        )

    def _handle_type_batched(self, data):
        for item in data["batches"]:
            yield from self.handle_data(item)

    def _handle_type_continue(self, data):
        self._backoff_tries = 0
        raise ProtocolError("Unused protocol message `continue`", data)

    def _handle_type_fullReload(self, data):
        # Not yet sure what consequence this has.
        # But I know that if this is sent, then some messages/events may not have been
        # sent to us, so we should query for them with a graphqlbatch-something.
        self._backoff_tries = 0
        if "ms" in data:
            return data["ms"]

    def _handle_type_heartbeat(self, data):
        # Request refresh, no need to do anything
        log.debug("Heartbeat")

    def _handle_type_lb(self, data):
        lb_info = data["lb_info"]
        self._sticky_token = lb_info["sticky"]
        if "pool" in lb_info:
            self._sticky_pool = lb_info["pool"]

    def _handle_type_msg(self, data):
        self._backoff_tries = 0
        return data["ms"]

    def _handle_type_refresh(self, data):
        # We won't perform the call, it's quite complicated, and perhaps unnecessary?
        raise ProtocolError(
            "The server told us to call `/ajax/presence/reconnect.php`."
            "This might mean our data representation is wrong!",
            data,
        )

    _handle_type_refreshDelay = _handle_type_refresh

    def _handle_type_test_streaming(self, data):
        raise ProtocolError("Unused protocol message `test_streaming`", data)

    # Public methods

    def handle_data(self, data: Dict[str, Any]) -> Iterable[Any]:
        # Don't worry if you've never seen a lot of these types, this is implemented
        # based on reading the JS source for Facebook's `ChannelManager`
        self._seq = self._parse_seq(data)

        type_ = data.get("t")
        method = getattr(self, "_handle_type_{}".format(type_), None)
        if method:
            return method(data) or ()
        else:
            raise ProtocolError("Unknown protocol message", data)

    def next_request(self) -> _abc.Request:
        return PullRequest(
            params={
                "clientid": self._clientid,
                "sticky_token": self._sticky_token,
                "sticky_pool": self._sticky_pool,
                "msgs_recv": 0,
                "seq": self._seq,
                "state": "active" if self.mark_alive else "offline",
            }
        )

    def handle_connection_error(self) -> None:
        self._backoff_tries += 1
        raise Backoff.from_tries("Could not pull", tries=self._backoff_tries)  # Unsure

    def handle_connect_timeout(self) -> None:
        # Keep trying every minute
        raise Backoff("Connection lost", delay=60)

    def handle_read_timeout(self) -> None:
        log.debug("Read timeout")
        # The server might not send data for a while, so we just try again

    def handle(self, status_code: int, body: bytes) -> Iterable[Any]:
        """Handle pull protocol body, and yield data frames ready for further parsing.

        Raise:
            `ProtocolError` if some assumption we made about Facebook's protocol was
            wrong.
        """
        if not _utils.safe_status_code(status_code):
            self._handle_status(status_code, body)
            return

        data = parse_body(body)

        yield from self.handle_data(data)


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
