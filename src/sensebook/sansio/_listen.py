import attr
import random
import logging

from typing import ClassVar, Iterable, Any, List

from ._utils import strip_text_for_json, load_json
from ._abc import ABCGetRequest


log = logging.getLogger(__name__)

__all__ = ("Backoff", "PullData", "PullRequest")


@attr.s(slots=True, kwonly=True)
class Backoff:
    _delay_override = attr.ib(None, type=float)
    _times = attr.ib(0, type=int)

    def do(self) -> None:
        self._times += 1

    def reset(self) -> None:
        self._times = 0

    def override(self, value: float) -> None:
        self._delay_override = value

    def reset_override(self) -> None:
        self._delay_override = None

    def get_delay(self) -> float:
        if self._delay_override:
            return self._delay_override
        if self._times > 0:
            delay = min(5 * (2 ** max(0, self._times - 1)), 320)
            return delay
        return None

    def get_randomized_delay(self) -> Optional[float]:
        delay = self.get_delay()
        if delay is None:
            return None
        return delay * random.uniform(1, 1.5)


@attr.s(slots=True, kwonly=True)
class PullData:
    backoff = attr.ib(factory=Backoff, type=Backoff)
    clientid = attr.ib(type=str)
    sticky_token = attr.ib(None, type=str)
    sticky_pool = attr.ib(None, type=str)
    msgs_recv = attr.ib(0, type=int)
    seq = attr.ib(0, type=int)
    _prev_seq = attr.ib(0, type=int)

    @clientid.default
    def default_client_id(self):
        return "{:x}".format(random.randint(0, 2 ** 31))

    def parse_seq(self, data: Any) -> int:
        """Extract a new `seq` from pull data, or return the old."""
        if "s" in data:
            return int(data["s"])
        if "seq" in data:
            return int(data["seq"])
        return self.seq

    def verify_seq(self, msgs: List[Any]) -> None:
        """Verifies that the messages arrived in the proper sequence."""
        if self.seq - self._prev_seq < len(msgs):
            msg = "Sequence regression. Some items may have been duplicated! %s, %s, %s"
            log.error(msg, self._prev_seq, self.seq, msgs)
            # We could strip the duplicated msgs with:
            # msgs = msgs[len(msgs) - (self._seq - self._prev_seq): ]
            # But I'm not sure what causes a sequence regression, and there might be
            # other factors involved, so it's safer to just allow duplicates for now

    def handle_msg(self, msgs: List[Any]) -> Iterable[Any]:
        """Handle the message data in the `ms` key."""
        self.verify_seq(msgs)
        for msg in msgs:
            self.msgs_recv += 1
            yield msg

    def handle_type_backoff(self, data):
        log.warning("Server told us to back off")
        self.backoff.do()

    def handle_type_batched(self, data):
        for item in data["batches"]:
            yield from self.handle_protocol_data(item)

    def handle_type_continue(self, data):
        self.backoff.reset()
        log.info("Unused protocol message 'continue', %s", data)

    def handle_type_fullReload(self, data):
        """Not yet sure what consequence this has.

        But I know that if this is sent, then some messages/events may not have been
        sent to us, so we should query for them with a graphqlbatch-something.
        """
        self.backoff.reset()
        if "ms" in data:
            yield from self.handle_msg(data["ms"])

    def handle_type_heartbeat(self, data):
        # Request refresh, no need to do anything

    def handle_type_lb(self, data):
        lb_info = data["lb_info"]
        self.sticky_token = lb_info["sticky"]
        if "pool" in lb_info:
            self.sticky_pool = lb_info["pool"]

    def handle_type_msg(self, data):
        self.backoff.reset()
        yield from self.handle_msg(data["ms"])

    def handle_type_refresh(self, data):
        # {'t': 'refresh', 'reason': 110, 'seq': 0}
        self.backoff.override(5)  # Temporary, I was hitting infinite loops
        log.info("Unused protocol message 'refresh', %s", data)

    handle_type_refreshDelay = handle_type_refresh

    def handle_type_test_streaming(self, data):
        log.info("Unused protocol message 'test_streaming', %s", data)

    def handle(self, data: Dict[str, Any]) -> Iterable[Any]:
        """Handle pull protocol data, and yield data frames ready for further parsing"""
        self._prev_seq = self.seq
        self.seq = self.parse_seq(data)

        # Don't worry if you've never seen a lot of these types, this is implemented
        # based on reading the JS source for Facebook's `ChannelManager`
        type_ = data.get("t")
        method = getattr(self, "handle_type_{}".format(type_), None)
        if method:
            yield from method(data) or ()
        else:
            log.error("Unknown protocol message: %s, %s", type_, data)


@attr.s(slots=True, kwonly=True)
class PullRequest(ABCGetRequest):
    """Handles polling for events."""

    mark_alive = attr.ib(type=bool)
    pull_data = attr.ib(type=PullData)

    host = "0-edge-chat.facebook.com"
    target = "/pull"
    #: The server holds the request open for 50 seconds
    read_timeout = 60
    connect_timeout = 10

    def get_params(self):
        return {
            "clientid": self.pull_data.clientid,
            "sticky_token": self.pull_data.sticky_token,
            "sticky_pool": self.pull_data.sticky_pool,
            "msgs_recv": self.pull_data.msgs_recv,
            "seq": self.pull_data.seq,
            "state": "active" if self.mark_alive else "offline"
        }

    def parse(self, data: bytes) -> None:
        j = load_json(strip_text_for_json(data.decode("utf-8")))
        return self.pull_data.handle(j)

    def handle_error(self, code, *more) -> None:
        raise NotImplementedError
