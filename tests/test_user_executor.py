from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.operations.UserOperation import UserOperation
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.TokenProvisioner import TokenProvisionerError
from zbxtemplar.decree import User
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


def _users(*dicts):
    return [User.from_dict(d) for d in dicts]


def test_creates_user():
    api = _api()
    api.user.create.return_value = {"userids": ["10"]}
    op = UserOperation(_users({"username": "zbx-service", "role": "User role", "password": "pass"}), api)
    op.execute()
    api.user.create.assert_called_once_with(username="zbx-service", roleid="1", passwd="pass")


def test_updates_existing_user():
    api = _api()
    api.user.get.return_value = [{"userid": "10", "username": "zbx-service"}]
    op = UserOperation(_users({"username": "zbx-service", "role": "User role", "password": "newpass"}), api)
    op.execute()
    api.user.update.assert_called_once_with(userid="10", roleid="1", passwd="newpass")
    api.user.create.assert_not_called()


def test_creates_user_with_groups():
    api = _api()
    api.user.create.return_value = {"userids": ["10"]}
    op = UserOperation(_users({
        "username": "zbx-service",
        "role": "User role",
        "groups": ["Templar Users"],
    }), api)
    op.execute()
    call = api.user.create.call_args[1]
    assert call["usrgrps"] == [{"usrgrpid": "7"}]


def test_creates_user_with_medias():
    api = _api()
    api.user.create.return_value = {"userids": ["10"]}
    op = UserOperation(_users({
        "username": "zbx-service",
        "role": "Super admin role",
        "medias": [
            {"type": "PagerDuty", "sendto": "service-key-123"},
            {"type": "Email", "sendto": "alerts@example.com", "severity": ["AVERAGE", "HIGH", "DISASTER"]},
        ],
    }), api)
    op.execute()
    call = api.user.create.call_args[1]
    assert call["medias"][0] == {"mediatypeid": "5", "sendto": "service-key-123"}
    assert call["medias"][1]["mediatypeid"] == "1"
    assert call["medias"][1]["sendto"] == "alerts@example.com"


def test_creates_user_with_token():
    api = _api()
    api.user.create.return_value = {"userids": ["20"]}
    op = UserOperation(_users({
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT", "expires_at": "NEVER"},
    }), api)
    op.execute()
    api.token.create.assert_called_once_with(name="api-reader-token", userid="20", expires_at=0)
    api.token.generate.assert_called_once_with(tokenid="55")


def test_updates_existing_token_with_force(capsys):
    api = _api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token", "userid": "20"}]
    op = UserOperation(_users({
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT", "expires_at": "NEVER"},
        "force_token": True,
    }), api)
    op.execute()
    api.token.update.assert_called_once_with(tokenid="55", status=0, expires_at=0)
    api.token.create.assert_not_called()
    assert "generated-secret" in capsys.readouterr().out


def test_unknown_role_raises():
    api = _api()
    op = UserOperation(_users({"username": "bad", "role": "Nonexistent", "password": "pass"}), api)
    with pytest.raises(ValueError, match="Role 'Nonexistent' not found"):
        op.execute()


def test_unknown_user_group_raises():
    api = _api()
    op = UserOperation(_users({
        "username": "bad", "role": "User role",
        "groups": ["Nonexistent"],
    }), api)
    with pytest.raises(ValueError, match="User group 'Nonexistent' not found"):
        op.execute()


def test_unknown_media_type_raises():
    api = _api()
    op = UserOperation(_users({
        "username": "bad", "role": "User role",
        "medias": [{"type": "Slack", "sendto": "x"}],
    }), api)
    with pytest.raises(ValueError, match="Media type 'Slack' not found"):
        op.execute()


def test_api_error_on_create_is_wrapped():
    api = _api()
    api.user.create.side_effect = APIRequestError("network drop")
    op = UserOperation(_users({"username": "zbx-service", "role": "User role", "password": "pass"}), api)
    with pytest.raises(ExecutorApiError, match="Failed to create user 'zbx-service'"):
        op.execute()


def test_api_error_on_update_is_wrapped():
    api = _api()
    api.user.get.return_value = [{"userid": "10", "username": "zbx-service"}]
    api.user.update.side_effect = APIRequestError("network drop")
    op = UserOperation(_users({"username": "zbx-service", "role": "User role", "password": "pass"}), api)
    with pytest.raises(ExecutorApiError, match="Failed to update user 'zbx-service'"):
        op.execute()


# --- token provisioner ---

def test_token_update_without_changing_expiration(capsys):
    api = _api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [
        {
            "tokenid": "55",
            "name": "api-reader-token",
            "userid": "20",
            "expires_at": "1710000000",
            "status": "1",
        }
    ]
    op = UserOperation(_users({
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT"},
        "force_token": True,
    }), api)
    op.execute()
    api.token.update.assert_called_once_with(tokenid="55", status=0)
    api.token.create.assert_not_called()
    assert "generated-secret" in capsys.readouterr().out


def test_token_owned_by_other_user_raises():
    api = _api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token", "userid": "99"}]
    op = UserOperation(_users({
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT"},
        "force_token": True,
    }), api)
    with pytest.raises(TokenProvisionerError, match="belongs to a different user"):
        op.execute()


def test_token_requires_expires_at_on_create():
    api = _api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    op = UserOperation(_users({
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": "STDOUT"},
    }), api)
    with pytest.raises(TokenProvisionerError, match="expires_at is required on create"):
        op.execute()


def test_token_writes_to_file(tmp_path):
    api = _api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    out_file = tmp_path / "api-reader.token"
    op = UserOperation(_users({
        "username": "api-reader",
        "role": "User role",
        "token": {"name": "api-reader-token", "store_at": str(out_file), "expires_at": "NEVER"},
    }), api)
    op.execute()
    assert out_file.read_text(encoding="utf-8") == "generated-secret"


def test_duplicate_store_at_raises(tmp_path):
    api = _api()
    out_file = str(tmp_path / "shared.token")
    with pytest.raises(TokenProvisionerError, match="Duplicate store_at path"):
        UserOperation(_users(
            {
                "username": "api-reader-a",
                "role": "User role",
                "token": {"name": "token-a", "store_at": out_file, "expires_at": "NEVER"},
            },
            {
                "username": "api-reader-b",
                "role": "User role",
                "token": {"name": "token-b", "store_at": out_file, "expires_at": "NEVER"},
            },
        ), api)


def test_duplicate_token_name_raises():
    api = _api()
    with pytest.raises(TokenProvisionerError, match="Duplicate token name"):
        UserOperation(_users(
            {
                "username": "api-reader-a",
                "role": "User role",
                "token": {"name": "shared-token", "store_at": "STDOUT", "expires_at": "NEVER"},
            },
            {
                "username": "api-reader-b",
                "role": "User role",
                "token": {"name": "shared-token", "store_at": "b.token", "expires_at": "NEVER"},
            },
        ), api)


def test_existing_store_at_file_raises(tmp_path):
    api = _api()
    out_file = tmp_path / "existing.token"
    out_file.write_text("present", encoding="utf-8")
    with pytest.raises(TokenProvisionerError, match="refusing to overwrite existing file"):
        UserOperation(_users({
            "username": "api-reader",
            "role": "User role",
            "token": {"name": "api-reader-token", "store_at": str(out_file), "expires_at": "NEVER"},
        }), api)
