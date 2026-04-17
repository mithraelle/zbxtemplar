import os
from unittest.mock import MagicMock

from zbxtemplar.dicts.Scroll import Scroll
from zbxtemplar.executor.ScrollExecutor import ScrollExecutor
from tests.paths import FIXTURES_DIR

SCROLL = FIXTURES_DIR / "scroll.yml"


def _full_api():
    api = MagicMock()
    # set_super_admin
    api.user.checkAuthentication.return_value = {"userid": "1"}
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


def _load(api, path):
    path = str(path)
    base_dir = os.path.dirname(os.path.abspath(path))
    Scroll._base_dir = base_dir
    Scroll._resolve_envs = True
    try:
        scroll = Scroll.from_file(path)
    finally:
        Scroll._base_dir = None
        Scroll._resolve_envs = False
    return ScrollExecutor(scroll, api, base_dir)


def test_scroll_runs_all_actions(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    _load(api, SCROLL).execute()

    api.user.update.assert_called_once_with(userid="1", passwd="admin123", current_passwd="admin123")
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


def test_scroll_only_action(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    _load(api, SCROLL).execute(only_action="set_super_admin")

    api.user.update.assert_called_once_with(userid="1", passwd="admin123", current_passwd="admin123")
    # other actions should not run
    api.usermacro.createglobal.assert_not_called()
    api.usergroup.create.assert_not_called()
    api.user.create.assert_not_called()


def test_scroll_from_action(monkeypatch):
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    _load(api, SCROLL).execute(from_action="decree")

    # earlier actions should be skipped
    api.user.update.assert_not_called()
    api.usermacro.createglobal.assert_not_called()
    # decree should run (user_group + add_user)
    api.usergroup.create.assert_called_once()
    api.user.create.assert_called_once()


def test_scroll_skips_missing_action(monkeypatch):
    """The scroll has no 'apply' action — runner should skip it silently."""
    monkeypatch.setenv("ZBX_ADMIN_PASSWORD", "admin123")
    api = _full_api()

    _load(api, SCROLL).execute()

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
    scroll_file.write_text("set_macro: macros.yml\n")

    api = MagicMock()
    api.usermacro.get.return_value = []

    # CWD is tmp_path, scroll is in tmp_path/deploy/
    # macros.yml should resolve to tmp_path/deploy/macros.yml
    base_dir = str(subdir)
    Scroll._base_dir = base_dir
    try:
        scroll = Scroll.from_file(str(scroll_file))
    finally:
        Scroll._base_dir = None
    ex = ScrollExecutor(scroll, api, base_dir)
    ex.execute()

    api.usermacro.createglobal.assert_called_once_with(
        macro="{$FROM_FILE}", value="works", type=0
    )
