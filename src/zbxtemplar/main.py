import argparse
import yaml

from zbxtemplar.core.ZbxEntity import set_uuid_namespace
from zbxtemplar.core.TemplarModule import load_module


def _write_yaml(data: dict, path: str, label: str):
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"{label} -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Zbx Templar — Zabbix template generator")
    parser.add_argument("module", help="Path to a Python module (.py) with TemplarModule subclass(es)")
    parser.add_argument("output", nargs="?", help="Output YAML file path (combined templates + hosts)")
    parser.add_argument("--templates-output", help="Output YAML file path for templates only")
    parser.add_argument("--hosts-output", help="Output YAML file path for hosts only")
    parser.add_argument("--namespace", help="UUID namespace for deterministic ID generation")
    args = parser.parse_args()

    if not args.output and not args.templates_output and not args.hosts_output:
        parser.error("at least one output is required: output, --templates-output, or --hosts-output")

    if args.namespace:
        set_uuid_namespace(args.namespace)

    modules = load_module(args.module)
    if not modules:
        print(f"No TemplarModule subclasses found in {args.module}")
        return 1

    for name, mod in modules.items():
        if args.output:
            _write_yaml(mod.to_export(), args.output, name)
        if args.templates_output:
            _write_yaml(mod.export_templates(), args.templates_output, f"{name} [templates]")
        if args.hosts_output:
            _write_yaml(mod.export_hosts(), args.hosts_output, f"{name} [hosts]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())