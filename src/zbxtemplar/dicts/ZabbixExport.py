import re
from typing import Self

from zbxtemplar.dicts.Schema import Schema, field
from zbxtemplar.zabbix.Template import Template, TemplateGroup
from zbxtemplar.zabbix.Host import Host, HostGroup
from zbxtemplar.zabbix.Trigger import Trigger


class ZabbixExport(Schema):
    version: str | None = field(
        str_type="str",
        description="Zabbix export format version (e.g. '7.4').",
    )
    template_groups: list[TemplateGroup] | None = field(
        str_type="list[TemplateGroup]",
        description="Template group definitions.",
    )
    host_groups: list[HostGroup] | None = field(
        str_type="list[HostGroup]",
        description="Host group definitions.",
    )
    templates: list[Template] | None = field(
        str_type="list[Template]",
        description="Template definitions.",
    )
    hosts: list[Host] | None = field(
        str_type="list[Host]",
        description="Host definitions.",
    )
    triggers: list[Trigger] | None = field(
        str_type="list[Trigger]",
        description="Standalone triggers.",
    )
    graphs: list[dict] | None = field(
        str_type="list[dict]",
        type=list,
        description="Graph definitions (raw dicts; typed deserialization pending).",
    )

    _OMIT_FROM_SCHEMA_DOCS = True

    @classmethod
    def from_data(cls, data: dict | list | str) -> Self:
        if isinstance(data, dict) and set(data) == {"zabbix_export"}:
            data = data["zabbix_export"]
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__}: expected a mapping, got {type(data).__name__}")
        zx = cls.from_dict(data)
        zx._assign_triggers()
        return zx

    def _assign_triggers(self):
        templates = {t.name: t for t in self.templates or []}
        hosts = {h.name: h for h in self.hosts or []}
        for tr in self.triggers or []:
            owner = re.search(r'/([^/]+)/', tr.expression or "")
            if not owner:
                continue
            name = owner.group(1)
            if name in templates:
                templates[name]._triggers.append(tr)
            elif name in hosts:
                hosts[name]._triggers.append(tr)