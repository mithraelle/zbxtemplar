from typing import Dict, List, Union
from enum import Enum

import zbxtemplar.core.ZbxEntity as _zbx
from zbxtemplar.core.ZbxEntity import ZbxEntity, WithTags, WithMacros
from zbxtemplar.entities.Dashboard import Widget, Dashboard
from zbxtemplar.entities.Item import Item


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


class Template(ZbxEntity, WithTags, WithMacros):
    def __init__(self, name: str, groups: Union[None, List[str]] = None):
        super().__init__(name)
        if groups is None:
            groups = [_zbx.ZBX_TEMPLAR_TEMPLATE_GROUP]
        self.template = name
        self.items: List[Item] = []
        self.dashboards: List[Dashboard] = []
        self.valuemaps: List[ValueMap] = []
        self.groups = [{"name": g} for g in groups]

    def add_item(self, item: Item):
        item._host = self.name
        self.items.append(item)
        return self

    def add_dashboard(self, dashboard: Dashboard):
        self.dashboards.append(dashboard)
        return self

    def add_value_map(self, value_map: ValueMap):
        self.valuemaps.append(value_map)
        return self

