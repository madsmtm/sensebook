import attr
import requests

from .. import sansio
from . import State

__all__ = ("login", "logout", "is_logged_in")

LOGIN_URL = "https://m.facebook.com/login"
HOME_URL = "https://facebook.com/home"


def login(email: str, password: str) -> State:
    state = State()

    r = state.get(LOGIN_URL)
    method, url, data = sansio._login.get_form_data(r.text, email, password)
    r = state.request(method, url, data=data)

    sansio._login.check(state, r.url)

    r = state.get(HOME_URL)
    state.fb_dtsg = sansio._login.get_fb_dtsg(r.text)
    state.revision = sansio._login.get_revision(r.text)

    return state


def logout(state: State) -> None:
    """Properly log out and invalidate the session"""

    r = state.post("/bluebar/modern_settings_menu/", data={"pmid": "4"})
    state.get("/logout.php", params=sansio._login.get_logout_form_params(r.text))


def is_logged_in(state: State) -> bool:
    """Check the login status

    Return:
        Whether the session is still logged in
    """
    # Call the login url, and see if we're redirected to the home page
    r = state.get(LOGIN_URL, allow_redirects=False)

    return "Location" in r.headers and "home" in r.headers["Location"]
