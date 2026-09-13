import re
from enum import StrEnum

from zbxtemplar.dicts.Schema import FieldPolicy, SchemaField, SubsetBy
from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags, WithGroups, YesNo
from zbxtemplar.zabbix.macro import Macro, WithMacros
from zbxtemplar.zabbix.Trigger import WithTriggers
from zbxtemplar.zabbix.Graph import WithGraphs
from zbxtemplar.zabbix.Dashboard import Dashboard, ItemPattern
from zbxtemplar.zabbix.Item import Item, WithItems


class TemplateGroup(ZbxEntity):
    """Zabbix template group. Created automatically by the executor if missing."""

    def __init__(self, name: str):
        super().__init__(name)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["name"])


class ValueMapType(StrEnum):
    """Match type for a value map entry."""

    EQUAL = "EQUAL"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    IN_RANGE = "IN_RANGE"
    REGEXP = "REGEXP"
    DEFAULT = "DEFAULT"


class ValueMap(ZbxEntity):
    """Named mapping from raw collected values to human-readable display strings."""

    def __init__(self, name: str):
        super().__init__(name)
        self.mappings: list[dict[str, str]] = []

    def add_mapping(self, value: str, newvalue: str, type: ValueMapType = ValueMapType.EQUAL):
        """Add a mapping entry. Returns self for chaining.

        Args:
            value: Raw incoming value to match.
            newvalue: Display string shown in Zabbix.
            type: Match type; defaults to EQUAL.
        """
        self.mappings.append({"value": value, "newvalue": newvalue, "type": type.value})
        return self

class WithValueMaps:
    name: str

    def __init__(self):
        super().__init__()
        self.valuemaps: list[ValueMap] = []

    def add_value_map(self, name: str) -> ValueMap:
        """Create, register and return a new ValueMap. Raises on duplicate name."""
        if any(v.name == name for v in self.valuemaps):
            raise ValueError(
                f"Duplicate value map '{name}' on '{self.name}'"
            )
        value_map = ValueMap(name)
        self.valuemaps.append(value_map)
        return value_map


class WithTemplates:
    name: str

    def __init__(self):
        super().__init__()
        self.templates: list["Template"] = []

    def link_template(self, template: "Template"):
        if any(t.name == template.name for t in self.templates):
            raise ValueError(
                f"Duplicate template '{template.name}' on {type(self).__name__.lower()} '{self.name}'"
            )
        self.templates.append(template)
        return self

    def templates_to_list(self):
        return [{"name": t.name} for t in self.templates]


class Template(ZbxEntity, WithTags, WithMacros, WithGroups, WithTriggers, WithGraphs, WithTemplates, WithItems, WithValueMaps):
    """Zabbix template: container for items, triggers, graphs, dashboards, macros, and value maps."""

    # Drives Comparator only; serialization stays with ZbxEntity.to_dict.
    # IGNORE marks fields from_dict() does not parse: the API side is always
    # empty, so comparing them would report drift that isn't there. Teach
    # from_dict() to read one and drop its IGNORE to switch comparison on.
    _SCHEMA = [
        SchemaField("name", type=str),
        SchemaField("template", type=str),
        SchemaField("uuid", type=str),
        SchemaField("groups", policy=SubsetBy("name")),
        SchemaField("items", policy=SubsetBy("key")),
        # Multi-item triggers only: add_trigger() inlines single-item ones onto
        # the item. Reaches the WithTriggers property, which vars() cannot see.
        SchemaField("triggers", policy=SubsetBy("name")),
        SchemaField("macros"),
        SchemaField("tags"),
        SchemaField("dashboards", policy=FieldPolicy.IGNORE),
        SchemaField("valuemaps", policy=FieldPolicy.IGNORE),
        SchemaField("templates", policy=FieldPolicy.IGNORE),
    ]

    def __init__(self, name: str, groups: list[TemplateGroup]):
        super().__init__(name)
        self.template = name
        self.dashboards: list[Dashboard] = []
        self.groups = groups

    def add_dashboard(self, name: str, display_period: int = 0,
                      auto_start: YesNo = YesNo.YES) -> Dashboard:
        """Create, register and return a new Dashboard. Raises on duplicate name."""
        dashboard = Dashboard(name=name, display_period=display_period, auto_start=auto_start)
        if any(d.name == dashboard.name for d in self.dashboards):
            raise ValueError(
                f"Duplicate dashboard '{dashboard.name}' on template '{self.name}'"
            )
        dashboard._host = self.name
        self.dashboards.append(dashboard)
        return dashboard

    def get_item_pattern(self, pattern: str) -> ItemPattern:
        """Return the pattern checked against item names of this template and its
        linked templates (``*`` wildcard, full-name match). Raises ValueError when
        nothing matches. Construct ItemPattern directly for patterns meant to
        match items that don't exist yet.
        """
        regex = re.compile(".*".join(re.escape(part) for part in pattern.split("*")))
        stack, seen = [self], set()
        while stack:
            template = stack.pop()
            if template.name in seen:
                continue
            seen.add(template.name)
            if any(regex.fullmatch(item.name) for item in template.items):
                return ItemPattern(pattern)
            stack.extend(template.templates)
        raise ValueError(
            f"Pattern '{pattern}' matches no item name on '{self.name}' or its linked templates"
        )

    @classmethod
    def from_dict(cls, data: dict):
        groups = [TemplateGroup(g["name"]) for g in data.get("groups", [])]
        template = cls(name=data["name"], groups=groups)
        for m in data.get("macros", []):
            macro = Macro.from_dict(m)
            template.macros[macro.name] = macro
        for t in data.get("tags", []):
            template.add_tag(t["tag"], t.get("value", ""))
        for i in data.get("items", []):
            template.items.append(Item.from_dict(i, host=data["name"]))
        return template
