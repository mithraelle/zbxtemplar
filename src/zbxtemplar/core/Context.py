import re

import yaml

from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.decree.User import User
from zbxtemplar.zabbix.ZbxEntity import Macro
from zbxtemplar.zabbix.Template import Template, TemplateGroup
from zbxtemplar.zabbix.Host import Host, HostGroup
from zbxtemplar.zabbix.Trigger import Trigger


class Context:
    def __init__(self):
        self._macros = {}
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

    _KNOWN_KEYS = {"zabbix_export", "set_macro", "user_group", "add_user", "actions", "encryption"}

    @staticmethod
    def _upsert(registry: dict, key, obj):
        if key in registry:
            registry[key].__dict__.update(obj.__dict__)
        else:
            registry[key] = obj

    def load(self, filename: str):
        with open(filename) as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"{filename}: expected a YAML mapping, got {type(data).__name__}")

        unknown = set(data.keys()) - self._KNOWN_KEYS
        if unknown:
            raise ValueError(f"{filename}: unknown format (top-level keys: {', '.join(sorted(unknown))})")

        if "zabbix_export" in data:
            self._load_zabbix_export(data["zabbix_export"])
        if "set_macro" in data:
            self._load_set_macro(data["set_macro"])
        if "user_group" in data:
            self._load_user_group(data["user_group"])
        if "add_user" in data:
            self._load_add_user(data["add_user"])

        return self

    def _load_zabbix_export(self, zx: dict):
        for g in zx.get("template_groups", []):
            self._upsert(self._template_groups, g["name"], TemplateGroup(g["name"]))
        for g in zx.get("host_groups", []):
            self._upsert(self._host_groups, g["name"], HostGroup(g["name"]))
        for t in zx.get("templates", []):
            self._upsert(self._templates, t["name"],
                         Template.from_dict(t, template_groups=self._template_groups))
        for h in zx.get("hosts", []):
            self._upsert(self._hosts, h["name"],
                         Host.from_dict(h, host_groups=self._host_groups, templates=self._templates))
        for tr in zx.get("triggers", []):
            trigger = Trigger.from_dict(tr)
            owner_name = re.search(r'/([^/]+)/', tr.get("expression", ""))
            if owner_name:
                name = owner_name.group(1)
                if name in self._templates:
                    self._templates[name]._triggers.append(trigger)
                elif name in self._hosts:
                    self._hosts[name]._triggers.append(trigger)

    def _load_set_macro(self, macros: list):
        for m in macros:
            macro = Macro.from_dict(m)
            self._upsert(self._macros, macro.name, macro)

    def _load_user_group(self, groups: list):
        for g in groups:
            ug = UserGroup.from_dict(g, host_groups=self._host_groups, template_groups=self._template_groups)
            self._upsert(self._user_groups, ug.name, ug)

    def _load_add_user(self, users: list):
        for u in users:
            User.from_dict(u, user_groups=self._user_groups)