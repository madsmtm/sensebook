import datetime
import sensebook
from pytest import fixture, mark, param


def test_default_user_agent():
    assert sensebook.default_user_agent().startswith("sensebook/")


def test_build_url():
    assert "https://example.com/path?a=1" == sensebook.build_url(
        host="example.com", target="/path", params={"a": 1}
    )


def test_strip_json_cruft():
    assert sensebook.strip_json_cruft('for(;;);{"a":2}') == '{"a":2}'


@mark.raises(exception=ValueError, message="No JSON object found")
def test_strip_json_cruft_invalid():
    sensebook.strip_json_cruft("not really json")


def test_time_from_millis():
    dt = datetime.datetime(2018, 11, 16, 1, 51, 4, 162000)
    assert sensebook.time_from_millis(1542333064162) == dt


def test_random_hex():
    assert sensebook.random_hex(10)


def test_safe_status_code():
    assert not sensebook.safe_status_code(199)
    assert sensebook.safe_status_code(200)
    assert sensebook.safe_status_code(299)
    assert not sensebook.safe_status_code(300)
