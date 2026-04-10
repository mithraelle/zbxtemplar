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


# --- run_scroll error handling ---

def test_yaml_parse_error_wrapped(tmp_path):
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("invalid: [yaml\n", encoding="utf-8")
    api = MagicMock()

    with pytest.raises(ExecutorParseError, match="Failed to parse") as exc:
        ScrollExecutor(api).run_scroll(str(bad_yaml))

    assert exc.value.path == str(bad_yaml)