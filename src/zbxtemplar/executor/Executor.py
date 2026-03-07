import os
import re

import yaml


def _resolve_env(value):
    if not isinstance(value, str):
        return value

    def replace(match):
        var = match.group(1)
        env_val = os.environ.get(var)
        if env_val is None:
            raise ValueError(f"Environment variable '{var}' is not set")
        return env_val

    return re.sub(r'\$\{(\w+)\}', replace, value)


def _resolve_deep(obj):
    if isinstance(obj, str):
        return _resolve_env(obj)
    if isinstance(obj, dict):
        return {k: _resolve_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_deep(v) for v in obj]
    return obj


def _preflight_env_check(obj):
    missing = set()

    def scan(obj):
        if isinstance(obj, str):
            for match in re.finditer(r'\$\{(\w+)\}', obj):
                var = match.group(1)
                if os.environ.get(var) is None:
                    missing.add(var)
        elif isinstance(obj, dict):
            for v in obj.values():
                scan(v)
        elif isinstance(obj, list):
            for v in obj:
                scan(v)

    scan(obj)
    if missing:
        lines = "\n".join(f"  {var}" for var in sorted(missing))
        raise ValueError(
            f"Pre-flight check failed. Missing environment variables:\n{lines}\n\n"
            "Execution aborted. No changes were made."
        )


class Executor:
    """Executes actions against a Zabbix instance.

    Actions that handle sensitive values (set_super_admin, set_macro,
    add_user) resolve ${} env references before execution.
    Actions that take file paths (apply, decree) do not.
    """

    def __init__(self, api):
        self._api = api
        self._base_dir = None

    def _resolve_path(self, path):
        if self._base_dir and not os.path.isabs(path):
            return os.path.join(self._base_dir, path)
        return path

    def _resolve(self, data):
        _preflight_env_check(data)
        return _resolve_deep(data)

    def set_super_admin(self, data):
        data = self._resolve(data)
        password = data if isinstance(data, str) else data["password"]
        self._api.user.update(userid="1", passwd=password)
        print("Super admin password updated.")

    _MACRO_TYPES = {"text": 0, "secret": 1, "vault": 2}

    def _validate_macro(self, macro, index=None):
        prefix = f"macro[{index}]" if index is not None else "macro"
        if not isinstance(macro, dict):
            raise ValueError(f"{prefix}: expected a mapping with 'name' and 'value', got {type(macro).__name__}")
        for key in ("name", "value"):
            if key not in macro:
                raise ValueError(f"{prefix}: missing required field '{key}'")
        macro_type = macro.get("type", "text")
        if macro_type not in self._MACRO_TYPES:
            raise ValueError(f"{prefix}: invalid type '{macro_type}', expected one of: {', '.join(self._MACRO_TYPES)}")

    def _load_macros_from_file(self, path):
        with open(self._resolve_path(path)) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "set_macro" in data:
            data = data["set_macro"]
        return data if isinstance(data, list) else [data]

    def set_macro(self, data):
        if isinstance(data, str):
            data = self._load_macros_from_file(data)
        if isinstance(data, list):
            flat = []
            for item in data:
                if isinstance(item, str):
                    flat.extend(self._load_macros_from_file(item))
                else:
                    flat.append(item)
            data = flat
        data = self._resolve(data)
        macros = data if isinstance(data, list) else [data]

        for i, macro in enumerate(macros):
            self._validate_macro(macro, i if len(macros) > 1 else None)

        existing = {
            m["macro"]: m["globalmacroid"]
            for m in self._api.usermacro.get(globalmacro=True)
        }

        for macro in macros:
            wire_name = "{$" + macro["name"] + "}"
            value = macro["value"]
            macro_type = self._MACRO_TYPES.get(macro.get("type", "text"), 0)

            if wire_name in existing:
                self._api.usermacro.updateglobal(
                    globalmacroid=existing[wire_name], value=value, type=macro_type
                )
                print(f"Updated macro {wire_name}.")
            else:
                self._api.usermacro.createglobal(
                    macro=wire_name, value=value, type=macro_type
                )
                print(f"Created macro {wire_name}.")

    _IMPORT_RULES = {
        "template_groups": {"createMissing": True, "updateExisting": True},
        "templates": {"createMissing": True, "updateExisting": True},
        "host_groups": {"createMissing": True, "updateExisting": True},
        "hosts": {"createMissing": True, "updateExisting": True},
        "valueMaps": {"createMissing": True, "updateExisting": True},
        "items": {"createMissing": True, "updateExisting": True},
        "triggers": {"createMissing": True, "updateExisting": True},
        "graphs": {"createMissing": True, "updateExisting": True},
        "templateDashboards": {"createMissing": True, "updateExisting": True},
        "mediaTypes": {"createMissing": True, "updateExisting": True},
        "templateLinkage": {"createMissing": True, "deleteMissing": True},
    }

    def _apply_file(self, path):
        with open(self._resolve_path(path)) as f:
            yaml_content = f.read()
        self._api.configuration.import_(
            source=yaml_content, format="yaml", rules=self._IMPORT_RULES
        )
        print(f"Imported {path}.")

    def apply(self, data):
        if isinstance(data, list):
            for item in data:
                self._apply_file(item)
        else:
            self._apply_file(data)

    _GUI_ACCESS = {"DEFAULT": 0, "INTERNAL": 1, "LDAP": 2, "DISABLED": 3}
    _PERMISSIONS = {"NONE": 0, "READ": 2, "READ_WRITE": 3}

    def _resolve_rights(self, groups, group_lookup, label):
        rights = []
        for g in groups:
            name = g["name"]
            if name not in group_lookup:
                raise ValueError(f"{label} '{name}' not found in Zabbix")
            perm = g.get("permission", "READ")
            if perm not in self._PERMISSIONS:
                raise ValueError(f"Invalid permission '{perm}', expected one of: {', '.join(self._PERMISSIONS)}")
            rights.append({"id": group_lookup[name], "permission": self._PERMISSIONS[perm]})
        return rights

    def _decree_user_group(self, data):
        host_groups = {g["name"]: g["groupid"] for g in self._api.hostgroup.get(output=["groupid", "name"])}
        template_groups = {g["name"]: g["groupid"] for g in self._api.templategroup.get(output=["groupid", "name"])}
        existing_ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}

        for ug in data:
            name = ug["name"]
            gui = ug.get("gui_access", "DEFAULT")
            if gui not in self._GUI_ACCESS:
                raise ValueError(f"Invalid gui_access '{gui}', expected one of: {', '.join(self._GUI_ACCESS)}")

            params = {"name": name, "gui_access": self._GUI_ACCESS[gui]}

            if "host_groups" in ug:
                params["hostgroup_rights"] = self._resolve_rights(ug["host_groups"], host_groups, "Host group")
            if "template_groups" in ug:
                params["templategroup_rights"] = self._resolve_rights(ug["template_groups"], template_groups, "Template group")

            if name in existing_ugroups:
                params["usrgrpid"] = existing_ugroups[name]
                del params["name"]
                self._api.usergroup.update(**params)
                print(f"Updated user group '{name}'.")
            else:
                self._api.usergroup.create(**params)
                print(f"Created user group '{name}'.")

    _SEVERITIES = {
        "NOT_CLASSIFIED": 1, "INFORMATION": 2, "WARNING": 4,
        "AVERAGE": 8, "HIGH": 16, "DISASTER": 32,
    }

    def _parse_severity(self, value):
        if isinstance(value, int):
            return value
        mask = 0
        for name in value.split(","):
            name = name.strip()
            if name not in self._SEVERITIES:
                raise ValueError(f"Invalid severity '{name}', expected one of: {', '.join(self._SEVERITIES)}")
            mask |= self._SEVERITIES[name]
        return mask

    def _decree_add_user(self, data):
        data = self._resolve(data)
        users = data if isinstance(data, list) else [data]

        # Build lookups
        roles = {r["name"]: r["roleid"] for r in self._api.role.get(output=["roleid", "name"])}
        ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        media_types = {m["name"]: m["mediatypeid"] for m in self._api.mediatype.get(output=["mediatypeid", "name"])}
        existing = {u["username"]: u["userid"] for u in self._api.user.get(output=["userid", "username"])}

        for user in users:
            username = user["username"]
            role_name = user["role"]
            if role_name not in roles:
                raise ValueError(f"Role '{role_name}' not found in Zabbix")

            params = {"username": username, "roleid": roles[role_name]}

            if "password" in user:
                params["passwd"] = user["password"]

            if "groups" in user:
                usrgrps = []
                for gname in user["groups"]:
                    if gname not in ugroups:
                        raise ValueError(f"User group '{gname}' not found in Zabbix")
                    usrgrps.append({"usrgrpid": ugroups[gname]})
                params["usrgrps"] = usrgrps

            if "medias" in user:
                medias = []
                for m in user["medias"]:
                    type_name = m["type"]
                    if type_name not in media_types:
                        raise ValueError(f"Media type '{type_name}' not found in Zabbix")
                    media = {
                        "mediatypeid": media_types[type_name],
                        "sendto": m["sendto"],
                    }
                    if "severity" in m:
                        media["severity"] = self._parse_severity(m["severity"])
                    if "period" in m:
                        media["period"] = m["period"]
                    medias.append(media)
                params["medias"] = medias

            if username in existing:
                params["userid"] = existing[username]
                del params["username"]
                self._api.user.update(**params)
                print(f"Updated user '{username}'.")
            else:
                self._api.user.create(**params)
                print(f"Created user '{username}'.")

            # Create API token if requested
            if "token" in user:
                userid = existing.get(username) or self._api.user.get(
                    output=["userid"], filter={"username": username}
                )[0]["userid"]
                token_name = f"{username}-token"
                existing_tokens = self._api.token.get(
                    output=["tokenid", "name"],
                    userids=userid,
                    filter={"name": token_name},
                )
                if existing_tokens:
                    if not user.get("force_token"):
                        raise ValueError(
                            f"API token '{token_name}' already exists for user '{username}'. "
                            f"Set force_token: true to delete and recreate."
                        )
                    self._api.token.delete(existing_tokens[0]["tokenid"])
                    print(f"Deleted existing API token for '{username}'.")
                self._api.token.create(
                    name=token_name,
                    userid=userid,
                )
                print(f"Created API token for '{username}'.")

    _DECREE_ACTIONS = (
        ("user_group", "_decree_user_group"),
        ("add_user", "_decree_add_user"),
    )

    def _load_decree_file(self, path):
        with open(self._resolve_path(path)) as f:
            return yaml.safe_load(f)

    def _merge_decree(self, sources):
        merged = {}
        for src in sources:
            if isinstance(src, str):
                src = self._load_decree_file(src)
            for key in src:
                merged.setdefault(key, []).extend(
                    src[key] if isinstance(src[key], list) else [src[key]]
                )
        return merged

    def decree(self, data):
        if isinstance(data, str):
            data = self._load_decree_file(data)
        if isinstance(data, list):
            data = self._merge_decree(data)

        for key, method in self._DECREE_ACTIONS:
            if key in data:
                getattr(self, method)(data[key])

    def add_user(self, data):
        if isinstance(data, str):
            with open(self._resolve_path(data)) as f:
                data = yaml.safe_load(f)
        if isinstance(data, dict):
            if "add_user" in data:
                data = data["add_user"]
            else:
                data = [data]
        self._decree_add_user(data)

    PIPELINE = (
        ("bootstrap", ("set_super_admin", "set_macro")),
        ("templates", ("apply",)),
        ("state",     ("decree",)),
    )

    def run_scroll(self, scroll_path, from_stage=None, only_stage=None):
        self._base_dir = os.path.dirname(os.path.abspath(scroll_path))
        with open(scroll_path) as f:
            scroll = yaml.safe_load(f)

        stages = {s["stage"]: s for s in scroll["stages"]}

        pipeline = self.PIPELINE
        if only_stage:
            pipeline = [(name, actions) for name, actions in pipeline if name == only_stage]
        elif from_stage:
            start = next((i for i, (name, _) in enumerate(pipeline) if name == from_stage), None)
            if start is not None:
                pipeline = pipeline[start:]

        for stage_name, actions in pipeline:
            if stage_name not in stages:
                continue
            stage = stages[stage_name]
            print(f"--- stage: {stage_name}")
            for action in actions:
                if action in stage:
                    getattr(self, action)(stage[action])