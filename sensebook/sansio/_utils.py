import datetime
import json
import random
import urllib.parse
from typing import Dict, Any

__all__ = (
    "build_url",
    "strip_json_cruft",
    "load_json",
    "time_from_millis",
    "random_hex",
)


def build_url(
    *, host: str, target: str, params: Dict[str, Any], secure: bool = True
) -> str:
    scheme = "https" if secure else "http"
    query = urllib.parse.urlencode(params)
    return urllib.parse.urlunsplit((scheme, host, target, query, ""))


def strip_json_cruft(text: str) -> str:
    """Removes `for(;;);` (and other cruft) that preceeds JSON responses"""
    try:
        return text[text.index("{") :]
    except ValueError:
        raise ValueError("No JSON object found: {!r}".format(text))


def load_json(text: str) -> Any:
    return json.loads(text)


def time_from_millis(timestamp_in_milliseconds: int) -> datetime:
    return datetime.datetime.utcfromtimestamp(int(timestamp_in_milliseconds) / 1000)


def random_hex(n):
    return "{:x}".format(random.randint(0, 2 ** n))


# @decorator.decorator
# def raises(func, exception_cls: BaseException = None, *args, **kwargs):
#     try:
#         return func(*args, **kwargs)
#     except Exception as e:
#         if exception_cls is not None and isinstance(e, exception_cls):
#             raise
#         raise InternalError from e
