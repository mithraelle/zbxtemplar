from abc import ABC, abstractmethod
from typing import List, Union

from zbxtemplar.core.ZbxEntity import ZbxEntity, YesNo, WithTags, WithMacros, WithGroups
from zbxtemplar.entities.Trigger import WithTriggers
from zbxtemplar.entities.Graph import WithGraphs
from zbxtemplar.entities.Item import Item
from zbxtemplar.entities.Template import Template, ValueMap


class HostGroup(ZbxEntity):
    def __init__(self, name: str):
        super().__init__(name)


_interface_counter = 0


class HostInterface(ABC):
    def __init__(self, ip: str = "127.0.0.1", dns: str = "", port: str = "10050", useip: bool = True):
        if useip and not ip:
            raise ValueError("ip is required when useip=True")
        if not useip and not dns:
            raise ValueError("dns is required when useip=False")
        global _interface_counter
        _interface_counter += 1
        self.interface_ref = f"if{_interface_counter}"
        self.ip = ip
        self.dns = dns
        self.port = port
        self.useip = YesNo.YES if useip else YesNo.NO

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class AgentInterface(HostInterface):
    def to_dict(self) -> dict:
        return {
            "type": "ZABBIX",
            "useip": self.useip.value,
            "ip": self.ip,
            "dns": self.dns,
            "port": self.port,
            "interface_ref": self.interface_ref,
        }


class Host(ZbxEntity, WithTags, WithMacros, WithGroups, WithTriggers, WithGraphs):
    def __init__(self, name: str, groups: Union[None, List[HostGroup]] = None):
        super().__init__(name)
        self.host = name
        self.templates: List[Template] = []
        self.interfaces: List[HostInterface] = []
        self.items: List[Item] = []
        self.valuemaps: List[ValueMap] = []
        self.groups = groups or []
        self._default_interface: Union[HostInterface, None] = None

    def add_interface(self, interface: HostInterface, default: bool = False):
        if not any(i.interface_ref == interface.interface_ref for i in self.interfaces):
            self.interfaces.append(interface)
        if default or self._default_interface is None:
            self._default_interface = interface
        return self

    def add_template(self, template: Template):
        if not any(t.name == template.name for t in self.templates):
            self.templates.append(template)
        return self

    def interfaces_to_list(self):
        return [
            {**iface.to_dict(), "default": YesNo.YES.value if iface is self._default_interface else YesNo.NO.value}
            for iface in self.interfaces
        ]

    def templates_to_list(self):
        return [{"name": t.name} for t in self.templates]

    def add_item(self, item: Item):
        if not any(i.key == item.key for i in self.items):
            item._host = self.name
            self.items.append(item)
        return self

    def get_macro(self, name: str):
        clean_name = name.replace("{$", "").replace("}", "")
        macro = self.macros.get(clean_name)
        if macro is not None:
            return macro
        for t in self.templates:
            macro = t.macros.get(clean_name)
            if macro is not None:
                return macro
        raise KeyError(f"Macro '{{${clean_name}}}' not found on host '{self.name}' or its linked templates")

    def add_value_map(self, value_map: ValueMap):
        if not any(v.name == value_map.name for v in self.valuemaps):
            self.valuemaps.append(value_map)
        return self

    def to_dict(self, **kwargs):
        return super().to_dict(skip_uuid=True)