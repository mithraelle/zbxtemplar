from abc import ABC, abstractmethod

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, YesNo, WithTags, WithGroups
from zbxtemplar.zabbix.macro import Macro, WithMacros
from zbxtemplar.zabbix.Trigger import WithTriggers
from zbxtemplar.zabbix.Graph import WithGraphs
from zbxtemplar.zabbix.Item import Item, WithItems
from zbxtemplar.zabbix.Template import Template, ValueMap, WithTemplates, WithValueMaps


class HostGroup(ZbxEntity):
    """Zabbix host group. Created automatically by the executor if missing."""

    def __init__(self, name: str):
        super().__init__(name)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["name"])


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
    """Zabbix agent (passive or active) monitoring interface."""

    def to_dict(self) -> dict:
        return {
            "type": "ZABBIX",
            "useip": self.useip.value,
            "ip": self.ip,
            "dns": self.dns,
            "port": self.port,
            "interface_ref": self.interface_ref,
        }


class Host(ZbxEntity, WithTags, WithMacros, WithGroups, WithTriggers, WithGraphs, WithTemplates, WithItems, WithValueMaps):
    """Zabbix host definition. Exported without UUID — Zabbix rejects UUIDs on hosts."""

    def __init__(self, name: str, groups: list[HostGroup]):
        super().__init__(name)
        self.host = name
        self.interfaces: list[HostInterface] = []
        self.groups = groups
        self._default_interface: HostInterface | None = None

    def add_interface(self, interface: HostInterface, default: bool = False):
        """Register a monitoring interface. The first added becomes the default unless overridden.

        Args:
            interface: AgentInterface or other HostInterface subclass.
            default: Force this interface to be the default.
        """
        if any(i.interface_ref == interface.interface_ref for i in self.interfaces):
            raise ValueError(
                f"Duplicate interface ref '{interface.interface_ref}' on host '{self.name}'"
            )
        self.interfaces.append(interface)
        if default or self._default_interface is None:
            self._default_interface = interface
        return self

    def interfaces_to_list(self):
        return [
            {**iface.to_dict(), "default": YesNo.YES.value if iface is self._default_interface else YesNo.NO.value}
            for iface in self.interfaces
        ]

    def to_dict(self, **kwargs):
        return super().to_dict(skip_uuid=True)

    @classmethod
    def from_dict(cls, data: dict):
        groups = [HostGroup(g["name"]) for g in data.get("groups", [])]
        host = cls(name=data["name"], groups=groups)
        for m in data.get("macros", []):
            macro = Macro.from_dict(m)
            host.macros[macro.name] = macro
        for t in data.get("tags", []):
            host.add_tag(t["tag"], t.get("value", ""))
        for tname in data.get("templates", []):
            host.templates.append(Template(name=tname["name"], groups=[]))
        for i in data.get("items", []):
            host.items.append(Item.from_dict(i, host=data["name"]))
        return host