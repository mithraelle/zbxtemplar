from typing import Self

from zbxtemplar.dicts.Schema import Schema, SchemaField
from zbxtemplar.zabbix.Template import Template, TemplateGroup
from zbxtemplar.zabbix.Host import Host, HostGroup
from zbxtemplar.zabbix.Trigger import Trigger


class ZabbixExport(Schema):
    _SCHEMA = [
        SchemaField("version", str_type="str", type=str,
                    description="Zabbix export format version (e.g. '7.4')."),
        SchemaField("template_groups", str_type="list[TemplateGroup]", type=list[TemplateGroup],
                    description="Template group definitions."),
        SchemaField("host_groups", str_type="list[HostGroup]", type=list[HostGroup],
                    description="Host group definitions."),
        SchemaField("templates", str_type="list[Template]", type=list[Template],
                    description="Template definitions."),
        SchemaField("hosts", str_type="list[Host]", type=list[Host],
                    description="Host definitions."),
        SchemaField("triggers", str_type="list[Trigger]", type=list[Trigger],
                    description="Standalone triggers."),
        SchemaField("graphs", str_type="list[dict]", type=list,
                    description="Graph definitions (raw dicts; typed deserialization pending)."),
    ]

    @classmethod
    def from_data(cls, data: dict) -> Self:
        if set(data) == {"zabbix_export"}:
            data = data["zabbix_export"]
        return cls.from_dict(data)