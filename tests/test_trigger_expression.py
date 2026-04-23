import pytest

from zbxtemplar.zabbix.Item import Item
from zbxtemplar.zabbix.macro import Macro
from zbxtemplar.zabbix.Trigger import Trigger, WithTriggers, TriggerPriority
from zbxtemplar.catalog.zabbix_7_4.functions.history import Last
from zbxtemplar.catalog.zabbix_7_4.functions.aggregate import Min, Avg, LastForeach


class FakeOwner(WithTriggers):
    def __init__(self, name, items=None):
        super().__init__()
        self.name = name
        self.items = items or []


@pytest.fixture
def item_a():
    return Item("Item A", "cpu.util", host="test.host")


@pytest.fixture
def item_b():
    return Item("Item B", "mem.free", host="test.host")


@pytest.fixture
def macro():
    return Macro(name="THRESHOLD", value="90")


# --- Expression string rendering ---

def test_simple_comparison(item_a):
    t = Trigger("t", Last(item_a) > 90)
    assert t.expression == "last(/test.host/cpu.util) > 90"


def test_rmul_and_macro(item_a, macro):
    t = Trigger("t", 0.5 * Last(item_a) < 3 * macro)
    assert t.expression == "(0.5 * last(/test.host/cpu.util)) < (3 * {$THRESHOLD})"


def test_nested_foreach():
    t = Trigger("t", Avg(LastForeach('/*/cpu.util?[group="Prod"]')) > 80)
    assert t.expression == 'avg(last_foreach(/*/cpu.util?[group="Prod"])) > 80'


def test_logical_and_not(item_a, item_b):
    expr = (Last(item_a) > 1) & ~(Last(item_b) < 0)
    t = Trigger("t", expr)
    assert t.expression == (
        "(last(/test.host/cpu.util) > 1) and (not (last(/test.host/mem.free) < 0))"
    )


def test_bool_keyword_raises(item_a):
    with pytest.raises(TypeError, match="'&'"):
        bool(Last(item_a) > 1)


# --- Baked at init ---

def test_expression_baked_as_string(item_a):
    expr = Last(item_a) > 90
    t = Trigger("high cpu", expr)
    assert isinstance(t.expression, str)
    assert t.expression == "last(/test.host/cpu.util) > 90"


def test_expr_tree_mutation_does_not_affect_trigger(item_a):
    expr = Last(item_a) > 90
    t = Trigger("t", expr)
    expr._right = 999
    assert t.expression == "last(/test.host/cpu.util) > 90"


def test_outer_parens_stripped(item_a, item_b):
    # top-level BinOp produces wrapping parens that Trigger should strip
    expr = (Last(item_a) > 1) & (Last(item_b) < 100)
    t = Trigger("t", expr)
    assert t.expression == (
        "(last(/test.host/cpu.util) > 1) and (last(/test.host/mem.free) < 100)"
    )


# --- items() deduplication ---

def test_items_returns_distinct_refs(item_a, item_b):
    expr = (Last(item_a) > 1) & (Last(item_b) < 100)
    assert expr.items() == [item_a, item_b]


def test_items_deduplicates_same_object(item_a):
    expr = (Last(item_a) > 1) & (Last(item_a) < 100)
    assert expr.items() == [item_a]


def test_items_empty_for_foreach():
    expr = Avg(LastForeach('/*/cpu.util')) > 80
    assert expr.items() == []


# --- WithTriggers.add_trigger routing ---

def test_single_item_inlines_on_item(item_a):
    owner = FakeOwner("myhost", [item_a])
    owner.add_trigger("high cpu", Last(item_a) > 90)
    assert owner._triggers == []
    assert len(item_a.triggers) == 1
    assert item_a.triggers[0].name == "high cpu"


def test_multi_item_goes_to_owner(item_a, item_b):
    owner = FakeOwner("myhost", [item_a, item_b])
    owner.add_trigger("combined", (Last(item_a) > 90) & (Last(item_b) < 100))
    assert len(owner._triggers) == 1
    assert item_a.triggers == []
    assert item_b.triggers == []


def test_same_item_twice_inlines(item_a):
    # two references to same item → len(refs)==1 → inlined
    owner = FakeOwner("myhost", [item_a])
    owner.add_trigger("range", (Last(item_a) > 10) & (Last(item_a) < 90))
    assert owner._triggers == []
    assert len(item_a.triggers) == 1


def test_unowned_item_raises(item_a, item_b):
    owner = FakeOwner("myhost", [item_a])
    with pytest.raises(ValueError, match="not owned"):
        owner.add_trigger("bad", Last(item_b) > 90)


def test_unowned_item_in_multi_raises(item_a, item_b):
    owner = FakeOwner("myhost", [item_a])
    with pytest.raises(ValueError, match="not owned"):
        owner.add_trigger("bad", (Last(item_a) > 1) & (Last(item_b) < 100))


def test_duplicate_name_raises(item_a):
    owner = FakeOwner("myhost", [item_a])
    owner.add_trigger("t1", Last(item_a) > 90)
    with pytest.raises(ValueError, match="Duplicate trigger"):
        owner.add_trigger("t1", Last(item_a) < 80)


def test_add_trigger_returns_owner(item_a):
    owner = FakeOwner("myhost", [item_a])
    result = owner.add_trigger("t", Last(item_a) > 90)
    assert result is owner