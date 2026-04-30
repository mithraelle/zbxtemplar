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


def test_action_filter_equal_all_shapes():
    from zbxtemplar.decree.Action import AutoregistrationAction
    from zbxtemplar.decree.action_conditions import (
        ConditionList, EvalType, HostGroupCondition, HostTemplateCondition,
    )
    from zbxtemplar.inquest.ActionComparator import ActionComparator

    pairs = [
        (AutoregistrationAction("a"), AutoregistrationAction("a")),
    ]

    a = AutoregistrationAction("a")
    a.set_conditions(ConditionList(EvalType.AND).add(HostGroupCondition("g")))
    b = AutoregistrationAction("a")
    b.set_conditions(ConditionList(EvalType.AND).add(HostGroupCondition("g")))
    pairs.append((a, b))

    a = AutoregistrationAction("a")
    a.set_conditions(HostGroupCondition("g") | HostTemplateCondition("t"))
    b = AutoregistrationAction("a")
    b.set_conditions(HostGroupCondition("g") | HostTemplateCondition("t"))
    pairs.append((a, b))

    for local, remote in pairs:
        assert ActionComparator.compare(RawDiff(), local, remote, "act") == []


def test_action_filter_set_or_unset(show):
    from zbxtemplar.decree.Action import AutoregistrationAction
    from zbxtemplar.decree.action_conditions import HostGroupCondition
    from zbxtemplar.inquest.ActionComparator import ActionComparator

    has_filter = AutoregistrationAction("a")
    has_filter.set_conditions(HostGroupCondition("g"))
    bare = AutoregistrationAction("a")

    diffs = ActionComparator.compare(RawDiff(), has_filter, bare, "action.a")
    assert diffs == [Diff("action.a.filter", "ConditionExpression", None)]
    text = _render(diffs)
    show(text)
    assert text == "\n".join([
        "", HEADER, "  1 diff across 1 entity", "",
        "  DIFF   action            a",
        "      ~ filter:",
        '        local:  "ConditionExpression"',
        "        remote: null",
        "",
        LEGEND, "",
    ])

    diffs = ActionComparator.compare(RawDiff(), bare, has_filter, "action.a")
    assert diffs == [Diff("action.a.filter", None, "ConditionExpression")]


def test_action_filter_shape_mismatch(show):
    from zbxtemplar.decree.Action import AutoregistrationAction
    from zbxtemplar.decree.action_conditions import (
        ConditionList, EvalType, HostGroupCondition,
    )
    from zbxtemplar.inquest.ActionComparator import ActionComparator

    local = AutoregistrationAction("a")
    local.set_conditions(ConditionList(EvalType.AND).add(HostGroupCondition("g")))
    remote = AutoregistrationAction("a")
    remote.set_conditions(HostGroupCondition("g"))

    diffs = ActionComparator.compare(RawDiff(), local, remote, "action.a")
    assert diffs == [Diff("action.a.filter", "ConditionList", "ConditionExpression")]
    text = _render(diffs)
    show(text)
    assert text == "\n".join([
        "", HEADER, "  1 diff across 1 entity", "",
        "  DIFF   action            a",
        "      ~ filter:",
        '        local:  "ConditionList"',
        '        remote: "ConditionExpression"',
        "",
        LEGEND, "",
    ])


def test_action_filter_list_branches(show):
    from zbxtemplar.decree.Action import AutoregistrationAction
    from zbxtemplar.decree.action_conditions import (
        ConditionList, EvalType,
        HostGroupCondition, HostMetadataCondition, HostTemplateCondition,
    )
    from zbxtemplar.inquest.ActionComparator import ActionComparator

    local = AutoregistrationAction("a")
    local.set_conditions(
        ConditionList(EvalType.AND)
        .add(HostGroupCondition("g1"))
        .add(HostGroupCondition("same"))
        .add(HostTemplateCondition("t1"))
        .add(HostGroupCondition("only-local"))
    )
    remote = AutoregistrationAction("a")
    remote.set_conditions(
        ConditionList(EvalType.OR)
        .add(HostGroupCondition("g2"))
        .add(HostGroupCondition("same"))
        .add(HostMetadataCondition("p"))
    )

    diffs = ActionComparator.compare(RawDiff(), local, remote, "action.a")
    assert diffs == [
        Diff("action.a.filter.evaltype", "AND", "OR"),
        Diff("action.a.filter[0].value", "g1", "g2"),
        Diff(
            "action.a.filter[2]",
            "HostTemplateCondition(op=EQUALS, value='t1')",
            "HostMetadataCondition(op=CONTAINS, value='p')",
        ),
        Diff("action.a.filter", ["HostGroupCondition(op=EQUALS, value='only-local')"], None),
    ]
    text = _render(diffs)
    show(text)
    assert text == "\n".join([
        "", HEADER, "  4 diffs across 1 entity", "",
        "  DIFF   action            a",
        "      ~ filter.evaltype:",
        '        local:  "AND"',
        '        remote: "OR"',
        "      ~ filter[0].value:",
        '        local:  "g1"',
        '        remote: "g2"',
        "      ~ filter[2]:",
        '        local:  "HostTemplateCondition(op=EQUALS, value=\'t1\')"',
        '        remote: "HostMetadataCondition(op=CONTAINS, value=\'p\')"',
        '      - filter: ["HostGroupCondition(op=EQUALS, value=\'only-local\')"]',
        "",
        LEGEND, "",
    ])


def test_action_filter_expression_branches(show):
    from zbxtemplar.decree.Action import AutoregistrationAction
    from zbxtemplar.decree.action_conditions import ConditionExpression
    from zbxtemplar.inquest.ActionComparator import ActionComparator

    local = AutoregistrationAction("a")
    local.set_conditions(ConditionExpression.from_dict({
        "evaltype": 3,
        "formula": "A and B",
        "conditions": [
            {"conditiontype": 0,  "operator": 0, "value": "g-local",  "formulaid": "A"},
            {"conditiontype": 13, "operator": 0, "value": "t-shared", "formulaid": "B"},
        ],
    }))
    remote = AutoregistrationAction("a")
    remote.set_conditions(ConditionExpression.from_dict({
        "evaltype": 3,
        "formula": "A or B or C",
        "conditions": [
            {"conditiontype": 0,  "operator": 0, "value": "g-remote", "formulaid": "A"},
            {"conditiontype": 13, "operator": 0, "value": "t-shared", "formulaid": "B"},
            {"conditiontype": 0,  "operator": 0, "value": "extra",    "formulaid": "C"},
        ],
    }))

    diffs = ActionComparator.compare(RawDiff(), local, remote, "action.a")
    assert diffs == [
        Diff("action.a.filter.formula", "A and B", "A or B or C"),
        Diff("action.a.filter", None, ["HostGroupCondition(op=EQUALS, value='extra')"]),
        Diff("action.a.filter[A].value", "g-local", "g-remote"),
    ]
    text = _render(diffs)
    show(text)
    assert text == "\n".join([
        "", HEADER, "  3 diffs across 1 entity", "",
        "  DIFF   action            a",
        "      ~ filter.formula:",
        '        local:  "A and B"',
        '        remote: "A or B or C"',
        '      + filter: ["HostGroupCondition(op=EQUALS, value=\'extra\')"]',
        "      ~ filter[A].value:",
        '        local:  "g-local"',
        '        remote: "g-remote"',
        "",
        LEGEND, "",
    ])


def test_action_op_grouping_pairing_tails(show):
    from zbxtemplar.decree.Action import AutoregistrationAction
    from zbxtemplar.decree.action_operations import SetInventoryModeOperation
    from zbxtemplar.inquest.ActionComparator import ActionComparator

    local = AutoregistrationAction("act")
    local.operations.send_message(users=["alice"], subject="A")
    local.operations.add_host()
    local.operations.add_to_group("g1")
    local.operations.link_template("t1")
    local.operations.set_inventory_mode(SetInventoryModeOperation.MANUAL)
    local.operations.disable_host()

    remote = AutoregistrationAction("act")
    remote.operations.send_message(users=["alice"], subject="A_PRIME")
    remote.operations.add_host()
    remote.operations.add_to_group("g2")
    remote.operations.link_template("t2")
    remote.operations.set_inventory_mode(SetInventoryModeOperation.AUTOMATIC)
    remote.operations.enable_host()

    diffs = ActionComparator.compare(RawDiff(), local, remote, "action.act")
    assert diffs == [
        Diff("action.act.operations[SendMessageOperation][0].subject", "A", "A_PRIME"),
        Diff("action.act.operations[AddToGroupOperation][0].group", "g1", "g2"),
        Diff("action.act.operations[LinkTemplateOperation][0].template", "t1", "t2"),
        Diff("action.act.operations", None, ["EnableHostOperation"]),
        Diff("action.act.operations", ["DisableHostOperation"], None),
        Diff("action.act.operations[SetInventoryModeOperation][0].inventory_mode", 0, 1),
    ]

    text = _render(diffs)
    show(text)
    assert text == "\n".join([
        "", HEADER, "  6 diffs across 1 entity", "",
        "  DIFF   action            act",
        "      ~ operations[SendMessageOperation][0].subject:",
        '        local:  "A"',
        '        remote: "A_PRIME"',
        "      ~ operations[AddToGroupOperation][0].group:",
        '        local:  "g1"',
        '        remote: "g2"',
        "      ~ operations[LinkTemplateOperation][0].template:",
        '        local:  "t1"',
        '        remote: "t2"',
        '      + operations: ["EnableHostOperation"]',
        '      - operations: ["DisableHostOperation"]',
        "      ~ operations[SetInventoryModeOperation][0].inventory_mode:",
        "        local:  0",
        "        remote: 1",
        "",
        LEGEND, "",
    ])