from enum import StrEnum

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags, WithGroups
from zbxtemplar.zabbix.macro import Macro, WithMacros
from zbxtemplar.zabbix.Trigger import WithTriggers
from zbxtemplar.zabbix.Graph import WithGraphs
from zbxtemplar.zabbix.Dashboard import Dashboard
from zbxtemplar.zabbix.Item import Item


class TemplateGroup(ZbxEntity):
    def __init__(self, name: str):
        super().__init__(name)


class ValueMapType(StrEnum):
    EQUAL = "EQUAL"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    IN_RANGE = "IN_RANGE"
    REGEXP = "REGEXP"
    DEFAULT = "DEFAULT"


class ValueMap(ZbxEntity):
    def __init__(self, name: str):
        super().__init__(name)
        self.mappings: list[dict[str, str]] = []

    def add_mapping(self, value: str, newvalue: str, type: ValueMapType = ValueMapType.EQUAL):
        self.mappings.append({"value": value, "newvalue": newvalue, "type": type.value})
        return self


class Template(ZbxEntity, WithTags, WithMacros, WithGroups, WithTriggers, WithGraphs):
    def __init__(self, name: str, groups: list[TemplateGroup] | None = None):
        super().__init__(name)
        self.template = name
        self.items: list[Item] = []
        self.dashboards: list[Dashboard] = []
        self.valuemaps: list[ValueMap] = []
        self.groups = groups or []

    def add_item(self, item: Item):
        if any(i.key == item.key for i in self.items):
            raise ValueError(
                f"Duplicate item key '{item.key}' on template '{self.name}'"
            )
        item._host = self.name
        self.items.append(item)
        return self

    def add_dashboard(self, dashboard: Dashboard):
        if any(d.name == dashboard.name for d in self.dashboards):
            raise ValueError(
                f"Duplicate dashboard '{dashboard.name}' on template '{self.name}'"
            )
        self.dashboards.append(dashboard)
        return self

    def add_value_map(self, value_map: ValueMap):
        if any(v.name == value_map.name for v in self.valuemaps):
            raise ValueError(
                f"Duplicate value map '{value_map.name}' on template '{self.name}'"
            )
        self.valuemaps.append(value_map)
        return self

    @classmethod
    def from_dict(cls, data: dict, template_groups=None):
        groups = []
        for g in data.get("groups", []):
            name = g["name"]
            if template_groups is not None:
                if name not in template_groups:
                    template_groups[name] = TemplateGroup(name)
                groups.append(template_groups[name])
            else:
                groups.append(TemplateGroup(name))
        template = cls(name=data["name"], groups=groups)
        for m in data.get("macros", []):
            macro = Macro.from_dict(m)
            template.macros[macro.name] = macro
        for t in data.get("tags", []):
            template.add_tag(t["tag"], t.get("value", ""))
        for i in data.get("items", []):
            template.items.append(Item.from_dict(i, host=data["name"]))
        return template
