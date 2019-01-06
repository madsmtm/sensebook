from pytest import fixture


@fixture
def patcher(mocker):
    return lambda *args, **kwargs: mocker.patch.object(*args, autospec=True, **kwargs)
