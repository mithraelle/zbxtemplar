from unittest.mock import MagicMock, call, patch

import pytest

from zbxtemplar.executor.ScrollExecutor import ScrollExecutor
from tests.paths import FIXTURES_DIR

SCROLL = FIXTURES_DIR / "scroll.yml"


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
    api.user.get.return_value = []
    api.user.create.return_value = {"userids": ["20"]}
    api.token.get.return_value = []
    api.token.create.return_value = {"tokenids": ["55"]}
    api.token.generate.return_value = {"token": "generated-secret"}
    return api


def test_scroll_runs_all_stages(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    ScrollExecutor(api).run_scroll(str(SCROLL))

    api.user.update.assert_called_once_with(userid="1", passwd="admin123")
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()
    api.token.create.assert_called_once_with(
        name="api-reader-token",
        userid="20",
        expires_at=0,
    )
    api.token.generate.assert_called_once_with(tokenid="55")


def test_scroll_only_stage(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    ScrollExecutor(api).run_scroll(str(SCROLL), only_stage="bootstrap")

    api.user.update.assert_called_once_with(userid="1", passwd="admin123")
    api.usermacro.createglobal.assert_called_once()
    # decree and add_user should not run
    api.usergroup.create.assert_not_called()
    api.user.create.assert_not_called()


def test_scroll_from_stage(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    ScrollExecutor(api).run_scroll(str(SCROLL), from_stage="state")

    # bootstrap should be skipped
    api.user.update.assert_not_called()
    api.usermacro.createglobal.assert_not_called()
    # state should run (user_group + add_user)
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()


def test_scroll_skips_missing_stage(monkeypatch):
    """The scroll has no 'templates' stage — runner should skip it silently."""
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    ScrollExecutor(api).run_scroll(str(SCROLL))

    api.configuration.import_.assert_not_called()


def test_scroll_resolves_file_paths_relative_to_scroll_dir(tmp_path, monkeypatch):
    """File paths in scroll actions resolve relative to the scroll file, not CWD."""
    monkeypatch.chdir(tmp_path)

    subdir = tmp_path / "deploy"
    subdir.mkdir()

    macro_file = subdir / "macros.yml"
    macro_file.write_text(
        "set_macro:\n"
        "  - name: FROM_FILE\n"
        "    value: works\n"
    )

    scroll_file = subdir / "scroll.yml"
    scroll_file.write_text(
        "stages:\n"
        "  - stage: bootstrap\n"
        "    set_macro: macros.yml\n"
    )

    api = MagicMock()
    api.usermacro.get.return_value = []

    # CWD is tmp_path, scroll is in tmp_path/deploy/
    # macros.yml should resolve to tmp_path/deploy/macros.yml
    ScrollExecutor(api).run_scroll(str(scroll_file))

    api.usermacro.createglobal.assert_called_once_with(
        macro="{$FROM_FILE}", value="works", type=0
    )
