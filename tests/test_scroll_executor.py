from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.ScrollExecutor import ScrollExecutor
from zbxtemplar.executor.operations.SuperAdminOperation import SuperAdminOperation
from zbxtemplar.executor.exceptions import ExecutorParseError


# --- SuperAdminOperation ---

def _run_super_admin(api, data):
    op = SuperAdminOperation(api)
    op.from_data(data)
    op.execute()


def test_set_super_admin_string():
    api = MagicMock()
    _run_super_admin(api, "newpass123")
    api.user.update.assert_called_once_with(userid="1", passwd="newpass123")


def test_set_super_admin_dict():
    api = MagicMock()
    _run_super_admin(api, {"password": "newpass123"})
    api.user.update.assert_called_once_with(userid="1", passwd="newpass123")


def test_set_super_admin_env_resolved(monkeypatch):
    monkeypatch.setenv("ADMIN_PW", "from_env")
    api = MagicMock()
    _run_super_admin(api, {"password": "${ADMIN_PW}"})
    api.user.update.assert_called_once_with(userid="1", passwd="from_env")


def test_set_super_admin_missing_env():
    api = MagicMock()
    with pytest.raises(ValueError, match="UNDEFINED_VAR"):
        _run_super_admin(api, {"password": "${UNDEFINED_VAR}"})
    api.user.update.assert_not_called()


# --- run_scroll error handling ---

def test_yaml_parse_error_wrapped(tmp_path):
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("invalid: [yaml\n", encoding="utf-8")
    api = MagicMock()

    with pytest.raises(ExecutorParseError, match="Failed to parse") as exc:
        ScrollExecutor(api).from_file(str(bad_yaml))

    assert exc.value.path == str(bad_yaml)