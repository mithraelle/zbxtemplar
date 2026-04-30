from collections import defaultdict
from enum import Enum

from zbxtemplar.decree.Action import Action, AutoregistrationAction, TriggerAction
from zbxtemplar.decree.action_conditions import (
    Condition, ConditionExpression, ConditionList, NotExpr,
)
from zbxtemplar.dicts.Schema import SchemaField
from zbxtemplar.inquest.Inquest import Diff


_TRIGGER_FIELDS = (
    "name", "status", "esc_period",
    "pause_symptoms", "pause_suppressed", "notify_if_canceled",
)
_AUTOREG_FIELDS = ("name", "status")

_OP_ATTRS = {
    TriggerAction:          ("operations", "recovery_operations", "update_operations"),
    AutoregistrationAction: ("operations",),
}

_CONDITION_FIELDS = ("op", "value", "value2")


class ActionComparator:
    @staticmethod
    def compare(parent, local: Action, remote: Action, path: str) -> list[Diff]:
        if type(local) is not type(remote):
            return [Diff(path, type(local).__name__, type(remote).__name__)]

        diffs = []
        fields = _TRIGGER_FIELDS if isinstance(local, TriggerAction) else _AUTOREG_FIELDS
        for name in fields:
            lv, rv = getattr(local, name), getattr(remote, name)
            if parent._should_compare(lv, rv, SchemaField(key=name)) and lv != rv:
                diffs.append(Diff(f"{path}.{name}", lv, rv))

        diffs += _compare_filter(local._filter, remote._filter, f"{path}.filter")

        for attr in _OP_ATTRS[type(local)]:
            diffs += _compare_ops(
                parent,
                getattr(local, attr)._ops,
                getattr(remote, attr)._ops,
                f"{path}.{attr}",
            )
        return diffs


def _compare_filter(local, remote, path) -> list[Diff]:
    if local is None and remote is None:
        return []
    if local is None:
        return [Diff(path, None, type(remote).__name__)]
    if remote is None:
        return [Diff(path, type(local).__name__, None)]
    if type(local) is not type(remote):
        return [Diff(path, type(local).__name__, type(remote).__name__)]
    if isinstance(local, ConditionList):
        return _compare_condition_list(local, remote, path)
    return _compare_condition_expression(local, remote, path)


def _compare_condition_list(local: ConditionList, remote: ConditionList, path) -> list[Diff]:
    diffs = []
    if local.eval_type != remote.eval_type:
        diffs.append(Diff(f"{path}.evaltype", local.eval_type.name, remote.eval_type.name))
    diffs += _pair_conditions(local.conditions, remote.conditions, path, lambda i: f"[{i}]")
    return diffs


def _compare_condition_expression(local: ConditionExpression, remote: ConditionExpression, path) -> list[Diff]:
    diffs = []
    l_formula, l_pairs = _expr_pairs(local)
    r_formula, r_pairs = _expr_pairs(remote)
    if l_formula != r_formula:
        diffs.append(Diff(f"{path}.formula", l_formula, r_formula))

    l_by = dict(l_pairs)
    r_by = dict(r_pairs)
    only_local = sorted(l_by.keys() - r_by.keys())
    only_remote = sorted(r_by.keys() - l_by.keys())
    if only_local:
        diffs.append(Diff(path, [_condition_summary(l_by[k]) for k in only_local], None))
    if only_remote:
        diffs.append(Diff(path, None, [_condition_summary(r_by[k]) for k in only_remote]))

    for label in sorted(l_by.keys() & r_by.keys()):
        l, r = l_by[label], r_by[label]
        slot = f"{path}[{label}]"
        if type(l) is not type(r):
            diffs.append(Diff(slot, _condition_summary(l), _condition_summary(r)))
        else:
            diffs += _compare_condition(l, r, slot)
    return diffs


def _pair_conditions(local, remote, path, slot_label) -> list[Diff]:
    diffs = []
    paired = min(len(local), len(remote))
    for i in range(paired):
        l, r = local[i], remote[i]
        slot = f"{path}{slot_label(i)}"
        if type(l) is not type(r):
            diffs.append(Diff(slot, _condition_summary(l), _condition_summary(r)))
        else:
            diffs += _compare_condition(l, r, slot)
    if local[paired:]:
        diffs.append(Diff(path, [_condition_summary(c) for c in local[paired:]], None))
    if remote[paired:]:
        diffs.append(Diff(path, None, [_condition_summary(c) for c in remote[paired:]]))
    return diffs


def _compare_condition(local: Condition, remote: Condition, path) -> list[Diff]:
    diffs = []
    for k in _CONDITION_FIELDS:
        lv = getattr(local, k, None)
        rv = getattr(remote, k, None)
        if lv != rv:
            diffs.append(Diff(f"{path}.{k}", lv, rv))
    return diffs


def _expr_pairs(expr: ConditionExpression):
    if hasattr(expr, "_raw_conditions"):
        return expr._raw_formula, [(c.formulaid, c) for c in expr._raw_conditions]
    pairs = []
    seen = {}

    def visit(node):
        if isinstance(node, Condition):
            if id(node) in seen:
                return
            label = chr(ord('A') + len(pairs))
            seen[id(node)] = label
            pairs.append((label, node))
        elif isinstance(node, NotExpr):
            visit(node.inner)
        else:
            visit(node.left)
            visit(node.right)

    visit(expr.expr)
    return expr.to_dict()["formula"], pairs


def _condition_summary(c: Condition) -> str:
    parts = []
    for k in _CONDITION_FIELDS:
        v = getattr(c, k, None)
        if v in (None, ""):
            continue
        rendered = v.name if isinstance(v, Enum) else repr(v)
        parts.append(f"{k}={rendered}")
    name = type(c).__name__
    return f"{name}({', '.join(parts)})" if parts else name


def _compare_ops(parent, local_ops, remote_ops, path) -> list[Diff]:
    l_by, r_by = defaultdict(list), defaultdict(list)
    for op in local_ops:
        l_by[op.operationtype].append(op)
    for op in remote_ops:
        r_by[op.operationtype].append(op)

    diffs = []
    for ot in sorted(set(l_by) | set(r_by)):
        ls, rs = l_by[ot], r_by[ot]
        paired = min(len(ls), len(rs))
        for i in range(paired):
            label = type(ls[i]).__name__
            diffs += parent._compare_entity(ls[i], rs[i], f"{path}[{label}][{i}]")
        if ls[paired:]:
            diffs.append(Diff(path, [_op_summary(op) for op in ls[paired:]], None))
        if rs[paired:]:
            diffs.append(Diff(path, None, [_op_summary(op) for op in rs[paired:]]))
    return diffs


def _op_summary(op) -> str:
    parts = [
        f"{k}={v!r}"
        for k, v in vars(op).items()
        if not k.startswith("_") and v not in (None, [], {})
    ]
    name = type(op).__name__
    return f"{name}({', '.join(parts)})" if parts else name