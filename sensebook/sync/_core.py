import attr
import requests

from typing import Dict, TypeVar, Type

from .. import sansio
from ..sansio import _login


T = TypeVar("T", bound="State")


@attr.s(slots=True, kw_only=True)
class State(sansio.State):
    _session = attr.ib(type=requests.Session)

    @_session.default
    @staticmethod
    def _default_session():
        session = requests.Session()
        session.headers["User-Agent"] = sansio.default_user_agent()
        return session

    @property
    def cookies(self):
        return self._session.cookies

    def request(self, method, url, **kwargs):
        if url.startswith("/"):
            url = "https://facebook.com" + url
        return self._session.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self._session.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._session.request("POST", url, **kwargs)

    @classmethod
    def login(cls: Type[T], email: str, password: str) -> T:
        session = cls._default_session()

        r = session.get(_login.LOGIN_URL)
        method, url, data = _login.get_form_data(r.text, email, password)
        r = session.request(method, url, data=data)

        _login.check(session, r.url)

        r = session.get(_login.HOME_URL)

        return cls(
            fb_dtsg=_login.get_fb_dtsg(r.text),
            revision=_login.get_revision(r.text),
            session=session,
        )

    def logout(self) -> None:
        """Properly log out and invalidate the session"""

        r = self.post("/bluebar/modern_settings_menu/", data={"pmid": "4"})
        params = _login.get_logout_form_params(r.text)
        self.get("/logout.php", params=params)

    def is_logged_in(self) -> bool:
        """Check the login status

        Return:
            Whether the session is still logged in
        """
        # Call the login url, and see if we're redirected to the home page
        r = self.get(_login.LOGIN_URL, allow_redirects=False)
        return "Location" in r.headers and "home" in r.headers["Location"]
