from unittest.mock import MagicMock

import pytest

from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
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


def _run(api, data):
    decree = Decree.from_data(data)
    ex = DecreeExecutor(decree, api)
    ex.execute()


# --- decree ---

def test_decree_creates_user_group():
    api = _decree_api()
    decree = Decree.from_file(str(DECREE_USER_GROUP))
    ex = DecreeExecutor(decree, api)
    ex.execute()
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

    _run(api, {
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
    decree = Decree.from_dict({
        "user_group": [{
            "name": "Bad Group",
            "host_groups": [{"name": "Nonexistent", "permission": "READ"}],
        }]
    })
    ex = DecreeExecutor(decree, api)
    with pytest.raises(ValueError, match="Host group 'Nonexistent' not found"):
        ex.execute()


def test_decree_combined_user_group_and_add_user():
    api = _decree_api()
    api.role.get.return_value = [{"roleid": "1", "name": "User role"}]
    api.mediatype.get.return_value = []
    api.user.get.return_value = []
    api.token.get.return_value = []

    _run(api, {
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


# --- add_user from file (integration) ---

def test_add_user_from_file(monkeypatch):
    monkeypatch.setenv("ZBX_SERVICE_PASSWORD", "s3cret")
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
    api.user.create.side_effect = [
        {"userids": ["10"]},  # zbx-service
        {"userids": ["20"]},  # api-reader
    ]
    api.token.get.return_value = []
    api.token.create.return_value = {"tokenids": ["55"]}
    api.token.generate.return_value = {"token": "generated-secret"}

    Decree._resolve_envs = True
    try:
        decree = Decree.from_file(str(ADD_USER))
    finally:
        Decree._resolve_envs = False
    ex = DecreeExecutor(decree, api)
    ex.execute()

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
