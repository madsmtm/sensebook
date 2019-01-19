import attr
import bs4
import re

from typing import Dict, Tuple

from . import _utils, State

REVISION_RE = re.compile(r'"client_revision":(.*?),')
FB_DTSG_RE = re.compile(r'name="fb_dtsg" value="(.*?)"')
LOGOUT_H_RE = re.compile(r'name=\\"h\\" value=\\"(.*?)\\"')
LOGIN_URL = "https://m.facebook.com/login"
HOME_URL = "https://facebook.com/home"


class LoginError(Exception):
    pass


def get_revision(html: str) -> str:
    match = REVISION_RE.search(html)
    if not match:
        raise LoginError("Could not find `revision`!")
    return match.group(1)


def get_fb_dtsg(html: str) -> str:
    match = FB_DTSG_RE.search(html)
    if not match:
        raise LoginError("Could not find `fb_dtsg`!")
    return match.group(1)


def get_logout_h(html: str) -> str:
    match = LOGOUT_H_RE.search(html)
    if not match:
        raise LoginError("Could not find `logout_h`!")
    return match.group(1)


def get_form_data(
    html: str, email: str, password: str
) -> Tuple[str, str, Dict[str, str]]:
    try:
        method, url, data = _utils.parse_form(html)
    except ValueError as e:
        raise LoginError from e  # TODO: Better error message
    data["email"] = email
    data["pass"] = password
    if "sign_up" in data:
        del data["sign_up"]
    data["login"] = "Log In"
    return method, url, data


def check(state: State, url: str) -> None:
    if "c_user" not in state.cookies:
        raise LoginError("Could not login, failed on: {}".format(url))


def get_logout_form_params(html: str) -> Dict[str, str]:
    return {"ref": "mb", "h": get_logout_h(html)}
