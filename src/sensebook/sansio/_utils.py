import datetime
import json
import urllib.parse
from typing import Dict, Any

__all__ = ("build_target", "strip_json_cruft", "load_json", "time_from_millis")


def build_url(
    host: str, target: str, query: Dict[str, Any], secure: bool = True
) -> str:
    scheme = "https" if secure else "http"
    return urllib.parse.urlunsplit(
        (scheme, host, target, urllib.parse.urlencode(query), "")
    )


def strip_json_cruft(text: str) -> str:
    """Removes `for(;;);` (and other cruft) that preceeds JSON responses"""
    try:
        return text[text.index("{") :]
    except ValueError:
        raise ValueError("No JSON object found: {!r}".format(text))


def load_json(text: str) -> Any:
    return json.loads(text)


def time_from_millis(timestamp_in_milliseconds: int) -> datetime:
    return datetime.datetime.fromtimestamp(int(timestamp) / 1000)
