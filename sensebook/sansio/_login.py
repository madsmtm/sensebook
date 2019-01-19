import attr
import bs4
import re

from typing import Dict, Tuple

__all__ = (
    "Login",
    "LoginError",
    "get_params",
    "get_form_data",
    "get_fb_dtsg",
    "get_client_revision",
)

CLIENT_REVISION_RE = re.compile(r'"client_revision":(.*?),')
FB_DTSG_RE = re.compile(r'name="fb_dtsg" value="(.*?)"')
LOGOUT_H_RE = re.compile(r'name=\\"h\\" value=\\"(.*?)\\"')


class LoginError(Exception):
    pass


def get_client_revision(html: str) -> str:
    match = CLIENT_REVISION_RE.search(html)
    if not match:
        raise LoginError("Could not find `client_revision`!")
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


def get_params(cookies: Dict[str, str], html: str) -> Dict[str, str]:
    return {
        "__rev": get_client_revision(html),
        "__user": cookies["c_user"],
        "__a": "1",
        "fb_dtsg": get_fb_dtsg(html),
    }


def get_form_data(html: str, email: str, password: str) -> Tuple[str, Dict[str, str]]:
    soup = bs4.BeautifulSoup(html, "html.parser")
    form = soup.form
    if form is None or not form.has_attr("action"):
        raise LoginError("Could not find proper `form` element!")
    data = {
        elem["name"]: elem["value"]
        for elem in form.find_all("input")
        if elem.has_attr("value")
        and elem.has_attr("name")
        and elem["name"] != "sign_up"
    }
    data["email"] = email
    data["pass"] = password
    data["login"] = "Log In"
    return form["action"], data


def check(cookies: Dict[str, str], url: str) -> None:
    if "c_user" not in cookies:
        raise LoginError("Could not login, failed on: {}".format(url))


def get_logout_form_params(html: str) -> Dict[str, str]:
    return {"ref": "mb", "h": get_logout_h(html)}
