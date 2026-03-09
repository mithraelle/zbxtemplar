import yaml


class Context:
    def __init__(self):
        self.macro_names = set()
        self.template_group_names = set()
        self.host_group_names = set()
        self.user_group_names = set()

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
            self.template_group_names.add(g["name"])
        for g in zx.get("host_groups", []):
            self.host_group_names.add(g["name"])
        for t in zx.get("templates", []):
            for m in t.get("macros", []):
                self.macro_names.add(m["macro"])
        for h in zx.get("hosts", []):
            for m in h.get("macros", []):
                self.macro_names.add(m["macro"])

    def _load_set_macro(self, macros: list):
        for m in macros:
            self.macro_names.add("{$" + m["name"] + "}")

    def _load_user_group(self, groups: list):
        for g in groups:
            self.user_group_names.add(g["name"])
            for hg in g.get("host_groups", []):
                self.host_group_names.add(hg["name"])
            for tg in g.get("template_groups", []):
                self.template_group_names.add(tg["name"])

    def _load_add_user(self, users: list):
        for u in users:
            for gname in u.get("groups", []):
                self.user_group_names.add(gname)