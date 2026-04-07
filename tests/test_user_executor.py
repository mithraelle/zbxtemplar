from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.UserExecutor import UserExecutor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zabbix_utils import APIRequestError


def _api():
    api = MagicMock()
    api.role.get.return_value = [
        {"roleid": "1", "name": "User role"},
        {"roleid": "3", "name": "Super admin role"},
    ]
    api.usergroup.get.return_value = [
        {"usrgrpid": "7", "name": "Templar Users"},
    ]
    api.mediatype.get.return_value = [
        {"mediatypeid": "5", "name": "PagerDuty"},
        {"mediatypeid": "1", "name": "Email"},
    ]
    api.user.get.return_value = []
    api.token.get.return_value = []
    api.token.create.return_value = {"tokenids": ["55"]}
    api.token.generate.return_value = {"token": "generated-secret"}
    return api


def _executor(api):
    return UserExecutor(api, lambda p: p)


def test_creates_user():
    api = _api()
    api.user.create.return_value = {"userids": ["10"]}
    _executor(api).execute([{"username": "zbx-service", "role": "User role", "password": "pass"}])
    api.user.create.assert_called_once_with(username="zbx-service", roleid="1", passwd="pass")


def test_updates_existing_user():
    api = _api()
    api.user.get.return_value = [{"userid": "10", "username": "zbx-service"}]
    _executor(api).execute([{"username": "zbx-service", "role": "User role", "password": "newpass"}])
    api.user.update.assert_called_once_with(userid="10", roleid="1", passwd="newpass")
    api.user.create.assert_not_called()


def test_creates_user_with_groups():
    api = _api()
    api.user.create.return_value = {"userids": ["10"]}
    _executor(api).execute([{
        "username": "zbx-service",
        "role": "User role",
        "groups": ["Templar Users"],
    }])
    call = api.user.create.call_args[1]
    assert call["usrgrps"] == [{"usrgrpid": "7"}]


def test_creates_user_with_medias():
    api = _api()
    api.user.create.return_value = {"userids": ["10"]}
    _executor(api).execute([{
        "username": "zbx-service",
        "role": "Super admin role",
        "medias": [
            {"type": "PagerDuty", "sendto": "service-key-123"},
            {"type": "Email", "sendto": "alerts@example.com", "severity": ["AVERAGE", "HIGH", "DISASTER"]},
        ],
    }])
    call = api.user.create.call_args[1]
    assert call["medias"][0] == {"mediatypeid": "5", "sendto": "service-key-123"}
    assert call["medias"][1]["mediatypeid"] == "1"
    assert call["medias"][1]["sendto"] == "alerts@example.com"


def test_creates_user_with_token():
    api = _api()
    api.user.create.return_value = {"userids": ["20"]}
    _executor(api).execute([{
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT", "expires_at": "NEVER"},
    }])
    api.token.create.assert_called_once_with(name="api-reader-token", userid="20", expires_at=0)
    api.token.generate.assert_called_once_with(tokenid="55")


def test_updates_existing_token_with_force(capsys):
    api = _api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token", "userid": "20"}]
    _executor(api).execute([{
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT", "expires_at": "NEVER"},
        "force_token": True,
    }])
    api.token.update.assert_called_once_with(tokenid="55", status=0, expires_at=0)
    api.token.create.assert_not_called()
    assert "generated-secret" in capsys.readouterr().out


def test_unknown_role_raises():
    api = _api()
    with pytest.raises(ValueError, match="Role 'Nonexistent' not found"):
        _executor(api).execute([{"username": "bad", "role": "Nonexistent", "password": "pass"}])


def test_unknown_user_group_raises():
    api = _api()
    with pytest.raises(ValueError, match="User group 'Nonexistent' not found"):
        _executor(api).execute([{
            "username": "bad", "role": "User role",
            "groups": ["Nonexistent"],
        }])


def test_unknown_media_type_raises():
    api = _api()
    with pytest.raises(ValueError, match="Media type 'Slack' not found"):
        _executor(api).execute([{
            "username": "bad", "role": "User role",
            "medias": [{"type": "Slack", "sendto": "x"}],
        }])



def test_api_error_on_create_is_wrapped():
    api = _api()
    api.user.create.side_effect = APIRequestError("network drop")
    with pytest.raises(ExecutorApiError, match="Failed to create user 'zbx-service'"):
        _executor(api).execute([{"username": "zbx-service", "role": "User role", "password": "pass"}])


def test_api_error_on_update_is_wrapped():
    api = _api()
    api.user.get.return_value = [{"userid": "10", "username": "zbx-service"}]
    api.user.update.side_effect = APIRequestError("network drop")
    with pytest.raises(ExecutorApiError, match="Failed to update user 'zbx-service'"):
        _executor(api).execute([{"username": "zbx-service", "role": "User role", "password": "pass"}])