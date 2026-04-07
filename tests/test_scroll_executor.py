from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.ScrollExecutor import ScrollExecutor
from zbxtemplar.executor.exceptions import ExecutorParseError


# --- set_super_admin ---

def test_set_super_admin_string():
    api = MagicMock()
    ScrollExecutor(api).set_super_admin("newpass123")
    api.user.update.assert_called_once_with(userid="1", passwd="newpass123")


def test_set_super_admin_dict():
    api = MagicMock()
    ScrollExecutor(api).set_super_admin({"password": "newpass123"})
    api.user.update.assert_called_once_with(userid="1", passwd="newpass123")


def test_set_super_admin_env_resolved(monkeypatch):
    monkeypatch.setenv("ADMIN_PW", "from_env")
    api = MagicMock()
    ScrollExecutor(api).set_super_admin({"password": "${ADMIN_PW}"})
    api.user.update.assert_called_once_with(userid="1", passwd="from_env")


def test_set_super_admin_missing_env():
    api = MagicMock()
    with pytest.raises(ValueError, match="UNDEFINED_VAR"):
        ScrollExecutor(api).set_super_admin({"password": "${UNDEFINED_VAR}"})
    api.user.update.assert_not_called()


# --- apply ---

def test_apply_reads_file_and_imports(tmp_path):
    test_str = "zabbix_export:\n  version: '7.4'\n"
    yaml_file = tmp_path / "templates.yml"
    yaml_file.write_text(test_str)

    api = MagicMock()
    ScrollExecutor(api).apply(str(yaml_file))
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
    ScrollExecutor(api).apply([str(file1), str(file2)])
    assert api.configuration.import_.call_count == 2


# --- set_macro ---

def test_set_macro_creates_new():
    api = MagicMock()
    api.usermacro.get.return_value = []

    ScrollExecutor(api).set_macro({"name": "SNMP_COMMUNITY", "value": "public"})
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )


def test_set_macro_updates_existing():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$SNMP_COMMUNITY}", "globalmacroid": "42"}
    ]

    ScrollExecutor(api).set_macro({"name": "SNMP_COMMUNITY", "value": "private"})
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="42", value="private", type=0
    )
    api.usermacro.createglobal.assert_not_called()


def test_set_macro_secret_type():
    api = MagicMock()
    api.usermacro.get.return_value = []

    ScrollExecutor(api).set_macro({"name": "DB_PASSWORD", "value": "s3cret", "type": "SECRET_TEXT"})
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
        "    type: SECRET_TEXT\n"
    )
    api = MagicMock()
    api.usermacro.get.return_value = []

    ScrollExecutor(api).set_macro(str(macro_file))
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

    ScrollExecutor(api).set_macro([
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

    ScrollExecutor(api).set_macro([
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
        ScrollExecutor(api).set_macro({"value": "public"})
    api.usermacro.get.assert_not_called()


def test_set_macro_missing_value():
    api = MagicMock()
    with pytest.raises(ValueError, match="missing required field 'value'"):
        ScrollExecutor(api).set_macro({"name": "FOO"})
    api.usermacro.get.assert_not_called()


def test_set_macro_invalid_type():
    api = MagicMock()
    with pytest.raises(ValueError, match="invalid type 'bogus'"):
        ScrollExecutor(api).set_macro({"name": "FOO", "value": "bar", "type": "bogus"})
    api.usermacro.get.assert_not_called()


def test_set_macro_string_is_file_path():
    api = MagicMock()
    with pytest.raises(FileNotFoundError):
        ScrollExecutor(api).set_macro("nonexistent.yml")


# --- run_scroll error handling ---

def test_yaml_parse_error_wrapped(tmp_path):
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("invalid: [yaml\n", encoding="utf-8")
    api = MagicMock()

    with pytest.raises(ExecutorParseError, match="Failed to parse") as exc:
        ScrollExecutor(api).run_scroll(str(bad_yaml))

    assert exc.value.path == str(bad_yaml)