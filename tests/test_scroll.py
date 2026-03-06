from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from zbxtemplar.executor import Executor

SCROLL = Path(__file__).parent / "test_scroll.yml"


def _full_api():
    api = MagicMock()
    # set_macro
    api.usermacro.get.return_value = []
    # decree
    api.hostgroup.get.return_value = [
        {"groupid": "2", "name": "Linux servers"},
        {"groupid": "3", "name": "Virtual machines"},
    ]
    api.templategroup.get.return_value = [
        {"groupid": "10", "name": "Test Template"},
    ]
    api.usergroup.get.return_value = []
    # add_user
    api.role.get.return_value = [
        {"roleid": "1", "name": "User role"},
    ]
    api.mediatype.get.return_value = []
    api.user.get.side_effect = [
        [],  # existing check
        [{"userid": "20", "username": "api-reader"}],  # after create, for token
    ]
    return api


def test_scroll_runs_all_stages(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    Executor(api).run_scroll(str(SCROLL))

    api.user.update.assert_called_once_with(userid="1", passwd="admin123")
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()
    api.token.create.assert_called_once()


def test_scroll_only_stage(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    Executor(api).run_scroll(str(SCROLL), only_stage="bootstrap")

    api.user.update.assert_called_once_with(userid="1", passwd="admin123")
    api.usermacro.createglobal.assert_called_once()
    # decree and add_user should not run
    api.usergroup.create.assert_not_called()
    api.user.create.assert_not_called()


def test_scroll_from_stage(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    Executor(api).run_scroll(str(SCROLL), from_stage="state")

    # bootstrap should be skipped
    api.user.update.assert_not_called()
    api.usermacro.createglobal.assert_not_called()
    # state and users should run
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()


def test_scroll_skips_missing_stage(monkeypatch):
    """The scroll has no 'templates' stage — runner should skip it silently."""
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    Executor(api).run_scroll(str(SCROLL))

    api.configuration.import_.assert_not_called()