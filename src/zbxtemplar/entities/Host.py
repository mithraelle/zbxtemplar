from typing import List, Union

from zbxtemplar.core.ZbxEntity import ZbxEntity, WithTags, WithMacros, WithGroups
from zbxtemplar.entities.Dashboard import Dashboard
from zbxtemplar.entities.Item import Item
from zbxtemplar.entities.Template import ValueMap


class HostGroup(ZbxEntity):
    def __init__(self, name: str):
        super().__init__(name)


class Host(ZbxEntity, WithTags, WithMacros, WithGroups):
    def __init__(self, name: str, groups: Union[None, List[HostGroup]] = None):
        super().__init__(name)
        if groups is None:
            groups = []
        self.host = name
        self.items: List[Item] = []
        self.valuemaps: List[ValueMap] = []
        self.groups = groups

    def add_item(self, item: Item):
        if not any(i.key == item.key for i in self.items):
            item._host = self.name
            self.items.append(item)
        return self

    def add_value_map(self, value_map: ValueMap):
        if not any(v.name == value_map.name for v in self.valuemaps):
            self.valuemaps.append(value_map)
        return self