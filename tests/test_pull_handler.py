import sensebook
from pytest import fixture, mark, param


@fixture
def handler():
    return sensebook.PullHandler()


def test_backoff_from_tries():
    delay = sensebook.Backoff.from_tries(None, tries=0).delay
    assert delay == 0.0
    delay = sensebook.Backoff.from_tries(None, tries=1).delay
    assert 7.5 > delay > 5.0
    delay = sensebook.Backoff.from_tries(None, tries=2).delay
    assert 15.0 > delay > 10.0
    delay = sensebook.Backoff.from_tries(None, tries=3).delay
    assert 30.0 > delay > 20.0
    delay = sensebook.Backoff.from_tries(None, tries=10).delay
    assert 480.0 > delay > 320.0


@mark.parametrize(
    "data, seq", [({}, None), ({"s": 1}, 1), ({"seq": 1}, 1), ({"s": 1, "seq": 2}, 1)]
)
def test_parse_seq(data, seq):
    handler = sensebook.PullHandler(seq=None)
    assert handler._parse_seq(data) == seq


@mark.raises(exception=sensebook.Backoff)
def test_handle_status_503(handler):
    handler._handle_status(503, b"")


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_status_failed(handler):
    handler._handle_status(500, b"")


def test_parse_body():
    assert sensebook._pull_handler.parse_body(b'for(;;);{"a":2}') == {"a": 2}


@mark.raises(exception=sensebook.ProtocolError)
def test_parse_body_invalid_unicode():
    sensebook._pull_handler.parse_body(bytes([255, 255]))


@mark.raises(exception=sensebook.ProtocolError)
def test_parse_body_invalid_json():
    sensebook._pull_handler.parse_body(b"invalid JSON")


@mark.raises(exception=sensebook.ProtocolError, message="Unknown")
def test_handle_unknown_data_type(handler):
    handler.handle_data({"t": "unknown"})


@mark.raises(exception=sensebook.Backoff)
def test_handle_type_backoff(handler):
    handler.handle_data({"t": "backoff"})


def test_handle_type_batched(handler, mocker):
    m = mocker.spy(sensebook.PullHandler, "handle_data")
    data = {"t": "batched", "batches": [{"t": "msg", "ms": []}, {"t": "msg", "ms": []}]}
    list(handler.handle_data(data))
    assert m.call_count == 3


@mark.raises(exception=sensebook.ProtocolError, message="Unused")
def test_handle_type_continue(handler):
    handler.handle_data({"t": "continue"})


def test_handle_type_full_reload(handler):
    data = [1, 2, 3]
    assert data == list(handler.handle_data({"t": "fullReload", "ms": data}))


def test_handle_type_heartbeat(handler):
    handler.handle_data({"t": "heartbeat"})


@mark.parametrize(
    "data, sticky_token, sticky_pool",
    [
        ({"t": "lb", "lb_info": {"sticky": 1234}}, 1234, None),
        ({"t": "lb", "lb_info": {"sticky": "1234", "pool": "abc"}}, "1234", "abc"),
        # param({"lb_info": {}}, None, None, marks=mark.xfail(raises=sensebook.ProtocolError)),
    ],
)
def test_handle_type_lb(data, sticky_token, sticky_pool):
    handler = sensebook.PullHandler(sticky_pool=None, sticky_token=None)
    handler.handle_data(data)
    assert handler._sticky_pool == sticky_pool
    assert handler._sticky_token == sticky_token


def test_handle_type_msg(handler):
    lst = [1, 2, 3]
    assert lst == list(handler.handle_data({"t": "msg", "ms": lst}))


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_type_refresh(handler):
    handler.handle_data({"t": "refresh", "reason": 110})


@mark.raises(exception=sensebook.ProtocolError, message="Unused")
def test_handle_type_test_streaming(handler):
    handler.handle_data({"t": "test_streaming"})


def test_request():
    params = {
        "clientid": "deadbeef",
        "sticky_token": "1234",
        "sticky_pool": "xxxxxxxx_chatproxy-regional",
        "seq": 6,
    }
    handler = sensebook.PullHandler(mark_alive=False, **params)

    params["state"] = "offline"
    params["msgs_recv"] = 0

    request = handler.next_request()
    assert request.params == params


@mark.raises(exception=sensebook.Backoff)
def test_handle_connection_error(handler):
    handler.handle_connection_error()


@mark.raises(exception=sensebook.Backoff)
def test_handle_connect_timeout(handler):
    handler.handle_connect_timeout()


def test_handle_read_timeout(handler):
    handler.handle_read_timeout()


def test_handle(handler):
    assert [1, 2, 3] == list(
        handler.handle(200, b'for(;;);{"t": "msg", "ms": [1, 2, 3]}')
    )
