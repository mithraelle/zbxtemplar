import os
import re

import yaml

from zbxtemplar.decree import UserGroup, User, UserMedia, GuiAccess, Permission, Severity, MacroType
from zbxtemplar.decree.Token import TokenOutput
from zbxtemplar.executor.TokenExecutor import TokenExecutor, TokenExecutorError
from zbxtemplar.executor.EncryptionExecutor import EncryptionExecutor
from zbxtemplar.executor.exceptions import ExecutorApiError, ExecutorParseError
from zabbix_utils import APIRequestError


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
        print("Updating super admin password...")
        try:
            self._api.user.update(userid="1", passwd=password)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to update super admin password: {e}") from e

    def _validate_macro(self, macro, index=None):
        prefix = f"macro[{index}]" if index is not None else "macro"
        if not isinstance(macro, dict):
            raise ValueError(f"{prefix}: expected a mapping with 'name' and 'value', got {type(macro).__name__}")
        for key in ("name", "value"):
            if key not in macro:
                raise ValueError(f"{prefix}: missing required field '{key}'")
        macro_type = macro.get("type", MacroType.TEXT)
        if macro_type not in MacroType._API_VALUES:
            raise ValueError(f"{prefix}: invalid type '{macro_type}', expected one of: {', '.join(MacroType._API_VALUES)}")

    def _load_macros_from_file(self, path):
        resolved_path = self._resolve_path(path)
        try:
            with open(resolved_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ExecutorParseError(f"Failed to parse macro file '{resolved_path}': {e}", path=resolved_path) from e
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
            macro_type = MacroType._API_VALUES[macro.get("type", MacroType.TEXT)]

            if wire_name in existing:
                print(f"Updating macro {wire_name}...")
                try:
                    self._api.usermacro.updateglobal(
                        globalmacroid=existing[wire_name], value=value, type=macro_type
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update macro '{wire_name}': {e}") from e
            else:
                print(f"Creating macro {wire_name}...")
                try:
                    self._api.usermacro.createglobal(
                        macro=wire_name, value=value, type=macro_type
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create macro '{wire_name}': {e}") from e

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
        resolved_path = self._resolve_path(path)
        with open(resolved_path) as f:
            yaml_content = f.read()
        print(f"Importing {path}...")
        try:
            self._api.configuration.import_(
                source=yaml_content, format="yaml", rules=self._IMPORT_RULES
            )
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to import '{path}': {e}") from e

    def apply(self, data):
        if isinstance(data, list):
            for item in data:
                self._apply_file(item)
        else:
            self._apply_file(data)

    def _resolve_rights(self, groups, group_lookup, label):
        rights = []
        for g in groups:
            name = g["name"]
            if name not in group_lookup:
                raise ValueError(f"{label} '{name}' not found in Zabbix")
            perm = g.get("permission", Permission.READ)
            rights.append({"id": group_lookup[name], "permission": Permission._API_VALUES[perm]})
        return rights

    def _decree_user_group(self, data):
        host_groups = {g["name"]: g["groupid"] for g in self._api.hostgroup.get(output=["groupid", "name"])}
        template_groups = {g["name"]: g["groupid"] for g in self._api.templategroup.get(output=["groupid", "name"])}
        existing_ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}

        for raw in data:
            ug = UserGroup.from_dict(raw)
            gui = ug.gui_access or GuiAccess.DEFAULT
            params = {"name": ug.name, "gui_access": GuiAccess._API_VALUES[gui]}

            if ug.host_groups:
                params["hostgroup_rights"] = self._resolve_rights(ug.host_groups, host_groups, "Host group")
            if ug.template_groups:
                params["templategroup_rights"] = self._resolve_rights(ug.template_groups, template_groups, "Template group")

            if ug.name in existing_ugroups:
                params["usrgrpid"] = existing_ugroups[ug.name]
                del params["name"]
                print(f"Updating user group '{ug.name}'...")
                try:
                    self._api.usergroup.update(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update user group '{ug.name}': {e}") from e
            else:
                print(f"Creating user group '{ug.name}'...")
                try:
                    self._api.usergroup.create(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create user group '{ug.name}': {e}") from e

    def _decree_add_user(self, data):
        data = self._resolve(data)
        raw_users = data if isinstance(data, list) else [data]
        users = [User.from_dict(raw) for raw in raw_users]
        token_executor = TokenExecutor(self._api, self._resolve_path)
        token_executor.validate(users)

        roles = {r["name"]: r["roleid"] for r in self._api.role.get(output=["roleid", "name"])}
        ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        media_types = {m["name"]: m["mediatypeid"] for m in self._api.mediatype.get(output=["mediatypeid", "name"])}
        existing = {u["username"]: u["userid"] for u in self._api.user.get(output=["userid", "username"])}

        for user in users:
            if user.role not in roles:
                raise ValueError(f"Role '{user.role}' not found in Zabbix")
            params = {"username": user.username, "roleid": roles[user.role]}

            if user.password:
                params["passwd"] = user.password

            if user.groups:
                usrgrps = []
                for gname in user.groups:
                    if gname not in ugroups:
                        raise ValueError(f"User group '{gname}' not found in Zabbix")
                    usrgrps.append({"usrgrpid": ugroups[gname]})
                params["usrgrps"] = usrgrps

            if user.medias:
                medias = []
                for m in user.medias:
                    if m.type not in media_types:
                        raise ValueError(f"Media type '{m.type}' not found in Zabbix")
                    media = {"mediatypeid": media_types[m.type], "sendto": m.sendto}
                    if m.severity is not None:
                        media["severity"] = Severity.mask(m.severity)
                    if m.period is not None:
                        media["period"] = m.period
                    medias.append(media)
                params["medias"] = medias

            if user.username in existing:
                params["userid"] = existing[user.username]
                del params["username"]
                print(f"Updating user '{user.username}'...")
                try:
                    self._api.user.update(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update user '{user.username}': {e}") from e
            else:
                print(f"Creating user '{user.username}'...")
                try:
                    create_result = self._api.user.create(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create user '{user.username}': {e}") from e
                userids = (create_result or {}).get("userids")
                if not userids:
                    raise ValueError(f"Unable to resolve created user id for '{user.username}'")
                existing[user.username] = userids[0]

            if user.token:
                try:
                    updated = token_executor.provision(
                        user.token, existing[user.username], force=user.force_token
                    )
                    action = "Updated" if updated else "Created"
                    print(f"{action} API token '{user.token.name}' for '{user.username}'.")
                    if user.token.store_at is not TokenOutput.STDOUT:
                        print(f"Wrote token to '{user.token.store_at}'.")
                except TokenExecutorError as e:
                    raise TokenExecutorError(
                        f"User '{user.username}' token '{user.token.name}': {e}"
                    ) from e

    # Condition types that store names needing ID resolution
    _CONDITION_RESOLVERS = {
        0: ("hostgroup", "groupid", "Host group"),
        1: ("host", "hostid", "Host"),
        2: ("trigger", "triggerid", "Trigger"),
        13: ("template", "templateid", "Template"),
        18: ("drule", "druleid", "Discovery rule"),
        20: ("proxy", "proxyid", "Proxy"),
    }

    def _resolve_conditions(self, conditions):
        lookups = {}
        for cond in conditions:
            ct = cond["conditiontype"]
            if ct in self._CONDITION_RESOLVERS and ct not in lookups:
                api_name, id_field, _ = self._CONDITION_RESOLVERS[ct]
                api = getattr(self._api, api_name)
                lookups[ct] = {
                    item["name"]: item[id_field]
                    for item in api.get(output=[id_field, "name"])
                }

        for cond in conditions:
            ct = cond["conditiontype"]
            if ct in lookups:
                _, _, label = self._CONDITION_RESOLVERS[ct]
                name = cond["value"]
                if name not in lookups[ct]:
                    raise ValueError(f"{label} '{name}' not found in Zabbix")
                cond["value"] = lookups[ct][name]

    def _resolve_operations(self, ops, ugroups, users, media_types, host_groups, templates):
        for op in ops:
            if "opmessage_grp" in op:
                for entry in op["opmessage_grp"]:
                    name = entry["usrgrpid"]
                    if name not in ugroups:
                        raise ValueError(f"User group '{name}' not found in Zabbix")
                    entry["usrgrpid"] = ugroups[name]
            if "opmessage_usr" in op:
                for entry in op["opmessage_usr"]:
                    name = entry["userid"]
                    if name not in users:
                        raise ValueError(f"User '{name}' not found in Zabbix")
                    entry["userid"] = users[name]
            if "opmessage" in op:
                msg = op["opmessage"]
                if "mediatypeid" in msg:
                    name = msg["mediatypeid"]
                    if name not in media_types:
                        raise ValueError(f"Media type '{name}' not found in Zabbix")
                    msg["mediatypeid"] = media_types[name]
            if "opgroup" in op:
                for entry in op["opgroup"]:
                    name = entry["groupid"]
                    if name not in host_groups:
                        raise ValueError(f"Host group '{name}' not found in Zabbix")
                    entry["groupid"] = host_groups[name]
            if "optemplate" in op:
                for entry in op["optemplate"]:
                    name = entry["templateid"]
                    if name not in templates:
                        raise ValueError(f"Template '{name}' not found in Zabbix")
                    entry["templateid"] = templates[name]

    def _decree_actions(self, data):
        ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        users = {u["username"]: u["userid"] for u in self._api.user.get(output=["userid", "username"])}
        media_types = {m["name"]: m["mediatypeid"] for m in self._api.mediatype.get(output=["mediatypeid", "name"])}
        host_groups = {g["name"]: g["groupid"] for g in self._api.hostgroup.get(output=["groupid", "name"])}
        templates = {t["name"]: t["templateid"] for t in self._api.template.get(output=["templateid", "name"])}
        existing = {a["name"]: a["actionid"] for a in self._api.action.get(output=["actionid", "name"])}

        for action in data:
            name = action["name"]

            if "filter" in action and "conditions" in action["filter"]:
                self._resolve_conditions(action["filter"]["conditions"])

            for op_key in ("operations", "recovery_operations", "update_operations"):
                if op_key in action:
                    self._resolve_operations(action[op_key], ugroups, users, media_types, host_groups, templates)

            if name in existing:
                action["actionid"] = existing[name]
                del action["name"]
                print(f"Updating action '{name}'...")
                try:
                    self._api.action.update(**action)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update action '{name}': {e}") from e
            else:
                print(f"Creating action '{name}'...")
                try:
                    self._api.action.create(**action)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create action '{name}': {e}") from e

    def _decree_encryption(self, data):
        data = self._resolve(data)
        EncryptionExecutor(self._api).decree(data)

    _DECREE_ACTIONS = (
        ("user_group", "_decree_user_group"),
        ("add_user", "_decree_add_user"),
        ("actions", "_decree_actions"),
        ("encryption", "_decree_encryption"),
    )

    def _load_decree_file(self, path):
        resolved_path = self._resolve_path(path)
        try:
            with open(resolved_path) as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ExecutorParseError(f"Failed to parse decree file '{resolved_path}': {e}", path=resolved_path) from e

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

        unknown = set(data.keys()) - {k for k, _ in self._DECREE_ACTIONS}
        if unknown:
            raise ExecutorParseError(f"Unknown keys in decree document: {', '.join(sorted(unknown))}")

        for key, method in self._DECREE_ACTIONS:
            if key in data:
                getattr(self, method)(data[key])

    def add_user(self, data):
        if isinstance(data, str):
            resolved_path = self._resolve_path(data)
            try:
                with open(resolved_path) as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ExecutorParseError(f"Failed to parse user file '{resolved_path}': {e}", path=resolved_path) from e
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

    def _preflight_scroll(self, stages):
        combined = []
        for stage in stages.values():
            for action_name in ("set_macro", "decree"):
                value = stage.get(action_name)
                if value is None:
                    continue
                if isinstance(value, str):
                    combined.append(self._load_decree_file(value))
                elif isinstance(value, dict):
                    combined.append(value)
                elif isinstance(value, list):
                    for entry in value:
                        if isinstance(entry, str):
                            combined.append(self._load_decree_file(entry))
                        else:
                            combined.append(entry)
        if combined:
            _preflight_env_check(combined)

    def run_scroll(self, scroll_path, from_stage=None, only_stage=None):
        self._base_dir = os.path.dirname(os.path.abspath(scroll_path))
        try:
            with open(scroll_path) as f:
                scroll = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ExecutorParseError(f"Failed to parse scroll file '{scroll_path}': {e}", path=scroll_path) from e

        unknown = set(scroll.keys()) - {"stages"}
        if unknown:
            raise ExecutorParseError(f"Unknown keys in scroll document '{scroll_path}': {', '.join(sorted(unknown))}")

        stages = {s["stage"]: s for s in scroll["stages"]}
        self._preflight_scroll(stages)

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
