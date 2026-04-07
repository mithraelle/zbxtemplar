from unittest.mock import MagicMock

import pytest
from zabbix_utils import APIRequestError

from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.TokenExecutor import TokenExecutorError
from zbxtemplar.executor.exceptions import ExecutorApiError, ExecutorParseError
from tests.paths import FIXTURES_DIR

DECREE_USER_GROUP = FIXTURES_DIR / "user_group.decree.yml"
ADD_USER = FIXTURES_DIR / "add_user.yml"


def _decree_api():
    api = MagicMock()
    api.hostgroup.get.return_value = [
        {"groupid": "2", "name": "Linux servers"},
        {"groupid": "3", "name": "Virtual machines"},
    ]
    api.templategroup.get.return_value = [
        {"groupid": "10", "name": "Test Template"},
    ]
    api.usergroup.get.return_value = []
    return api


def _user_api():
    api = MagicMock()
    api.role.get.return_value = [
        {"roleid": "1", "name": "User role"},
        {"roleid": "2", "name": "Admin role"},
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


# --- decree ---

def test_decree_creates_user_group():
    api = _decree_api()
    DecreeExecutor(api).decree(str(DECREE_USER_GROUP))
    api.usergroup.create.assert_called_once_with(
        name="Templar Users",
        gui_access=1,
        hostgroup_rights=[
            {"id": "2", "permission": 0},
            {"id": "3", "permission": 2},
        ],
        templategroup_rights=[
            {"id": "10", "permission": 3},
        ],
    )


def test_decree_updates_existing_user_group():
    api = _decree_api()
    api.usergroup.get.return_value = [{"usrgrpid": "99", "name": "Templar Users"}]

    DecreeExecutor(api).decree({
        "user_group": [{
            "name": "Templar Users",
            "gui_access": "DISABLED",
        }]
    })
    api.usergroup.update.assert_called_once_with(
        usrgrpid="99",
        gui_access=3,
    )
    api.usergroup.create.assert_not_called()


def test_decree_unknown_host_group():
    api = _decree_api()
    with pytest.raises(ValueError, match="Host group 'Nonexistent' not found"):
        DecreeExecutor(api).decree({
            "user_group": [{
                "name": "Bad Group",
                "host_groups": [{"name": "Nonexistent", "permission": "READ"}],
            }]
        })


def test_decree_invalid_permission():
    api = _decree_api()
    with pytest.raises(ValueError, match="Invalid permission 'ADMIN'"):
        DecreeExecutor(api).decree({
            "user_group": [{
                "name": "Bad Group",
                "host_groups": [{"name": "Linux servers", "permission": "ADMIN"}],
            }]
        })


def test_decree_invalid_gui_access():
    api = _decree_api()
    with pytest.raises(ValueError, match="Invalid gui_access 'YES'"):
        DecreeExecutor(api).decree({
            "user_group": [{
                "name": "Bad Group",
                "gui_access": "YES",
            }]
        })


def test_decree_unknown_keys_raises():
    api = _decree_api()
    with pytest.raises(ExecutorParseError, match="Unknown keys in decree document: something_else"):
        DecreeExecutor(api).decree({"something_else": []})
    api.usergroup.create.assert_not_called()
    api.usergroup.update.assert_not_called()


def test_decree_list_of_files(tmp_path):
    groups_file = tmp_path / "groups.yml"
    groups_file.write_text(
        "user_group:\n"
        "  - name: Ops Team\n"
        "    gui_access: DEFAULT\n"
    )
    users_file = tmp_path / "users.yml"
    users_file.write_text(
        "add_user:\n"
        "  - username: ops-bot\n"
        "    role: User role\n"
        "    password: pass123\n"
    )
    api = _decree_api()
    api.role.get.return_value = [{"roleid": "1", "name": "User role"}]
    api.mediatype.get.return_value = []
    api.user.get.return_value = []

    DecreeExecutor(api).decree([str(groups_file), str(users_file)])
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()


def test_decree_mixed_files_and_inline(tmp_path):
    groups_file = tmp_path / "groups.yml"
    groups_file.write_text(
        "user_group:\n"
        "  - name: Ops Team\n"
        "    gui_access: DEFAULT\n"
    )
    api = _decree_api()
    api.role.get.return_value = [{"roleid": "1", "name": "User role"}]
    api.mediatype.get.return_value = []
    api.user.get.return_value = []

    DecreeExecutor(api).decree([
        str(groups_file),
        {"add_user": [{"username": "ops-bot", "role": "User role", "password": "pass"}]},
    ])
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()


def test_decree_combined_user_group_and_add_user():
    api = _decree_api()
    api.role.get.return_value = [{"roleid": "1", "name": "User role"}]
    api.mediatype.get.return_value = []
    api.user.get.return_value = []
    api.token.get.return_value = []

    DecreeExecutor(api).decree({
        "user_group": [{
            "name": "Ops Team",
            "gui_access": "DEFAULT",
        }],
        "add_user": [{
            "username": "ops-bot",
            "role": "User role",
            "password": "pass123",
        }],
    })
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()


# --- add_user ---

def test_add_user_from_file(monkeypatch):
    monkeypatch.setenv("ZBX_SERVICE_PASSWORD", "s3cret")
    api = _user_api()
    api.user.get.return_value = []
    api.user.create.side_effect = [
        {"userids": ["10"]},  # zbx-service
        {"userids": ["20"]},  # api-reader
    ]
    api.token.get.return_value = []

    DecreeExecutor(api).add_user(str(ADD_USER))

    # First user: zbx-service with password, group, medias
    first_call = api.user.create.call_args_list[0][1]
    assert first_call["username"] == "zbx-service"
    assert first_call["roleid"] == "3"
    assert first_call["passwd"] == "s3cret"
    assert first_call["usrgrps"] == [{"usrgrpid": "7"}]
    assert first_call["medias"] == [
        {"mediatypeid": "5", "sendto": "service-key-123"},
        {"mediatypeid": "1", "sendto": "alerts@example.com", "severity": 56},
    ]

    # Second user: api-reader with token
    second_call = api.user.create.call_args_list[1][1]
    assert second_call["username"] == "api-reader"
    assert second_call["roleid"] == "1"
    api.token.create.assert_called_once_with(
        name="api-reader-token",
        userid="20",
        expires_at=0,
    )
    api.token.generate.assert_called_once_with(tokenid="55")


def test_add_user_updates_existing():
    api = _user_api()
    api.user.get.return_value = [{"userid": "10", "username": "zbx-service"}]

    DecreeExecutor(api).add_user({
        "username": "zbx-service",
        "role": "Admin role",
        "password": "newpass",
    })
    api.user.update.assert_called_once_with(
        userid="10",
        roleid="2",
        passwd="newpass",
    )
    api.user.create.assert_not_called()


def test_add_user_creates_token():
    api = _user_api()
    api.user.get.return_value = []
    api.user.create.return_value = {"userids": ["20"]}
    api.token.get.return_value = []

    DecreeExecutor(api).add_user({
        "username": "api-reader",
        "role": "User role",
        "token": {
            "name": "api-reader-token",
            "store_at": "STDOUT",
            "expires_at": "NEVER",
        },
    })
    api.user.create.assert_called_once()
    api.token.create.assert_called_once_with(
        name="api-reader-token",
        userid="20",
        expires_at=0,
    )
    api.token.generate.assert_called_once_with(tokenid="55")


def test_add_user_updates_existing_token_without_changing_expiration(capsys):
    api = _user_api()
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

    DecreeExecutor(api).add_user({
        "username": "api-reader",
        "role": "User role",
        "token": {
            "name": "api-reader-token",
            "store_at": "STDOUT",
        },
        "force_token": True,
    })
    api.token.update.assert_called_once_with(tokenid="55", status=0)
    api.token.create.assert_not_called()
    assert "generated-secret" in capsys.readouterr().out


def test_add_user_force_token_updates():
    api = _user_api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token", "userid": "20"}]

    DecreeExecutor(api).add_user({
        "username": "api-reader",
        "role": "User role",
        "token": {
            "name": "api-reader-token",
            "store_at": "STDOUT",
            "expires_at": "NEVER",
        },
        "force_token": True,
    })
    api.token.update.assert_called_once_with(tokenid="55", status=0, expires_at=0)
    api.token.create.assert_not_called()
    api.token.generate.assert_called_once_with(tokenid="55")


def test_add_user_rejects_token_owned_by_other_user():
    api = _user_api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token", "userid": "99"}]

    with pytest.raises(TokenExecutorError, match="belongs to a different user"):
        DecreeExecutor(api).add_user({
            "username": "api-reader",
            "role": "User role",
            "token": {
                "name": "api-reader-token",
                "store_at": "STDOUT",
            },
            "force_token": True,
        })


def test_add_user_requires_token_store_at():
    api = _user_api()
    with pytest.raises(ValueError, match="missing required key.*store_at"):
        DecreeExecutor(api).add_user({
            "username": "api-reader",
            "role": "User role",
            "token": {
                "name": "api-reader-token",
                "expires_at": "NEVER",
            },
        })


def test_add_user_requires_expires_at_on_create():
    api = _user_api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]

    with pytest.raises(TokenExecutorError, match="expires_at is required on create"):
        DecreeExecutor(api).add_user({
            "username": "api-reader",
            "role": "User role",
            "token": {
                "name": "api-reader-token",
                "store_at": "STDOUT",
            },
        })


def test_add_user_writes_token_to_file(tmp_path):
    api = _user_api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    out_file = tmp_path / "api-reader.token"

    DecreeExecutor(api).add_user({
        "username": "api-reader",
        "role": "User role",
        "token": {
            "name": "api-reader-token",
            "store_at": str(out_file),
            "expires_at": "NEVER",
        },
    })

    assert out_file.read_text(encoding="utf-8") == "generated-secret"


def test_add_user_rejects_duplicate_store_at(tmp_path):
    api = _user_api()
    out_file = str(tmp_path / "shared.token")

    with pytest.raises(TokenExecutorError, match="Duplicate store_at path"):
        DecreeExecutor(api).add_user([
            {
                "username": "api-reader-a",
                "role": "User role",
                "token": {
                    "name": "token-a",
                    "store_at": out_file,
                    "expires_at": "NEVER",
                },
            },
            {
                "username": "api-reader-b",
                "role": "User role",
                "token": {
                    "name": "token-b",
                    "store_at": out_file,
                    "expires_at": "NEVER",
                },
            },
        ])


def test_add_user_rejects_duplicate_token_name():
    api = _user_api()

    with pytest.raises(TokenExecutorError, match="Duplicate token name"):
        DecreeExecutor(api).add_user([
            {
                "username": "api-reader-a",
                "role": "User role",
                "token": {
                    "name": "shared-token",
                    "store_at": "STDOUT",
                    "expires_at": "NEVER",
                },
            },
            {
                "username": "api-reader-b",
                "role": "User role",
                "token": {
                    "name": "shared-token",
                    "store_at": "b.token",
                    "expires_at": "NEVER",
                },
            },
        ])


def test_add_user_rejects_existing_store_at_file(tmp_path):
    api = _user_api()
    out_file = tmp_path / "existing.token"
    out_file.write_text("present", encoding="utf-8")

    with pytest.raises(TokenExecutorError, match="refusing to overwrite existing file"):
        DecreeExecutor(api).add_user({
            "username": "api-reader",
            "role": "User role",
            "token": {
                "name": "api-reader-token",
                "store_at": str(out_file),
                "expires_at": "NEVER",
            },
        })


def test_add_user_unknown_role():
    api = _user_api()
    with pytest.raises(ValueError, match="Role 'Nonexistent' not found"):
        DecreeExecutor(api).add_user({
            "username": "bad",
            "role": "Nonexistent",
            "password": "pass",
        })


def test_add_user_unknown_group():
    api = _user_api()
    with pytest.raises(ValueError, match="User group 'Nonexistent' not found"):
        DecreeExecutor(api).add_user({
            "username": "bad",
            "role": "User role",
            "password": "pass",
            "groups": ["Nonexistent"],
        })


def test_add_user_unknown_media_type():
    api = _user_api()
    with pytest.raises(ValueError, match="Media type 'Slack' not found"):
        DecreeExecutor(api).add_user({
            "username": "bad",
            "role": "User role",
            "password": "pass",
            "medias": [{"type": "Slack", "sendto": "x"}],
        })


# --- error handling ---

def test_api_error_wrapped():
    api = _decree_api()
    api.usergroup.create.side_effect = APIRequestError("Simulated network drop")

    with pytest.raises(ExecutorApiError, match="Failed to create user group 'Ops Team': Simulated network drop"):
        DecreeExecutor(api).decree({
            "user_group": [{
                "name": "Ops Team",
                "gui_access": "DEFAULT",
            }]
        })