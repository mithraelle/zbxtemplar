from __future__ import annotations

from abc import ABC, abstractmethod


def _render_arg(a) -> str:
    from zbxtemplar.zabbix.Item import Item
    if isinstance(a, Item):
        return f"/{a._host}/{a.key}"
    return str(a)


class TriggerExpr(ABC):
    @abstractmethod
    def __str__(self) -> str: ...

    def items(self) -> list:
        """Distinct ``Item`` leaves referenced in the tree, in first-seen order.

        Deduplicated by object identity.
        """
        from zbxtemplar.zabbix.Item import Item
        seen: dict[int, Item] = {}

        def walk(node):
            if isinstance(node, Item):
                seen.setdefault(id(node), node)
            elif isinstance(node, BinOp):
                walk(node._left)
                walk(node._right)
            elif isinstance(node, UnaryOp):
                walk(node._operand)
            elif isinstance(node, TriggerFunction):
                for a in node._args:
                    walk(a)

        walk(self)
        return list(seen.values())

    def __add__(self, other): return BinOp("+", self, other)
    def __radd__(self, other): return BinOp("+", other, self)
    def __sub__(self, other): return BinOp("-", self, other)
    def __rsub__(self, other): return BinOp("-", other, self)
    def __mul__(self, other): return BinOp("*", self, other)
    def __rmul__(self, other): return BinOp("*", other, self)
    def __truediv__(self, other): return BinOp("/", self, other)
    def __rtruediv__(self, other): return BinOp("/", other, self)

    def __gt__(self, other): return BinOp(">", self, other)
    def __lt__(self, other): return BinOp("<", self, other)
    def __ge__(self, other): return BinOp(">=", self, other)
    def __le__(self, other): return BinOp("<=", self, other)
    def __eq__(self, other): return BinOp("=", self, other)
    def __ne__(self, other): return BinOp("<>", self, other)

    def __and__(self, other): return BinOp("and", self, other)
    def __or__(self, other): return BinOp("or", self, other)
    def __invert__(self): return UnaryOp("not", self)

    def __bool__(self):
        raise TypeError(
            "TriggerExpr cannot be used with 'and'/'or'/'not' keywords — use '&', '|', '~' instead"
        )

    # Required because __eq__ is overridden.
    __hash__ = object.__hash__


class BinOp(TriggerExpr):
    def __init__(self, op: str, left, right):
        self._op, self._left, self._right = op, left, right

    def __str__(self) -> str:
        return f"({self._left} {self._op} {self._right})"


class UnaryOp(TriggerExpr):
    def __init__(self, op: str, operand):
        self._op, self._operand = op, operand

    def __str__(self) -> str:
        return f"({self._op} {self._operand})"


class TriggerFunction(TriggerExpr):
    def __init__(self, fn_name: str, *args):
        self._fn = fn_name
        self._args = tuple(a for a in args if a is not None)

    def __str__(self) -> str:
        return f"{self._fn}({','.join(_render_arg(a) for a in self._args)})"