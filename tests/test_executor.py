from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor import Executor
from zbxtemplar.executor.Executor import _resolve_env, _preflight_env_check
from tests.paths import FIXTURES_DIR

DECREE_USER_GROUP = FIXTURES_DIR / "user_group.decree.yml"
ADD_USER = FIXTURES_DIR / "add_user.yml"


# --- resolve_env ---

def test_resolve_plain_string():
    assert _resolve_env("hello") == "hello"


def test_resolve_env_var(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "secret")
    assert _resolve_env("${TEST_VAR}") == "secret"


def test_resolve_env_var_embedded(monkeypatch):
    monkeypatch.setenv("HOST", "db.local")
    assert _resolve_env("jdbc://${HOST}:5432") == "jdbc://db.local:5432"


def test_resolve_env_missing():
    with pytest.raises(ValueError, match="NONEXISTENT"):
        _resolve_env("${NONEXISTENT}")


def test_resolve_non_string():
    assert _resolve_env(42) == 42


# --- preflight ---

def test_preflight_passes(monkeypatch):
    monkeypatch.setenv("A", "1")
    _preflight_env_check({"key": "${A}"})  # no exception


def test_preflight_reports_all_missing():
    with pytest.raises(ValueError, match="MISSING_A") as exc:
        _preflight_env_check({"x": "${MISSING_A}", "y": [{"z": "${MISSING_B}"}]})
    assert "MISSING_B" in str(exc.value)


# --- set_super_admin ---

def test_set_super_admin_string():
    api = MagicMock()
    Executor(api).set_super_admin("newpass123")
    api.user.update.assert_called_once_with(userid="1", passwd="newpass123")


def test_set_super_admin_dict():
    api = MagicMock()
    Executor(api).set_super_admin({"password": "newpass123"})
    api.user.update.assert_called_once_with(userid="1", passwd="newpass123")


def test_set_super_admin_env_resolved(monkeypatch):
    monkeypatch.setenv("ADMIN_PW", "from_env")
    api = MagicMock()
    Executor(api).set_super_admin({"password": "${ADMIN_PW}"})
    api.user.update.assert_called_once_with(userid="1", passwd="from_env")


def test_set_super_admin_missing_env():
    api = MagicMock()
    with pytest.raises(ValueError, match="UNDEFINED_VAR"):
        Executor(api).set_super_admin({"password": "${UNDEFINED_VAR}"})
    api.user.update.assert_not_called()


# --- apply ---

def test_apply_reads_file_and_imports(tmp_path):
    test_str = "zabbix_export:\n  version: '7.4'\n"
    yaml_file = tmp_path / "templates.yml"
    yaml_file.write_text(test_str)

    api = MagicMock()
    Executor(api).apply(str(yaml_file))
    api.configuration.import_.assert_called_once()
    call_kwargs = api.configuration.import_.call_args[1]
    assert call_kwargs["source"] == test_str
    assert call_kwargs["format"] == "yaml"
    assert call_kwargs["rules"]["templates"]["createMissing"] is True


def test_apply_list_of_files(tmp_path):
    file1 = tmp_path / "templates.yml"
    file1.write_text("zabbix_export:\n  version: '7.4'\n")
    file2 = tmp_path / "hosts.yml"
    file2.write_text("zabbix_export:\n  version: '7.4'\n")

    api = MagicMock()
    Executor(api).apply([str(file1), str(file2)])
    assert api.configuration.import_.call_count == 2


# --- set_macro ---

def test_set_macro_creates_new():
    api = MagicMock()
    api.usermacro.get.return_value = []

    Executor(api).set_macro({"name": "SNMP_COMMUNITY", "value": "public"})
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )


def test_set_macro_updates_existing():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$SNMP_COMMUNITY}", "globalmacroid": "42"}
    ]

    Executor(api).set_macro({"name": "SNMP_COMMUNITY", "value": "private"})
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="42", value="private", type=0
    )
    api.usermacro.createglobal.assert_not_called()


def test_set_macro_secret_type():
    api = MagicMock()
    api.usermacro.get.return_value = []

    Executor(api).set_macro({"name": "DB_PASSWORD", "value": "s3cret", "type": "secret"})
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$DB_PASSWORD}", value="s3cret", type=1
    )


def test_set_macro_from_file(tmp_path):
    macro_file = tmp_path / "macros.yml"
    macro_file.write_text(
        "set_macro:\n"
        "  - name: SNMP_COMMUNITY\n"
        "    value: public\n"
        "  - name: DB_PASSWORD\n"
        "    value: s3cret\n"
        "    type: secret\n"
    )
    api = MagicMock()
    api.usermacro.get.return_value = []

    Executor(api).set_macro(str(macro_file))
    assert api.usermacro.createglobal.call_count == 2
    api.usermacro.createglobal.assert_any_call(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )
    api.usermacro.createglobal.assert_any_call(
        macro="{$DB_PASSWORD}", value="s3cret", type=1
    )


def test_set_macro_mixed_list(tmp_path):
    macro_file = tmp_path / "macros.yml"
    macro_file.write_text(
        "set_macro:\n"
        "  - name: FROM_FILE\n"
        "    value: file_val\n"
    )
    api = MagicMock()
    api.usermacro.get.return_value = []

    Executor(api).set_macro([
        str(macro_file),
        {"name": "INLINE", "value": "inline_val"},
    ])
    assert api.usermacro.createglobal.call_count == 2
    api.usermacro.createglobal.assert_any_call(
        macro="{$FROM_FILE}", value="file_val", type=0
    )
    api.usermacro.createglobal.assert_any_call(
        macro="{$INLINE}", value="inline_val", type=0
    )


def test_set_macro_batch():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$EXISTING}", "globalmacroid": "10"}
    ]

    Executor(api).set_macro([
        {"name": "EXISTING", "value": "updated"},
        {"name": "NEW_ONE", "value": "fresh"},
    ])
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="10", value="updated", type=0
    )
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$NEW_ONE}", value="fresh", type=0
    )


def test_set_macro_missing_name():
    api = MagicMock()
    with pytest.raises(ValueError, match="missing required field 'name'"):
        Executor(api).set_macro({"value": "public"})
    api.usermacro.get.assert_not_called()


def test_set_macro_missing_value():
    api = MagicMock()
    with pytest.raises(ValueError, match="missing required field 'value'"):
        Executor(api).set_macro({"name": "FOO"})
    api.usermacro.get.assert_not_called()


def test_set_macro_invalid_type():
    api = MagicMock()
    with pytest.raises(ValueError, match="invalid type 'bogus'"):
        Executor(api).set_macro({"name": "FOO", "value": "bar", "type": "bogus"})
    api.usermacro.get.assert_not_called()


def test_set_macro_string_is_file_path():
    api = MagicMock()
    with pytest.raises(FileNotFoundError):
        Executor(api).set_macro("nonexistent.yml")


# --- decree ---

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


def test_decree_creates_user_group():
    api = _decree_api()
    Executor(api).decree(str(DECREE_USER_GROUP))
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

    Executor(api).decree({
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
        Executor(api).decree({
            "user_group": [{
                "name": "Bad Group",
                "host_groups": [{"name": "Nonexistent", "permission": "READ"}],
            }]
        })


def test_decree_invalid_permission():
    api = _decree_api()
    with pytest.raises(ValueError, match="Invalid permission 'ADMIN'"):
        Executor(api).decree({
            "user_group": [{
                "name": "Bad Group",
                "host_groups": [{"name": "Linux servers", "permission": "ADMIN"}],
            }]
        })


def test_decree_invalid_gui_access():
    api = _decree_api()
    with pytest.raises(ValueError, match="Invalid gui_access 'YES'"):
        Executor(api).decree({
            "user_group": [{
                "name": "Bad Group",
                "gui_access": "YES",
            }]
        })


def test_decree_unknown_keys_ignored():
    api = _decree_api()
    Executor(api).decree({"something_else": []})
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

    Executor(api).decree([str(groups_file), str(users_file)])
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

    Executor(api).decree([
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

    Executor(api).decree({
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
    return api


def test_add_user_from_file(monkeypatch):
    monkeypatch.setenv("ZBX_SERVICE_PASSWORD", "s3cret")
    api = _user_api()
    api.user.get.side_effect = [
        [],  # first call: check existing (both users absent)
        [{"userid": "20", "username": "api-reader"}],  # after api-reader create, for token
    ]
    api.token.get.return_value = []

    Executor(api).add_user(str(ADD_USER))

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
    api.token.create.assert_called_once_with(name="api-reader-token", userid="20")


def test_add_user_updates_existing():
    api = _user_api()
    api.user.get.return_value = [{"userid": "10", "username": "zbx-service"}]

    Executor(api).add_user({
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
    api.user.get.side_effect = [
        [],  # first call: check existing
        [{"userid": "20", "username": "api-reader"}],  # second call: after create
    ]
    api.token.get.return_value = []

    Executor(api).add_user({
        "username": "api-reader",
        "role": "User role",
        "token": "read-only-token",
    })
    api.user.create.assert_called_once()
    api.token.create.assert_called_once_with(
        name="api-reader-token",
        userid="20",
    )


def test_add_user_token_exists_raises():
    api = _user_api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token"}]

    with pytest.raises(ValueError, match="already exists.*force_token"):
        Executor(api).add_user({
            "username": "api-reader",
            "role": "User role",
            "token": "read-only-token",
        })
    api.token.create.assert_not_called()
    api.token.delete.assert_not_called()


def test_add_user_force_token_recreates():
    api = _user_api()
    api.user.get.return_value = [{"userid": "20", "username": "api-reader"}]
    api.token.get.return_value = [{"tokenid": "55", "name": "api-reader-token"}]

    Executor(api).add_user({
        "username": "api-reader",
        "role": "User role",
        "token": "read-only-token",
        "force_token": True,
    })
    api.token.delete.assert_called_once_with("55")
    api.token.create.assert_called_once_with(
        name="api-reader-token",
        userid="20",
    )


def test_add_user_unknown_role():
    api = _user_api()
    with pytest.raises(ValueError, match="Role 'Nonexistent' not found"):
        Executor(api).add_user({
            "username": "bad",
            "role": "Nonexistent",
            "password": "pass",
        })


def test_add_user_unknown_group():
    api = _user_api()
    with pytest.raises(ValueError, match="User group 'Nonexistent' not found"):
        Executor(api).add_user({
            "username": "bad",
            "role": "User role",
            "password": "pass",
            "groups": ["Nonexistent"],
        })


def test_add_user_unknown_media_type():
    api = _user_api()
    with pytest.raises(ValueError, match="Media type 'Slack' not found"):
        Executor(api).add_user({
            "username": "bad",
            "role": "User role",
            "password": "pass",
            "medias": [{"type": "Slack", "sendto": "x"}],
        })