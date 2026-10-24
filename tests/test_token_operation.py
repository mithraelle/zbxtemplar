from unittest.mock import MagicMock

import pytest

from zbxtemplar.dicts.Scroll import Scroll
from zbxtemplar.executor.ScrollExecutor import ScrollExecutor


def _api():
    api = MagicMock()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = []
    api.token.create.return_value = {"tokenids": ["55"]}
    api.token.generate.return_value = {"token": "generated-secret"}
    return api


def _set_token(*entries):
    return Scroll.from_data({"set_token": list(entries)})


def test_set_token_for_existing_user(capsys):
    api = _api()
    scroll = _set_token({
        "username": "api-reader",
        "token": {"name": "api-reader-token", "store_at": "STDOUT", "expires_at": "NEVER"},
    })

    ScrollExecutor(scroll, api).execute()

    api.token.create.assert_called_once_with(name="api-reader-token", userid="20", expires_at=0)
    api.token.generate.assert_called_once_with(tokenid="55")
    api.user.create.assert_not_called()
    api.user.update.assert_not_called()
    assert "generated-secret" in capsys.readouterr().out


def test_set_token_unknown_user_raises_before_any_token_call():
    api = _api()
    scroll = _set_token(
        {"username": "api-reader", "token": {"name": "reader", "store_at": "STDOUT", "expires_at": "NEVER"}},
        {"username": "ghost", "token": {"name": "ghost", "store_at": "STDOUT", "expires_at": "NEVER"}},
    )

    with pytest.raises(ValueError, match="User\\(s\\) not found in Zabbix: ghost"):
        ScrollExecutor(scroll, api).execute()

    api.token.create.assert_not_called()
