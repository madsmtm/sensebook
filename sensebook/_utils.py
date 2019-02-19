import bs4
import datetime
import json
import random
import urllib.parse

from typing import Dict, Any, Tuple


def default_user_agent() -> str:
    from . import __version__

    return "{}/{}".format(__name__.split(".")[0], __version__)


def parse_form(html: str) -> Tuple[str, str, Dict[str, str]]:
    soup = bs4.BeautifulSoup(html, "html.parser")
    form = soup.form
    if form is None or not form.has_attr("action"):
        raise ValueError("Could not find `form` element!")
    data = {
        elem["name"]: elem["value"]
        for elem in form.find_all("input")
        if elem.has_attr("value") and elem.has_attr("name")
    }
    return form.get("method", "GET"), form["action"], data


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


def time_from_millis(timestamp_in_milliseconds: int) -> datetime.datetime:
    return datetime.datetime.utcfromtimestamp(int(timestamp_in_milliseconds) / 1000)


def random_hex(n):
    return "{:x}".format(random.randint(0, 2 ** n))


def safe_status_code(status_code):
    return 200 <= status_code < 300


# @decorator.decorator
# def raises(func, exception_cls: BaseException = None, *args, **kwargs):
#     try:
#         return func(*args, **kwargs)
#     except Exception as e:
#         if exception_cls is not None and isinstance(e, exception_cls):
#             raise
#         raise InternalError from e
