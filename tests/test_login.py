import sensebook
from pytest import mark, param


@mark.parametrize(
    "html, rev",
    [
        param("invalid", None, marks=mark.raises(exception=sensebook.LoginError)),
        ('"client_revision":123,', "123"),
        ('<script>...{"server_revision":123,"client_revision":456,...</script>', "456"),
    ],
)
def test_get_revision(html, rev):
    assert sensebook._login.get_revision(html) == rev


@mark.parametrize(
    "html, rev",
    [
        param("invalid", None, marks=mark.raises(exception=sensebook.LoginError)),
        ('name="fb_dtsg" value="123"', "123"),
        ('<input type="hidden" name="fb_dtsg" value="12:34" />', "12:34"),
    ],
)
def test_get_fb_dtsg(html, rev):
    assert sensebook._login.get_fb_dtsg(html) == rev


def test_get_form_data():
    html = """
    <form method="post" action="https://m.facebook.com/login/..." class="be bf" id="login_form" novalidate="1">
        <input type="hidden" name="lsd" value="ABC" autocomplete="off" />
        <input type="hidden" name="jazoest" value="123" autocomplete="off" />
        <input type="hidden" name="m_ts" value="1234567890" />
        <input type="hidden" name="li" value="DEF" />
        <input type="hidden" name="try_number" value="0" />
        <input type="hidden" name="unrecognized_tries" value="0" />
        <ul class="bg bh bi">
            <li class="bh">
                <span class="bj bk" id="u_0_0">Email address or phone number</span>
                <input autocorrect="off" autocapitalize="off" class="bl bm bn" autocomplete="on" id="m_login_email" name="email" aria-labelledby="u_0_0" type="text" />
            </li>
            <li class="bh">
                <div>
                    <span class="bj bk" id="u_0_1">Password</span>
                    <input autocorrect="off" autocapitalize="off" class="bl bm bo bp" autocomplete="on" name="pass" aria-labelledby="u_0_1" type="password" />
                </div>
            </li>
            <li class="bh">
                <input value="Log In" type="submit" name="login" class="n t o bq br bs" />
            </li>
        </ul>
        <div>
            <div class="bt">
                <span class="bu">or</span>
            </div>
            <div class="bv bw">
                <div class="bv bx by" id="signup-button" tabindex="0">
                    <input value="Create New Account" type="submit" name="sign_up" class="n t o bz br ca" />
                </div>
            </div>
        </div>
        <div></div>
        <noscript>
            <input type="hidden" name="_fb_noscript" value="true" />
        </noscript>
    </form>
    """
    email = "<email>"
    password = "<password>"

    method, url, data = sensebook._login.get_form_data(html, email, password)

    assert method == "post"
    assert url == "https://m.facebook.com/login/..."
    assert data == {
        "lsd": "ABC",
        "jazoest": "123",
        "m_ts": "1234567890",
        "li": "DEF",
        "try_number": "0",
        "unrecognized_tries": "0",
        "_fb_noscript": "true",
        "login": "Log In",
        "email": email,
        "pass": password,
    }


@mark.raises(exception=sensebook.LoginError)
def test_invalid_form_data():
    sensebook._login.get_form_data("invalid", None, None)
