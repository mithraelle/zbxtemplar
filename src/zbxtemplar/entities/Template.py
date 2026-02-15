from typing import List, Union

import zbxtemplar.core.ZbxEntity as _zbx
from zbxtemplar.core.ZbxEntity import ZbxEntity, WithTags, WithMacros
from zbxtemplar.entities.Dashboard import Widget, Dashboard
from zbxtemplar.entities.Item import Item


class Template(ZbxEntity, WithTags, WithMacros):
    def __init__(self, name: str, groups: Union[None, List[str]] = None):
        super().__init__(name)
        if groups is None:
            groups = [_zbx.ZBX_TEMPLAR_TEMPLATE_GROUP]
        self.template = name
        self.items: List[Item] = []
        self.dashboards: List[Dashboard] = []
        self.groups = [{"name": g} for g in groups]

    def add_item(self, item: Item):
        item._host = self.name
        self.items.append(item)
        return self

    def add_dashboard(self, dashboard: Dashboard):
        self.dashboards.append(dashboard)
        return self

