import datetime
from sensebook import sansio
from pytest import fixture, mark, param


def test_build_url():
    assert "https://example.com/path?a=1" == sansio.build_url(
        host="example.com", target="/path", params={"a": 1}
    )


def test_strip_json_cruft():
    assert sansio.strip_json_cruft('for(;;);{"a":2}') == '{"a":2}'


@mark.raises(exception=ValueError, match=r"No JSON object found.*")
def test_strip_json_cruft_invalid():
    sansio.strip_json_cruft("not really json")


def test_time_from_millis():
    dt = datetime.datetime(2018, 11, 16, 2, 51, 4, 162_000)
    assert sansio.time_from_millis(1_542_333_064_162) == dt


def test_random_hex():
    assert sansio.random_hex(10)
