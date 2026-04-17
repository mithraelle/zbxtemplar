from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.operations.SuperAdminOperation import SuperAdminOperation
from zbxtemplar.dicts.Scroll import SuperAdmin


def _run_super_admin(api, data):
    spec = SuperAdmin.from_dict(data)
    op = SuperAdminOperation(spec, api)
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
