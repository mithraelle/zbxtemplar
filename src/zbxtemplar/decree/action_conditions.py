from enum import IntEnum


# --- Eval types ---

class EvalType(IntEnum):
    AND_OR = 0
    AND = 1
    OR = 2


# --- Operator sets ---

class _EqualsOp(IntEnum):
    EQUALS = 0
    NOT_EQUALS = 1


class _ContainsOp(IntEnum):
    CONTAINS = 2
    NOT_CONTAINS = 3


class _PatternOp(IntEnum):
    CONTAINS = 2
    NOT_CONTAINS = 3
    MATCHES = 8
    NOT_MATCHES = 9


class _SeverityOp(IntEnum):
    EQUALS = 0
    NOT_EQUALS = 1
    GREATER_OR_EQUAL = 5
    LESS_OR_EQUAL = 6


class _EqualsOnlyOp(IntEnum):
    EQUALS = 0


class _InOp(IntEnum):
    IN = 4
    NOT_IN = 7


class _CompareOp(IntEnum):
    GREATER_OR_EQUAL = 5
    LESS_OR_EQUAL = 6


class _FullOp(IntEnum):
    EQUALS = 0
    NOT_EQUALS = 1
    CONTAINS = 2
    NOT_CONTAINS = 3
    GREATER_OR_EQUAL = 5
    LESS_OR_EQUAL = 6


class _TagOp(IntEnum):
    EQUALS = 0
    NOT_EQUALS = 1
    CONTAINS = 2
    NOT_CONTAINS = 3


class _SuppressedOp(IntEnum):
    YES = 10
    NO = 11


# --- Expression tree ---

class ConditionExpr:
    def __and__(self, other):
        return AndExpr(self, other)

    def __or__(self, other):
        return OrExpr(self, other)

    def __invert__(self):
        return NotExpr(self)

    def __bool__(self):
        raise TypeError(
            "Use & instead of 'and', | instead of 'or', ~ instead of 'not'"
        )


class AndExpr(ConditionExpr):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class OrExpr(ConditionExpr):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class NotExpr(ConditionExpr):
    def __init__(self, inner):
        self.inner = inner


# --- Condition base ---

class Condition(ConditionExpr):
    conditiontype = None

    def to_dict(self):
        return {
            "conditiontype": self.conditiontype,
            "operator": int(self.op),
            "value": self.value,
        }


# --- Condition types (conditiontype 0..28) ---

class HostGroupCondition(Condition):
    """Host group — conditiontype 0."""
    conditiontype = 0
    Op = _EqualsOp

    def __init__(self, group, op=_EqualsOp.EQUALS):
        self.value = group
        self.op = op


class HostCondition(Condition):
    """Host — conditiontype 1."""
    conditiontype = 1
    Op = _EqualsOp

    def __init__(self, host, op=_EqualsOp.EQUALS):
        self.value = host
        self.op = op


class TriggerCondition(Condition):
    """Trigger — conditiontype 2."""
    conditiontype = 2
    Op = _EqualsOp

    def __init__(self, trigger, op=_EqualsOp.EQUALS):
        self.value = trigger
        self.op = op


class EventNameCondition(Condition):
    """Event name — conditiontype 3."""
    conditiontype = 3
    Op = _ContainsOp

    def __init__(self, pattern, op=_ContainsOp.CONTAINS):
        self.value = pattern
        self.op = op


class SeverityCondition(Condition):
    """Trigger severity — conditiontype 4."""
    conditiontype = 4
    Op = _SeverityOp

    def __init__(self, severity, op=_SeverityOp.GREATER_OR_EQUAL):
        self.value = severity
        self.op = op


class TriggerValueCondition(Condition):
    """Trigger value — conditiontype 5."""
    conditiontype = 5
    Op = _EqualsOnlyOp

    OK = "OK"
    PROBLEM = "PROBLEM"

    def __init__(self, value=PROBLEM, op=_EqualsOnlyOp.EQUALS):
        self.value = value
        self.op = op


class TimePeriodCondition(Condition):
    """Time period — conditiontype 6."""
    conditiontype = 6
    Op = _InOp

    def __init__(self, period, op=_InOp.IN):
        self.value = period
        self.op = op


class HostIPCondition(Condition):
    """Host IP — conditiontype 7."""
    conditiontype = 7
    Op = _EqualsOp

    def __init__(self, ip_range, op=_EqualsOp.EQUALS):
        self.value = ip_range
        self.op = op


class DiscoveredServiceTypeCondition(Condition):
    """Discovered service type — conditiontype 8."""
    conditiontype = 8
    Op = _EqualsOp

    def __init__(self, service_type, op=_EqualsOp.EQUALS):
        self.value = service_type
        self.op = op


class DiscoveredServicePortCondition(Condition):
    """Discovered service port — conditiontype 9."""
    conditiontype = 9
    Op = _EqualsOp

    def __init__(self, port_range, op=_EqualsOp.EQUALS):
        self.value = port_range
        self.op = op


class DiscoveryStatusCondition(Condition):
    """Discovery status — conditiontype 10."""
    conditiontype = 10
    Op = _EqualsOnlyOp

    UP = "UP"
    DOWN = "DOWN"
    DISCOVERED = "DISCOVERED"
    LOST = "LOST"

    def __init__(self, value, op=_EqualsOnlyOp.EQUALS):
        self.value = value
        self.op = op


class UptimeCondition(Condition):
    """Uptime or downtime duration — conditiontype 11."""
    conditiontype = 11
    Op = _CompareOp

    def __init__(self, seconds, op=_CompareOp.GREATER_OR_EQUAL):
        self.value = seconds
        self.op = op


class ReceivedValueCondition(Condition):
    """Received values — conditiontype 12."""
    conditiontype = 12
    Op = _FullOp

    def __init__(self, value, op=_FullOp.EQUALS):
        self.value = value
        self.op = op


class HostTemplateCondition(Condition):
    """Host template — conditiontype 13."""
    conditiontype = 13
    Op = _EqualsOp

    def __init__(self, template, op=_EqualsOp.EQUALS):
        self.value = template
        self.op = op


class SuppressedCondition(Condition):
    """Problem is suppressed — conditiontype 16."""
    conditiontype = 16
    Op = _SuppressedOp

    def __init__(self, op=_SuppressedOp.NO):
        self.value = ""
        self.op = op

    def to_dict(self):
        return {
            "conditiontype": self.conditiontype,
            "operator": int(self.op),
        }


class DiscoveryRuleCondition(Condition):
    """Discovery rule — conditiontype 18."""
    conditiontype = 18
    Op = _EqualsOp

    def __init__(self, rule, op=_EqualsOp.EQUALS):
        self.value = rule
        self.op = op


class DiscoveryCheckCondition(Condition):
    """Discovery check — conditiontype 19."""
    conditiontype = 19
    Op = _EqualsOp

    def __init__(self, check, op=_EqualsOp.EQUALS):
        self.value = check
        self.op = op


class ProxyCondition(Condition):
    """Proxy — conditiontype 20."""
    conditiontype = 20
    Op = _EqualsOp

    def __init__(self, proxy, op=_EqualsOp.EQUALS):
        self.value = proxy
        self.op = op


class DiscoveryObjectCondition(Condition):
    """Discovery object — conditiontype 21."""
    conditiontype = 21
    Op = _EqualsOnlyOp

    HOST = "HOST"
    SERVICE = "SERVICE"

    def __init__(self, value, op=_EqualsOnlyOp.EQUALS):
        self.value = value
        self.op = op


class HostNameCondition(Condition):
    """Host name — conditiontype 22."""
    conditiontype = 22
    Op = _PatternOp

    def __init__(self, pattern, op=_PatternOp.CONTAINS):
        self.value = pattern
        self.op = op


class EventTypeCondition(Condition):
    """Event type — conditiontype 23."""
    conditiontype = 23
    Op = _EqualsOnlyOp

    ITEM_NOT_SUPPORTED = "ITEM_NOT_SUPPORTED"
    ITEM_NORMAL = "ITEM_NORMAL"
    LLD_NOT_SUPPORTED = "LLD_NOT_SUPPORTED"
    LLD_NORMAL = "LLD_NORMAL"
    TRIGGER_UNKNOWN = "TRIGGER_UNKNOWN"
    TRIGGER_NORMAL = "TRIGGER_NORMAL"

    def __init__(self, value, op=_EqualsOnlyOp.EQUALS):
        self.value = value
        self.op = op


class HostMetadataCondition(Condition):
    """Host metadata — conditiontype 24."""
    conditiontype = 24
    Op = _PatternOp

    def __init__(self, pattern, op=_PatternOp.CONTAINS):
        self.value = pattern
        self.op = op


class TagCondition(Condition):
    """Tag — conditiontype 25."""
    conditiontype = 25
    Op = _TagOp

    def __init__(self, tag, op=_TagOp.EQUALS):
        self.value = tag
        self.op = op


class TagValueCondition(Condition):
    """Tag value — conditiontype 26."""
    conditiontype = 26
    Op = _TagOp

    def __init__(self, tag, tag_value, op=_TagOp.EQUALS):
        self.value = tag
        self.value2 = tag_value
        self.op = op

    def to_dict(self):
        return {
            "conditiontype": self.conditiontype,
            "operator": int(self.op),
            "value": self.value,
            "value2": self.value2,
        }


class ServiceCondition(Condition):
    """Service — conditiontype 27."""
    conditiontype = 27
    Op = _EqualsOp

    def __init__(self, service, op=_EqualsOp.EQUALS):
        self.value = service
        self.op = op


class ServiceNameCondition(Condition):
    """Service name — conditiontype 28."""
    conditiontype = 28
    Op = _EqualsOp

    def __init__(self, name, op=_EqualsOp.EQUALS):
        self.value = name
        self.op = op


# --- Filters ---

class ConditionList:
    """Flat condition list with evaltype 0 (AND/OR), 1 (AND), or 2 (OR)."""

    def __init__(self, eval_type=EvalType.AND_OR):
        self.eval_type = eval_type
        self.conditions = []

    def add(self, condition):
        self.conditions.append(condition)
        return self

    def to_dict(self):
        return {
            "evaltype": int(self.eval_type),
            "conditions": [c.to_dict() for c in self.conditions],
        }


class ConditionExpression:
    """Custom expression filter — evaltype 3 with formula string."""

    def __init__(self, expr):
        self.expr = expr

    def _walk(self, node, conditions, seen, parent_type=None):
        if isinstance(node, Condition):
            if id(node) in seen:
                return seen[id(node)]
            label = chr(ord('A') + len(conditions))
            seen[id(node)] = label
            d = node.to_dict()
            d["formulaid"] = label
            conditions.append(d)
            return label
        if isinstance(node, NotExpr):
            inner = self._walk(node.inner, conditions, seen, NotExpr)
            if not isinstance(node.inner, Condition):
                inner = f"({inner})"
            return f"not {inner}"
        if isinstance(node, AndExpr):
            left = self._walk(node.left, conditions, seen, AndExpr)
            right = self._walk(node.right, conditions, seen, AndExpr)
            result = f"{left} and {right}"
        elif isinstance(node, OrExpr):
            left = self._walk(node.left, conditions, seen, OrExpr)
            right = self._walk(node.right, conditions, seen, OrExpr)
            result = f"{left} or {right}"
        if parent_type is AndExpr and isinstance(node, OrExpr):
            return f"({result})"
        return result

    def to_dict(self):
        conditions = []
        formula = self._walk(self.expr, conditions, {})
        return {
            "evaltype": 3,
            "formula": formula,
            "conditions": conditions,
        }