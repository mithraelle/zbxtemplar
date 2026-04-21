from enum import StrEnum

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags, WithGroups, YesNo
from zbxtemplar.zabbix.macro import Macro, WithMacros
from zbxtemplar.zabbix.Trigger import WithTriggers
from zbxtemplar.zabbix.Graph import WithGraphs
from zbxtemplar.zabbix.Dashboard import Dashboard
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
    def __init__(self):
        super().__init__()
        self.templates: list["Template"] = []

    def link_template(self, template: "Template"):
        if any(t.name == template.name for t in self.templates):
            raise ValueError(
                f"Duplicate template '{template.name}' on host '{self.name}'"
            )
        self.templates.append(template)
        return self

    def templates_to_list(self):
        return [{"name": t.name} for t in self.templates]


class Template(ZbxEntity, WithTags, WithMacros, WithGroups, WithTriggers, WithGraphs, WithTemplates, WithItems, WithValueMaps):
    """Zabbix template: container for items, triggers, graphs, dashboards, macros, and value maps."""

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
        self.dashboards.append(dashboard)
        return dashboard

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
