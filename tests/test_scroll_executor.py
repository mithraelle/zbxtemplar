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


def _mock_api(userid="1", username="Admin", use_token=False):
    api = MagicMock()
    api._ZabbixAPI__use_token = use_token
    api._ZabbixAPI__session_id = "test-session"
    api.user.checkAuthentication.return_value = {"userid": userid}
    api.user.get.return_value = [{"username": username}]
    return api


def test_set_super_admin_dict():
    api = _mock_api(userid="5", username="Admin")
    _run_super_admin(api, {"password": "newpass123", "current_password": "oldpass"})
    api.user.update.assert_called_once_with(userid="5", passwd="newpass123", current_passwd="oldpass")
    api.login.assert_called_once_with(user="Admin", password="newpass123")


def test_set_super_admin_username_only():
    api = _mock_api()
    _run_super_admin(api, {"username": "SuperAdmin"})
    api.user.update.assert_called_once_with(userid="1", username="SuperAdmin")
    api.login.assert_not_called()


def test_set_super_admin_password_without_current():
    api = MagicMock()
    with pytest.raises(ValueError, match="current_password"):
        _run_super_admin(api, {"password": "newpass123"})
    api.user.update.assert_not_called()


def test_set_super_admin_no_relogin_with_token():
    api = _mock_api(use_token=True)
    _run_super_admin(api, {"password": "newpass123", "current_password": "oldpass"})
    api.user.update.assert_called_once()
    api.login.assert_not_called()


def test_set_super_admin_env_resolved(monkeypatch):
    monkeypatch.setenv("ADMIN_PW", "from_env")
    api = _mock_api()
    _run_super_admin(api, {"password": "${ADMIN_PW}", "current_password": "${ADMIN_PW}"})
    api.user.update.assert_called_once_with(userid="1", passwd="from_env", current_passwd="from_env")


def test_set_super_admin_missing_env():
    api = MagicMock()
    with pytest.raises(ValueError, match="UNDEFINED_VAR"):
        _run_super_admin(api, {"password": "${UNDEFINED_VAR}", "current_password": "x"})
    api.user.update.assert_not_called()


# --- run_scroll error handling ---

def test_yaml_parse_error_wrapped(tmp_path):
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("invalid: [yaml\n", encoding="utf-8")
    api = MagicMock()

    with pytest.raises(ExecutorParseError, match="Failed to parse") as exc:
        ScrollExecutor(api).from_file(str(bad_yaml))

    assert exc.value.path == str(bad_yaml)