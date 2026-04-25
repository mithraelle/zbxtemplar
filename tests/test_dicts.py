"""Tests for the dicts deserialization layer (Schema, Decree, Scroll)."""
import pytest

from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.dicts.Schema import Schema
from zbxtemplar.dicts.Scroll import Scroll
from zbxtemplar.decree import UserGroup, User
from zbxtemplar.decree.Encryption import HostEncryption
from zbxtemplar.zabbix.macro import Macro


# --- Macro validation ---

def test_macro_missing_name():
    with pytest.raises(KeyError):
        Macro.from_dict({"value": "public"})


def test_macro_invalid_type():
    with pytest.raises(ValueError, match="is not a valid MacroType"):
        Macro.from_dict({"name": "FOO", "value": "bar", "type": "bogus"})


# --- Scroll macro loading ---

def test_scroll_macro_from_file(tmp_path):
    macro_file = tmp_path / "macros.yml"
    macro_file.write_text(
        "set_macro:\n"
        "  - name: SNMP_COMMUNITY\n"
        "    value: public\n"
        "  - name: DB_PASSWORD\n"
        "    value: s3cret\n"
        "    type: SECRET_TEXT\n"
    )
    scroll = Scroll.from_data({"set_macro": str(macro_file)})
    assert len(scroll.set_macro) == 2
    assert scroll.set_macro[0].full_name == "{$SNMP_COMMUNITY}"
    assert scroll.set_macro[1].full_name == "{$DB_PASSWORD}"


def test_scroll_macro_mixed_list(tmp_path):
    macro_file = tmp_path / "macros.yml"
    macro_file.write_text(
        "set_macro:\n"
        "  - name: FROM_FILE\n"
        "    value: file_val\n"
    )
    scroll = Scroll.from_data({"set_macro": [
        str(macro_file),
        {"name": "INLINE", "value": "inline_val"},
    ]})
    assert len(scroll.set_macro) == 2
    names = {m.full_name for m in scroll.set_macro}
    assert names == {"{$FROM_FILE}", "{$INLINE}"}


def test_scroll_macro_string_is_file_path():
    with pytest.raises(FileNotFoundError):
        Scroll.from_data({"set_macro": "nonexistent.yml"})


# --- Decree validation ---

def test_decree_unknown_keys_raises():
    with pytest.raises(ValueError, match="unknown key 'something_else'"):
        Decree.from_dict({"something_else": []})


def test_decree_invalid_permission():
    with pytest.raises(ValueError, match="expected Permission, got 'ADMIN'"):
        Decree.from_dict({
            "user_group": [{
                "name": "Bad Group",
                "host_groups": [{"name": "Linux servers", "permission": "ADMIN"}],
            }]
        })


def test_decree_invalid_gui_access():
    with pytest.raises(ValueError, match="expected GuiAccess, got 'YES'"):
        Decree.from_dict({
            "user_group": [{
                "name": "Bad Group",
                "gui_access": "YES",
            }]
        })


# --- Decree file loading ---

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
    decree = Decree.from_data([str(groups_file), str(users_file)])
    assert len(decree.user_group) == 1
    assert decree.user_group[0].name == "Ops Team"
    assert len(decree.add_user) == 1
    assert decree.add_user[0].username == "ops-bot"


def test_decree_mixed_files_and_inline(tmp_path):
    groups_file = tmp_path / "groups.yml"
    groups_file.write_text(
        "user_group:\n"
        "  - name: Ops Team\n"
        "    gui_access: DEFAULT\n"
    )
    decree = Decree.from_data([
        str(groups_file),
        {"add_user": [{"username": "ops-bot", "role": "User role", "password": "pass"}]},
    ])
    assert len(decree.user_group) == 1
    assert len(decree.add_user) == 1


# --- Encryption validation ---

def test_encryption_requires_host():
    with pytest.raises(ValueError, match="missing required key.*host"):
        HostEncryption.from_dict({"connect": "UNENCRYPTED", "accept": "UNENCRYPTED"})


def test_token_requires_store_at():
    with pytest.raises(ValueError, match="missing required key.*store_at"):
        User.from_dict({
            "username": "api-reader",
            "role": "User role",
            "token": {"name": "api-reader-token", "expires_at": "NEVER"},
        })


# --- resolve_env ---

_resolve_env = Schema._resolve_env


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


def test_resolve_env_dict(monkeypatch):
    monkeypatch.setenv("A", "1")
    assert _resolve_env({"key": "${A}"}) == {"key": "1"}


def test_resolve_env_reports_all_missing():
    with pytest.raises(ValueError, match="MISSING_A") as exc:
        _resolve_env({"x": "${MISSING_A}", "y": [{"z": "${MISSING_B}"}]})
    assert "MISSING_B" in str(exc.value)
