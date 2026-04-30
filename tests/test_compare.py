from copy import deepcopy

import pytest

from zbxtemplar.decree.UserGroup import GuiAccess, Permission, PermissionGroup, UsersStatus
from zbxtemplar.inquest import Diff, RawDiff, SchemaDiff, render
from zbxtemplar.modules import APIContext, Context

from tests.paths import FIXTURES_DIR


HEADER = "Checking declared state against zabbix.test (raw)"
LEGEND = (
    "  Legend:  OK=match  DIFF=fields differ  MISS=not found on remote   |"
    "  + key=only on remote  - key=only on local  ~ key=value differs"
)
FIXTURES = (
    "sample_user_group.yml", "sample_set_user.yml",
    "sample_encryption_decree.yml", "sample_saml_config.yml",
)


def _full():
    ctx = Context()
    for f in FIXTURES:
        ctx.load(str(FIXTURES_DIR / f))
    return ctx


def _mirror(ctx):
    r = APIContext(api=None)
    r._user_groups = deepcopy(ctx._user_groups)
    r._users = deepcopy(ctx._users)
    r._saml = deepcopy(ctx._saml)
    r._host_encryptions = deepcopy(ctx._host_encryptions)
    return r


def _render(diffs, comparator="raw"):
    return render(diffs, target="zabbix.test", comparator=comparator, color=False)


@pytest.fixture
def show(capsys):
    def _show(text):
        with capsys.disabled():
            print("\n" + text)
    return _show


def test_equal(show):
    local = _full()
    diffs = RawDiff().compare(local, _mirror(local))
    text = _render(diffs)
    show(text)
    assert diffs == []
    assert text == "\n".join(["", HEADER, "  no diffs", ""])


def test_local_full_remote_empty(show):
    local = _full()
    diffs = RawDiff().compare(local, APIContext(api=None))
    text = _render(diffs)
    show(text)
    assert diffs == [
        Diff("user_group", ["Templar Disabled", "Templar Users"], None),
        Diff("user", ["zbx-admin", "zbx-service"], None),
        Diff("encryption", ["Templar Host"], None),
        Diff("saml", local._saml, None),
    ]
    assert text == "\n".join([
        "", HEADER, "  4 diffs across 4 entities", "",
        "  MISS   user_group        Templar Disabled",
        "  MISS   user_group        Templar Users",
        "  MISS   user              zbx-admin",
        "  MISS   user              zbx-service",
        "  MISS   encryption        Templar Host",
        "  MISS   saml            ",
        "",
        LEGEND, "",
    ])


def test_local_empty_remote_full(show):
    diffs = RawDiff().compare(Context(), _mirror(_full()))
    text = _render(diffs)
    show(text)
    assert diffs == []
    assert text == "\n".join(["", HEADER, "  no diffs", ""])


def test_entity_compare(show):
    local = Context()
    local.load(str(FIXTURES_DIR / "sample_user_group.yml"))
    remote = _mirror(local)
    target = remote._user_groups["Templar Users"]
    target.gui_access = GuiAccess.DEFAULT
    target.users_status = UsersStatus.ENABLED
    target.host_groups = [pg for pg in target.host_groups if pg.name != "Templar Hosts"]
    target.host_groups.append(PermissionGroup("Cloud servers", Permission.READ))
    next(pg for pg in target.host_groups if pg.name == "Linux servers").permission = Permission.READ

    raw = RawDiff().compare(local, remote)
    schema = SchemaDiff().compare(local, remote)
    raw_text = _render(raw)
    schema_text = _render(schema, comparator="schema")
    show(raw_text)
    show(schema_text)
    assert raw == [
        Diff("user_group.Templar Users.gui_access",
             GuiAccess.INTERNAL, GuiAccess.DEFAULT),
        Diff("user_group.Templar Users.users_status",
             None, UsersStatus.ENABLED),
        Diff("user_group.Templar Users.host_groups", ["Templar Hosts"], None),
        Diff("user_group.Templar Users.host_groups", None, ["Cloud servers"]),
        Diff("user_group.Templar Users.host_groups[Linux servers].permission",
             Permission.NONE, Permission.READ),
    ]
    assert schema == [
        Diff("user_group.Templar Users.gui_access",
             GuiAccess.INTERNAL, GuiAccess.DEFAULT),
        Diff("user_group.Templar Users.host_groups", ["Templar Hosts"], None),
        Diff("user_group.Templar Users.host_groups", None, ["Cloud servers"]),
        Diff("user_group.Templar Users.host_groups[Linux servers].permission",
             Permission.NONE, Permission.READ),
    ]
    assert raw_text == "\n".join([
        "", HEADER, "  5 diffs across 1 entity", "",
        "  DIFF   user_group        Templar Users",
        "      ~ gui_access:",
        '        local:  "INTERNAL"',
        '        remote: "DEFAULT"',
        "      ~ users_status:",
        '        local:  null',
        '        remote: "ENABLED"',
        '      - host_groups: ["Templar Hosts"]',
        '      + host_groups: ["Cloud servers"]',
        "      ~ host_groups[Linux servers].permission:",
        '        local:  "NONE"',
        '        remote: "READ"',
        "",
        LEGEND, "",
    ])
    assert schema_text == "\n".join([
        "", "Checking declared state against zabbix.test (schema)",
        "  4 diffs across 1 entity", "",
        "  DIFF   user_group        Templar Users",
        "      ~ gui_access:",
        '        local:  "INTERNAL"',
        '        remote: "DEFAULT"',
        '      - host_groups: ["Templar Hosts"]',
        '      + host_groups: ["Cloud servers"]',
        "      ~ host_groups[Linux servers].permission:",
        '        local:  "NONE"',
        '        remote: "READ"',
        "",
        LEGEND, "",
    ])


def test_list_added_and_removed(show):
    local = Context()
    local.load(str(FIXTURES_DIR / "sample_user_group.yml"))
    remote = _mirror(local)
    local._user_groups["Templar Users"].template_groups = []
    remote._user_groups["Templar Users"].host_groups = []

    raw = RawDiff().compare(local, remote)
    schema = SchemaDiff().compare(local, remote)
    text = _render(raw)
    show(text)
    expected = [
        Diff("user_group.Templar Users.host_groups",
             ["Linux servers", "Templar Hosts", "Virtual machines"], None),
        Diff("user_group.Templar Users.template_groups",
             None, ["Templar Templates"]),
    ]
    assert raw == expected
    assert schema == expected
    assert text == "\n".join([
        "", HEADER, "  2 diffs across 1 entity", "",
        "  DIFF   user_group        Templar Users",
        '      - host_groups: ["Linux servers", "Templar Hosts", "Virtual machines"]',
        '      + template_groups: ["Templar Templates"]',
        "",
        LEGEND, "",
    ])


def test_saml_partial(show):
    local = Context()
    local.load(str(FIXTURES_DIR / "sample_saml_config.yml"))
    remote = _mirror(local)
    remote._saml.username_attribute = "mail"

    raw = RawDiff().compare(local, remote)
    schema = SchemaDiff().compare(local, remote)
    text = _render(raw)
    show(text)
    expected = [Diff("saml.username_attribute", "usrEmail", "mail")]
    assert raw == expected
    assert schema == expected
    assert text == "\n".join([
        "", HEADER, "  1 diff across 1 entity", "",
        "  DIFF   saml            ",
        "      ~ username_attribute:",
        '        local:  "usrEmail"',
        '        remote: "mail"',
        "",
        LEGEND, "",
    ])


def test_ignore_policy(show):
    local = Context()
    local.load(str(FIXTURES_DIR / "sample_set_user.yml"))
    remote = _mirror(local)
    remote._users["zbx-service"].token.store_at = "/tmp/different.token"

    raw = RawDiff().compare(local, remote)
    schema = SchemaDiff().compare(local, remote)
    show(_render(raw))
    assert raw == [
        Diff("user.zbx-service.token.store_at",
             ".secrets/monitoring-ro.token", "/tmp/different.token"),
    ]
    assert schema == []