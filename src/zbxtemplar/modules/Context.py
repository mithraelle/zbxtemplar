import os
import re

import yaml

from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.zabbix.macro import Macro
from zbxtemplar.zabbix.Template import Template, TemplateGroup
from zbxtemplar.zabbix.Host import Host, HostGroup
from zbxtemplar.dicts.Schema import Schema
from zbxtemplar.dicts.ZabbixExport import ZabbixExport
from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.dicts.Scroll import Scroll


class Context:
    _FORMATS = {
        ZabbixExport: "_merge_zabbix_export",
        Scroll: "_merge_scroll",
        Decree: "_merge_decree",
    }

    def __init__(self):
        self._macros: dict[str, Macro] = {}
        self._template_groups = {}
        self._host_groups = {}
        self._templates = {}
        self._hosts = {}
        self._user_groups = {}

    def get_macro(self, name: str) -> Macro:
        clean = name.replace("{$", "").replace("}", "")
        if clean not in self._macros:
            raise ValueError(f"Macro '{name}' not found in context")
        return self._macros[clean]

    def get_template_group(self, name: str) -> TemplateGroup:
        if name not in self._template_groups:
            raise ValueError(f"Template group '{name}' not found in context")
        return self._template_groups[name]

    def get_host_group(self, name: str) -> HostGroup:
        if name not in self._host_groups:
            raise ValueError(f"Host group '{name}' not found in context")
        return self._host_groups[name]

    def get_template(self, name: str) -> Template:
        if name not in self._templates:
            raise ValueError(f"Template '{name}' not found in context")
        return self._templates[name]

    def get_host(self, name: str) -> Host:
        if name not in self._hosts:
            raise ValueError(f"Host '{name}' not found in context")
        return self._hosts[name]

    def get_user_group(self, name: str) -> UserGroup:
        if name not in self._user_groups:
            raise ValueError(f"User group '{name}' not found in context")
        return self._user_groups[name]

    @staticmethod
    def _upsert(registry: dict, key, obj):
        if key in registry:
            registry[key].__dict__.update(obj.__dict__)
        else:
            registry[key] = obj

    def load(self, filename: str):
        path = os.path.abspath(filename)
        prev_base = Schema._base_dir
        Schema._base_dir = os.path.dirname(path)
        try:
            entity_cls = Schema.detect_type(filename)
            data = Schema._load_yaml(path)
            getattr(self, self._FORMATS[entity_cls])(entity_cls.from_data(data))
            return self
        finally:
            Schema._base_dir = prev_base

    def _merge_zabbix_export(self, zx: ZabbixExport):
        for g in zx.template_groups or []:
            self._upsert(self._template_groups, g.name, g)
        for g in zx.host_groups or []:
            self._upsert(self._host_groups, g.name, g)
        for t in zx.templates or []:
            t.groups = [self._template_groups.setdefault(g.name, g) for g in t.groups]
            self._upsert(self._templates, t.name, t)
        for h in zx.hosts or []:
            h.groups = [self._host_groups.setdefault(g.name, g) for g in h.groups]
            h.templates = [self._templates.setdefault(tpl.name, tpl) for tpl in h.templates]
            self._upsert(self._hosts, h.name, h)
        for tr in zx.triggers or []:
            owner = re.search(r'/([^/]+)/', tr.expression or "")
            if not owner:
                continue
            name = owner.group(1)
            if name in self._templates:
                self._templates[name]._triggers.append(tr)
            elif name in self._hosts:
                self._hosts[name]._triggers.append(tr)

    def _merge_decree(self, decree: Decree):
        for ug in decree.user_group or []:
            self._upsert(self._user_groups, ug.name, ug)
            for hg in ug.host_groups or []:
                self._host_groups.setdefault(hg["name"], HostGroup(hg["name"]))
            for tg in ug.template_groups or []:
                self._template_groups.setdefault(tg["name"], TemplateGroup(tg["name"]))
        for u in decree.add_user or []:
            for name in u.groups or []:
                self._user_groups.setdefault(name, UserGroup(name))

    def _merge_scroll(self, scroll: Scroll):
        for m in scroll.set_macro or []:
            self._upsert(self._macros, m.name, m)
        for path in scroll.apply or []:
            with open(Schema._resolve_path(path)) as f:
                raw = yaml.safe_load(f)
            self._merge_zabbix_export(ZabbixExport.from_data(raw))
        if scroll.decree is not None:
            self._merge_decree(scroll.decree)