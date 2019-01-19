import attr
import re
import requests

from .. import sansio

__all__ = ("Login",)


@attr.s(slots=True, kw_only=True)
class Login:
    """Core methods for logging in to and out of Facebook"""

    _session = attr.ib(type=requests.Session)

    BASE_URL = "https://facebook.com"
    MOBILE_URL = "https://m.facebook.com"
    FIND_LOGOUT_VALUE = re.compile(r'name=\\"h\\" value=\\"(.*?)\\"')

    @classmethod
    def login(cls, email: str, password: str) -> "Login":
        """Initialize and login, storing the cookies in the session

        Args:
            email: Facebook `email`, `id` or `phone number`
            password: Facebook account password
        """
        s = requests.Session()

        r = s.get(cls.MOBILE_URL)
        url, data = sansio._login.get_form_data(r.text)
        r = s.post(url, data=data)

        sansio._login.check(s.cookies, r.url)

        resp = s.get(cls.BASE_URL)
        s.params = sansio._login.get_params(s.cookies, resp.text)

        return cls(session=s)

    def logout(self) -> None:
        """Properly log out and invalidate the session"""

        r = self._session.post("/bluebar/modern_settings_menu/", data={"pmid": "4"})
        params = sansio._login.get_logout_form_params(r.text)
        self._session.get("/logout.php", params=params)

    def is_logged_in(self) -> bool:
        """Check the login status

        Return:
            Whether the session is still logged in
        """
        # Call the login url, and see if we're redirected to the home page
        r = self._session.get(self.LOGIN_URL, allow_redirects=False)

        return "Location" in r.headers and "home" in r.headers["Location"]
