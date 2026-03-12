from zbxtemplar.decree.action_conditions import (
    EvalType,
    ConditionList,
    ConditionExpression,
    HostGroupCondition,
    SeverityCondition,
    TriggerValueCondition,
    EventNameCondition,
    TagCondition,
    TagValueCondition,
    SuppressedCondition,
    HostNameCondition,
)
from zbxtemplar.core.constants import Severity


# --- Condition to_dict ---

def test_host_group_default_op():
    c = HostGroupCondition("Production")
    assert c.to_dict() == {
        "conditiontype": 0,
        "operator": 0,
        "value": "Production",
    }


def test_host_group_not_equals():
    c = HostGroupCondition("Staging", HostGroupCondition.Op.NOT_EQUALS)
    assert c.to_dict() == {
        "conditiontype": 0,
        "operator": 1,
        "value": "Staging",
    }


def test_severity_default_gte():
    c = SeverityCondition(Severity.HIGH)
    assert c.to_dict() == {
        "conditiontype": 4,
        "operator": 5,
        "value": Severity.HIGH,
    }


def test_trigger_value():
    c = TriggerValueCondition(TriggerValueCondition.PROBLEM)
    assert c.to_dict() == {
        "conditiontype": 5,
        "operator": 0,
        "value": "PROBLEM",
    }


def test_suppressed_no_value():
    c = SuppressedCondition()
    d = c.to_dict()
    assert d == {"conditiontype": 16, "operator": 11}
    assert "value" not in d


def test_tag_value_two_values():
    c = TagValueCondition("env", "production")
    assert c.to_dict() == {
        "conditiontype": 26,
        "operator": 0,
        "value": "env",
        "value2": "production",
    }


def test_host_name_matches():
    c = HostNameCondition("^web-.*", HostNameCondition.Op.MATCHES)
    assert c.to_dict() == {
        "conditiontype": 22,
        "operator": 8,
        "value": "^web-.*",
    }


# --- ConditionList ---

def test_condition_list_and_or():
    cl = ConditionList(EvalType.AND_OR)
    cl.add(HostGroupCondition("Production"))
    cl.add(HostGroupCondition("Staging"))
    cl.add(SeverityCondition(Severity.HIGH))

    d = cl.to_dict()
    assert d["evaltype"] == 0
    assert len(d["conditions"]) == 3
    assert d["conditions"][0]["value"] == "Production"
    assert d["conditions"][2]["conditiontype"] == 4


def test_condition_list_or():
    cl = ConditionList(EvalType.OR)
    cl.add(EventNameCondition("disk"))
    cl.add(EventNameCondition("cpu"))

    d = cl.to_dict()
    assert d["evaltype"] == 2
    assert len(d["conditions"]) == 2


# --- Expression tree & ConditionExpression ---

def test_simple_and():
    a = HostGroupCondition("Production")
    b = SeverityCondition(Severity.HIGH)

    expr = ConditionExpression(a & b)
    d = expr.to_dict()

    assert d["evaltype"] == 3
    assert d["formula"] == "A and B"
    assert len(d["conditions"]) == 2
    assert d["conditions"][0]["formulaid"] == "A"
    assert d["conditions"][1]["formulaid"] == "B"


def test_simple_or():
    a = HostGroupCondition("Production")
    b = HostGroupCondition("Staging")

    expr = ConditionExpression(a | b)
    d = expr.to_dict()

    assert d["formula"] == "A or B"


def test_or_and_precedence():
    """(a | b) & c should parenthesize the OR."""
    a = HostGroupCondition("Production")
    b = HostGroupCondition("Staging")
    c = SeverityCondition(Severity.HIGH)

    expr = ConditionExpression((a | b) & c)
    d = expr.to_dict()

    assert d["formula"] == "(A or B) and C"
    assert len(d["conditions"]) == 3


def test_and_or_no_extra_parens():
    """a & b | c — no parentheses needed."""
    a = HostGroupCondition("Production")
    b = SeverityCondition(Severity.HIGH)
    c = TagCondition("scope")

    expr = ConditionExpression(a & b | c)
    d = expr.to_dict()

    assert d["formula"] == "A and B or C"


def test_complex_expression():
    """(a | b) & (c | d)"""
    a = HostGroupCondition("Production")
    b = HostGroupCondition("Staging")
    c = SeverityCondition(Severity.HIGH)
    d = SeverityCondition(Severity.DISASTER)

    expr = ConditionExpression((a | b) & (c | d))
    result = expr.to_dict()

    assert result["formula"] == "(A or B) and (C or D)"
    assert len(result["conditions"]) == 4
    assert [c["formulaid"] for c in result["conditions"]] == ["A", "B", "C", "D"]


# --- Not / invert ---

def test_not_simple():
    a = HostGroupCondition("Production")
    expr = ConditionExpression(~a)
    d = expr.to_dict()

    assert d["formula"] == "not A"
    assert len(d["conditions"]) == 1


def test_not_in_and():
    """(a & ~b) | (~a & b) — XOR pattern, reuses labels."""
    a = HostGroupCondition("Production")
    b = SeverityCondition(Severity.HIGH)

    expr = ConditionExpression((a & ~b) | (~a & b))
    d = expr.to_dict()

    assert d["formula"] == "A and not B or not A and B"
    assert len(d["conditions"]) == 2


def test_not_compound_gets_parens():
    """~(a | b) should produce not (A or B)."""
    a = HostGroupCondition("Production")
    b = HostGroupCondition("Staging")

    expr = ConditionExpression(~(a | b))
    d = expr.to_dict()

    assert d["formula"] == "not (A or B)"


def test_not_preserves_original():
    """~a should not mutate a."""
    a = HostGroupCondition("Production")
    _ = ~a
    assert a.op == HostGroupCondition.Op.EQUALS


# --- __bool__ guard ---

def test_bool_raises():
    import pytest
    a = HostGroupCondition("Production")
    b = SeverityCondition(Severity.HIGH)
    with pytest.raises(TypeError, match="Use &"):
        a and b