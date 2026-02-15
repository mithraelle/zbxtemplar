import argparse
import yaml

from zbxtemplar.core.ZbxEntity import set_uuid_namespace, set_template_group
from zbxtemplar.core.TemplarModule import load_module


def main():
    parser = argparse.ArgumentParser(description="Zbx Templar — Zabbix template generator")
    parser.add_argument("module", help="Path to a Python module (.py) with TemplarModule subclass(es)")
    parser.add_argument("output", help="Output YAML file path")
    parser.add_argument("--namespace", help="UUID namespace for deterministic ID generation")
    parser.add_argument("--template-group", help="Default template group name")
    args = parser.parse_args()

    if args.namespace:
        set_uuid_namespace(args.namespace)
    if args.template_group:
        set_template_group(args.template_group)

    modules = load_module(args.module)
    if not modules:
        print(f"No TemplarModule subclasses found in {args.module}")
        return 1

    for name, mod in modules.items():
        export = mod.to_export()
        with open(args.output, "w") as f:
            yaml.dump(export, f, default_flow_style=False, sort_keys=False)
        print(f"{name} -> {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())