from zbxtemplar.modules.BaseModule import BaseModule
from zbxtemplar.zabbix.Template import Template, TemplateGroup
from zbxtemplar.zabbix.Host import Host, HostGroup


class TemplarModule(BaseModule):
    def __init__(self, **kwargs):
        self.templates: list[Template] = []
        self.hosts: list[Host] = []
        super().__init__(**kwargs)

    def add_template(self, name: str, groups: list[TemplateGroup]) -> Template:
        if any(t.name == name for t in self.templates):
            raise ValueError(
                f"{type(self).__name__}: duplicate template '{name}'"
            )
        template = Template(name=name, groups=groups)
        self.templates.append(template)
        return template

    def add_host(self, name: str, groups: list[HostGroup]) -> Host:
        if any(h.name == name for h in self.hosts):
            raise ValueError(
                f"{type(self).__name__}: duplicate host '{name}'"
            )
        host = Host(name=name, groups=groups)
        self.hosts.append(host)
        return host

    def _export_templates(self, zx: dict):
        if not self.templates:
            return
        groups = {}
        for t in self.templates:
            if not t.groups:
                raise ValueError(f"Template '{t.name}' has no groups. Add at least one TemplateGroup.")
            for g in t.groups:
                groups[g.name] = g
        zx["template_groups"] = [g.to_dict() for g in sorted(groups.values(), key=lambda g: g.name)]
        zx["templates"] = [t.to_dict() for t in self.templates]

    def _export_hosts(self, zx: dict):
        if not self.hosts:
            return
        groups = {}
        for h in self.hosts:
            if not h.groups:
                raise ValueError(f"Host '{h.name}' has no groups. Add at least one HostGroup.")
            for g in h.groups:
                groups[g.name] = g
        zx["host_groups"] = [g.to_dict() for g in sorted(groups.values(), key=lambda g: g.name)]
        zx["hosts"] = [h.to_dict() for h in self.hosts]

    def _export_extras(self, zx: dict, entities: list):
        triggers = [tr for entity in entities for tr in entity.triggers]
        if triggers:
            zx["triggers"] = [t.to_dict() for t in triggers]
        graphs = [gr for entity in entities for gr in entity.graphs]
        if graphs:
            zx["graphs"] = [g.to_dict() for g in graphs]

    def export_templates(self, version: str = "7.4") -> dict:
        export = {"zabbix_export": {"version": version}}
        zx = export["zabbix_export"]
        self._export_templates(zx)
        self._export_extras(zx, self.templates)
        return export

    def export_hosts(self, version: str = "7.4") -> dict:
        export = {"zabbix_export": {"version": version}}
        zx = export["zabbix_export"]
        self._export_hosts(zx)
        self._export_extras(zx, self.hosts)
        return export

    def to_export(self, version: str = "7.4") -> dict:
        export = {"zabbix_export": {"version": version}}
        zx = export["zabbix_export"]
        self._export_templates(zx)
        self._export_hosts(zx)
        self._export_extras(zx, self.templates + self.hosts)
        return export
