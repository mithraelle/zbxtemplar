from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.operations.MacroOperation import MacroOperation


def _executor(api):
    return MacroOperation(api)


def test_creates_new():
    api = MagicMock()
    api.usermacro.get.return_value = []

    op = _executor(api)
    op.from_data({"name": "SNMP_COMMUNITY", "value": "public"})
    op.execute()
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )


def test_updates_existing():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$SNMP_COMMUNITY}", "globalmacroid": "42"}
    ]

    op = _executor(api)
    op.from_data({"name": "SNMP_COMMUNITY", "value": "private"})
    op.execute()
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="42", value="private", type=0
    )
    api.usermacro.createglobal.assert_not_called()


def test_secret_type():
    api = MagicMock()
    api.usermacro.get.return_value = []

    op = _executor(api)
    op.from_data({"name": "DB_PASSWORD", "value": "s3cret", "type": "SECRET_TEXT"})
    op.execute()
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$DB_PASSWORD}", value="s3cret", type=1
    )


def test_from_file(tmp_path):
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

    op = _executor(api)
    op.from_data(str(macro_file))
    op.execute()
    assert api.usermacro.createglobal.call_count == 2
    api.usermacro.createglobal.assert_any_call(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )
    api.usermacro.createglobal.assert_any_call(
        macro="{$DB_PASSWORD}", value="s3cret", type=1
    )


def test_mixed_list(tmp_path):
    macro_file = tmp_path / "macros.yml"
    macro_file.write_text(
        "set_macro:\n"
        "  - name: FROM_FILE\n"
        "    value: file_val\n"
    )
    api = MagicMock()
    api.usermacro.get.return_value = []

    op = _executor(api)
    op.from_data([
        str(macro_file),
        {"name": "INLINE", "value": "inline_val"},
    ])
    op.execute()
    assert api.usermacro.createglobal.call_count == 2
    api.usermacro.createglobal.assert_any_call(
        macro="{$FROM_FILE}", value="file_val", type=0
    )
    api.usermacro.createglobal.assert_any_call(
        macro="{$INLINE}", value="inline_val", type=0
    )


def test_batch():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$EXISTING}", "globalmacroid": "10"}
    ]

    op = _executor(api)
    op.from_data([
        {"name": "EXISTING", "value": "updated"},
        {"name": "NEW_ONE", "value": "fresh"},
    ])
    op.execute()
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="10", value="updated", type=0
    )
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$NEW_ONE}", value="fresh", type=0
    )


def test_missing_name():
    api = MagicMock()
    op = _executor(api)
    with pytest.raises(KeyError):
        op.from_data({"value": "public"})
    api.usermacro.get.assert_not_called()


def test_invalid_type():
    api = MagicMock()
    op = _executor(api)
    with pytest.raises(ValueError, match="is not a valid MacroType"):
        op.from_data({"name": "FOO", "value": "bar", "type": "bogus"})
    api.usermacro.get.assert_not_called()


def test_string_is_file_path():
    api = MagicMock()
    op = _executor(api)
    with pytest.raises(FileNotFoundError):
        op.from_data("nonexistent.yml")


def test_env_resolved(monkeypatch):
    monkeypatch.setenv("MACRO_VAL", "from_env")
    api = MagicMock()
    api.usermacro.get.return_value = []

    op = _executor(api)
    op.from_data({"name": "FOO", "value": "from_env"})
    op.execute()
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$FOO}", value="from_env", type=0
    )