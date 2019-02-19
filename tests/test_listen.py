import sensebook
from pytest import fixture, mark, param


@fixture
def listener():
    return sensebook.PullHandler()


def test_parse_body():
    assert sensebook._pull_handler.parse_body(b'for(;;);{"a":2}') == {"a": 2}


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
    listener = sensebook.PullHandler(seq=None)
    assert listener._parse_seq(data) == seq


@mark.raises(exception=sensebook.Backoff)
def test_handle_status_503(listener):
    listener._handle_status(503, b"")


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_status_failed(listener):
    listener._handle_status(500, b"")


def test_parse_body():
    assert sensebook._pull_handler.parse_body(b'for(;;);{"a":2}') == {"a": 2}


@mark.raises(exception=sensebook.ProtocolError)
def test_parse_body_invalid_unicode():
    sensebook._pull_handler.parse_body(bytes([255, 255]))


@mark.raises(exception=sensebook.ProtocolError)
def test_parse_body_invalid_json():
    sensebook._pull_handler.parse_body(b"invalid JSON")


def test_handle_data(listener):
    lst = [1, 2, 3]
    assert list(listener._handle_data({"t": "msg", "ms": lst})) == lst


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_data_unknown_type(listener):
    listener._handle_data({"t": "unknown"})


# Type handlers


@mark.raises(exception=sensebook.Backoff)
def test_handle_type_backoff(listener):
    listener._handle_type_backoff({})


def test_handle_type_batched(listener, patcher):
    m = patcher(sensebook.PullHandler, "_handle_data", return_value=[])
    list(listener._handle_type_batched({"batches": ["1", "2", "3"]}))
    assert m.call_count == 3


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_type_continue(listener):
    listener._handle_type_continue({})


def test_handle_type_full_reload(listener):
    lst = [1, 2, 3]
    assert lst == list(listener._handle_type_fullReload({"ms": lst}))


def test_handle_type_heartbeat(listener):
    listener._handle_type_heartbeat({})


@mark.parametrize(
    "data, sticky_token, sticky_pool",
    [
        ({"lb_info": {"sticky": 1234}}, 1234, None),
        ({"lb_info": {"sticky": "1234", "pool": "abc"}}, "1234", "abc"),
        # param({"lb_info": {}}, None, None, marks=mark.xfail(raises=sensebook.ProtocolError)),
    ],
)
def test_handle_type_lb(data, sticky_token, sticky_pool):
    listener = sensebook.PullHandler(sticky_pool=None, sticky_token=None)
    listener._handle_type_lb(data)
    assert listener._sticky_pool == sticky_pool
    assert listener._sticky_token == sticky_token


def test_handle_type_msg(listener):
    lst = [1, 2, 3]
    assert lst == list(listener._handle_type_msg({"ms": lst}))


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_type_refresh(listener):
    listener._handle_type_refresh({})


@mark.raises(exception=sensebook.ProtocolError)
def test_handle_type_test_streaming(listener):
    listener._handle_type_test_streaming({})


# Public methods


def test_request():
    params = {
        "clientid": "deadbeef",
        "sticky_token": "1234",
        "sticky_pool": "xxxxxxxx_chatproxy-regional",
        "seq": 6,
    }
    listener = sensebook.PullHandler(mark_alive=False, **params)

    params["state"] = "offline"
    params["msgs_recv"] = 0

    request = listener.next_request()
    assert request.params == params


@mark.raises(exception=sensebook.Backoff)
def test_handle_connection_error(listener):
    listener.handle_connection_error()


@mark.raises(exception=sensebook.Backoff)
def test_handle_connect_timeout(listener):
    listener.handle_connect_timeout()


def test_handle_read_timeout(listener):
    listener.handle_read_timeout()


def test_handle(listener):
    assert [1, 2, 3] == list(
        listener.handle(200, b'for(;;);{"t": "msg", "ms": [1, 2, 3]}')
    )
