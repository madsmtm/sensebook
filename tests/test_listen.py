from sensebook import sansio
from pytest import fixture, mark, param


@fixture
def listener():
    return sansio.Listener()


def test_init():
    sansio.Listener()
    sansio.Listener(mark_alive=True)


@mark.parametrize(
    "data, seq", [({}, None), ({"s": 1}, 1), ({"seq": 1}, 1), ({"s": 1, "seq": 2}, 1)]
)
def test_parse_seq(data, seq):
    listener = sansio.Listener(seq=None)
    assert listener._parse_seq(data) == seq


def test_safe_status_code(listener):
    assert not listener._safe_status_code(199)
    assert listener._safe_status_code(200)
    assert listener._safe_status_code(299)
    assert not listener._safe_status_code(300)


def test_handle_status_503(listener):
    listener._handle_status(503, b"")


@mark.raises(exception=sansio.ProtocolError)
def test_handle_status_failed(listener):
    listener._handle_status(500, b"")


def test_parse_body(listener):
    assert listener._parse_body(b'for(;;);{"a":2}') == {"a": 2}


@mark.raises(exception=sansio.ProtocolError)
def test_parse_body_invalid_unicode(listener):
    listener._parse_body(bytes([255, 255]))


@mark.raises(exception=sansio.ProtocolError)
def test_parse_body_invalid_json(listener):
    listener._parse_body(b"invalid JSON")


def test_handle_data(listener):
    lst = [1, 2, 3]
    assert list(listener._handle_data({"t": "msg", "ms": lst})) == lst


@mark.raises(exception=sansio.ProtocolError)
def test_handle_data_unknown_type(listener):
    listener._handle_data({"t": "unknown"})


# Type handlers


def test_handle_type_backoff(listener):
    listener._handle_type_backoff({})
    assert listener._backoff._tries == 1


def test_handle_type_batched(listener, patcher):
    m = patcher(sansio.Listener, "_handle_data", return_value=[])
    list(listener._handle_type_batched({"batches": ["1", "2", "3"]}))
    assert m.call_count == 3


@mark.raises(exception=sansio.ProtocolError)
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
        # param({"lb_info": {}}, None, None, marks=mark.xfail(raises=sansio.ProtocolError)),
    ],
)
def test_handle_type_lb(data, sticky_token, sticky_pool):
    listener = sansio.Listener(sticky_pool=None, sticky_token=None)
    listener._handle_type_lb(data)
    assert listener._sticky_pool == sticky_pool
    assert listener._sticky_token == sticky_token


def test_handle_type_msg(listener):
    lst = [1, 2, 3]
    assert lst == list(listener._handle_type_msg({"ms": lst}))


@mark.raises(exception=sansio.ProtocolError)
def test_handle_type_refresh(listener):
    listener._handle_type_refresh({})


@mark.raises(exception=sansio.ProtocolError)
def test_handle_type_test_streaming(listener):
    listener._handle_type_test_streaming({})


# Public methods


def test_get_delay(listener):
    assert listener.get_delay() is None


def test_request():
    params = {
        "clientid": "deadbeef",
        "sticky_token": "1234",
        "sticky_pool": "xxxxxxxx_chatproxy-regional",
        "seq": 6,
    }
    listener = sansio.Listener(mark_alive=False, **params)

    params["state"] = "offline"
    params["msgs_recv"] = 0

    request = listener.next_request()
    assert request.params == params


def test_handle_errors(listener):
    listener.handle_connection_error()
    listener.handle_connect_timeout()
    listener.handle_read_timeout()


def test_handle(listener):
    assert [1, 2, 3] == list(
        listener.handle(200, b'for(;;);{"t": "msg", "ms": [1, 2, 3]}')
    )
