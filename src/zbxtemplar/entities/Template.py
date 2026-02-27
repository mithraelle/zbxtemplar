from typing import Dict, List, Union
from enum import Enum

import zbxtemplar.core.ZbxEntity as _zbx
from zbxtemplar.core.ZbxEntity import ZbxEntity, WithTags, WithMacros, WithGroups
from zbxtemplar.entities.Dashboard import Widget, Dashboard
from zbxtemplar.entities.Item import Item


class TemplateGroup(ZbxEntity):
    def __init__(self, name: str):
        super().__init__(name)


class ValueMapType(str, Enum):
    EQUAL = "EQUAL"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    IN_RANGE = "IN_RANGE"
    REGEXP = "REGEXP"
    DEFAULT = "DEFAULT"


class ValueMap(ZbxEntity):
    def __init__(self, name: str):
        super().__init__(name)
        self.mappings: List[Dict[str, str]] = []

    def add_mapping(self, value: str, newvalue: str, type: ValueMapType = ValueMapType.EQUAL):
        self.mappings.append({"value": value, "newvalue": newvalue, "type": type.value})
        return self


class Template(ZbxEntity, WithTags, WithMacros, WithGroups):
    def __init__(self, name: str, groups: Union[None, List[TemplateGroup]] = None):
        super().__init__(name)
        if groups is None:
            groups = [TemplateGroup(_zbx.ZBX_TEMPLAR_TEMPLATE_GROUP)]
        self.template = name
        self.items: List[Item] = []
        self.dashboards: List[Dashboard] = []
        self.valuemaps: List[ValueMap] = []
        self.groups = groups

    def add_item(self, item: Item):
        if not any(i.key == item.key for i in self.items):
            item._host = self.name
            self.items.append(item)
        return self

    def add_dashboard(self, dashboard: Dashboard):
        if not any(d.name == dashboard.name for d in self.dashboards):
            self.dashboards.append(dashboard)
        return self

    def add_value_map(self, value_map: ValueMap):
        if not any(v.name == value_map.name for v in self.valuemaps):
            self.valuemaps.append(value_map)
        return self
