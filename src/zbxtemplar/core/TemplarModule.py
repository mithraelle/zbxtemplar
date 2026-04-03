class TemplarModule:
    def __init__(self, context=None):
        self.context = context
        self.templates = []
        self.hosts = []

    def add_template(self, template):
        if any(t.name == template.name for t in self.templates):
            return self
        self.templates.append(template)
        return self

    def add_host(self, host):
        if any(h.name == host.name for h in self.hosts):
            return self
        self.hosts.append(host)
        return self

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