import yaml


class Context:
    def __init__(self):
        self._macros = {}
        self._template_groups = {}
        self._host_groups = {}
        self._user_groups = {}

    def get_macro(self, name: str) -> str:
        if name not in self._macros:
            raise ValueError(f"Macro '{name}' not found in context")
        return name

    def get_template_group(self, name: str) -> str:
        if name not in self._template_groups:
            raise ValueError(f"Template group '{name}' not found in context")
        return name

    def get_host_group(self, name: str) -> str:
        if name not in self._host_groups:
            raise ValueError(f"Host group '{name}' not found in context")
        return name

    def get_user_group(self, name: str) -> str:
        if name not in self._user_groups:
            raise ValueError(f"User group '{name}' not found in context")
        return name

    _KNOWN_KEYS = {"zabbix_export", "set_macro", "user_group", "add_user"}

    def load(self, filename: str):
        with open(filename) as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"{filename}: expected a YAML mapping, got {type(data).__name__}")

        if not (set(data.keys()) & self._KNOWN_KEYS):
            top = ", ".join(sorted(data.keys()))
            raise ValueError(f"{filename}: unknown format (top-level keys: {top})")

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
            self._template_groups[g["name"]] = g
        for g in zx.get("host_groups", []):
            self._host_groups[g["name"]] = g
        for t in zx.get("templates", []):
            for m in t.get("macros", []):
                self._macros[m["macro"]] = m
        for h in zx.get("hosts", []):
            for m in h.get("macros", []):
                self._macros[m["macro"]] = m

    def _load_set_macro(self, macros: list):
        for m in macros:
            self._macros["{$" + m["name"] + "}"] = m

    def _load_user_group(self, groups: list):
        for g in groups:
            self._user_groups[g["name"]] = g
            for hg in g.get("host_groups", []):
                self._host_groups[hg["name"]] = hg
            for tg in g.get("template_groups", []):
                self._template_groups[tg["name"]] = tg

    def _load_add_user(self, users: list):
        for u in users:
            for gname in u.get("groups", []):
                self._user_groups[gname] = {"name": gname}