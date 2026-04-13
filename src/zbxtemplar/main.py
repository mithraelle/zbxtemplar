import argparse
import importlib.util
import inspect
import os

import yaml

from zbxtemplar.zabbix.ZbxEntity import set_uuid_namespace
from zbxtemplar.modules.TemplarModule import TemplarModule
from zbxtemplar.modules.DecreeModule import DecreeModule
from zbxtemplar.modules.Context import Context

_COERCE = {int: int, float: float, bool: lambda v: v.lower() in ("1", "true", "yes")}

_BASE_CLASSES = (TemplarModule, DecreeModule)


_LOADER_INJECTED = {"context"}


def _build_kwargs(cls_name, sig, params):
    init_params = {k: v for k, v in sig.parameters.items() if k != "self"}

    unknown = set(params) - set(init_params) - _LOADER_INJECTED
    if unknown:
        raise TypeError(f"{cls_name}: unknown parameter(s): {', '.join(sorted(unknown))}")

    kwargs = {}
    for pname, param in init_params.items():
        if pname in _LOADER_INJECTED:
            continue
        if pname in params:
            value = params[pname]
            ann = param.annotation
            coerce = _COERCE.get(ann)
            if coerce and isinstance(value, str):
                try:
                    value = coerce(value)
                except (ValueError, TypeError):
                    raise TypeError(f"{cls_name}: parameter '{pname}' expects {ann.__name__}, got '{params[pname]}'")
            kwargs[pname] = value
        elif param.default is inspect.Parameter.empty:
            raise TypeError(f"{cls_name}: missing required parameter '{pname}'")

    return kwargs


def load_module(filename: str, params: dict = None, context: Context = None) -> dict:
    mod_name = os.path.splitext(os.path.basename(filename))[0]
    spec = importlib.util.spec_from_file_location(mod_name, filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    params = params or {}
    result = {}
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        for base in _BASE_CLASSES:
            if issubclass(obj, base) and obj is not base:
                sig = inspect.signature(obj.__init__)
                kwargs = _build_kwargs(name, sig, params)
                if context is not None and "context" in sig.parameters:
                    kwargs["context"] = context
                instance = obj(**kwargs)
                result[name] = instance
                break
    return result


def _parse_params(parser, raw_params):
    params = {}
    for p in raw_params or []:
        if "=" not in p:
            parser.error(f"invalid --param format: '{p}' (expected KEY=VALUE)")
        key, value = p.split("=", 1)
        params[key] = value
    return params


def _build_context(filenames):
    if not filenames:
        return None
    ctx = Context()
    for f in filenames:
        ctx.load(f)
    return ctx


def _write_yaml(data: dict, path: str, label: str):
    if not data:
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"{label} -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Zbx Templar — Zabbix configuration generator")
    parser.add_argument("module", help="Path to a Python module (.py) with TemplarModule/DecreeModule subclass(es)")
    parser.add_argument("-o", "--output", help="Output YAML file path (all content combined)")
    parser.add_argument("--templates-output", help="Output YAML for templates only")
    parser.add_argument("--hosts-output", help="Output YAML for hosts only")
    parser.add_argument("--user-groups-output", help="Output YAML for user groups only")
    parser.add_argument("--users-output", help="Output YAML for users only")
    parser.add_argument("--actions-output", help="Output YAML for actions only")
    parser.add_argument("--encryption-output", help="Output YAML for encryption only")
    parser.add_argument("--namespace", help="UUID namespace for deterministic ID generation")
    parser.add_argument("--context", action="append", metavar="FILE",
                        help="Context YAML for module lookups: zabbix_export, set_macro, decree snippets (repeatable)")
    parser.add_argument("--param", action="append", metavar="KEY=VALUE",
                        help="Parameter passed to the module constructor (repeatable)")
    args = parser.parse_args()

    has_output = (args.output or args.templates_output or args.hosts_output
                  or args.user_groups_output or args.users_output or args.actions_output
                  or args.encryption_output)
    if not has_output:
        parser.error("at least one output is required: -o, --templates-output, --hosts-output, "
                      "--user-groups-output, --users-output, --actions-output, or --encryption-output")

    if args.namespace:
        set_uuid_namespace(args.namespace)

    params = _parse_params(parser, args.param)
    context = _build_context(args.context)

    modules = load_module(args.module, params=params or None, context=context)
    if not modules:
        print(f"No TemplarModule/DecreeModule subclasses found in {args.module}")
        return 1

    for name, mod in modules.items():
        if isinstance(mod, TemplarModule):
            if args.output:
                _write_yaml(mod.to_export(), args.output, name)
            if args.templates_output:
                _write_yaml(mod.export_templates(), args.templates_output, f"{name} [templates]")
            if args.hosts_output:
                _write_yaml(mod.export_hosts(), args.hosts_output, f"{name} [hosts]")

        if isinstance(mod, DecreeModule):
            if args.output:
                _write_yaml(mod.to_export(), args.output, name)
            if args.user_groups_output:
                _write_yaml(mod.export_user_groups(), args.user_groups_output, f"{name} [user_groups]")
            if args.users_output:
                _write_yaml(mod.export_users(), args.users_output, f"{name} [users]")
            if args.actions_output:
                _write_yaml(mod.export_actions(), args.actions_output, f"{name} [actions]")
            if args.encryption_output:
                _write_yaml(mod.export_encryption(), args.encryption_output, f"{name} [encryption]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())