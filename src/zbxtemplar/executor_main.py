import argparse
import os

from zabbix_utils import ZabbixAPI

from zbxtemplar.executor import Executor


def _make_api(args):
    url = args.url or os.environ.get("ZABBIX_URL", "http://localhost")
    token = args.user_or_token or os.environ.get("ZABBIX_TOKEN")
    password = args.password or os.environ.get("ZABBIX_PASSWORD")
    user = os.environ.get("ZABBIX_USER", "Admin")

    if not token and not password:
        raise SystemExit("Auth required: --token or --password (or ZABBIX_TOKEN / ZABBIX_PASSWORD env)")

    if token:
        return ZabbixAPI(url=url, token=token)
    else:
        return ZabbixAPI(url=url, user=user, password=password)


def _cmd_set_super_admin(args):
    api = _make_api(args)
    executor = Executor(api)
    executor.set_super_admin(args.new_password)
    return 0


def _cmd_set_macro(args):
    api = _make_api(args)
    executor = Executor(api)
    if args.value is not None:
        executor.set_macro({"name": args.name_or_file, "value": args.value, "type": args.type})
    else:
        with open(args.name_or_file) as f:
            import yaml
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or "set_macro" not in data:
            raise SystemExit(f"Invalid macro file: expected a YAML file with a 'set_macro' key")
        executor.set_macro(data["set_macro"])
    return 0


def _cmd_apply(args):
    api = _make_api(args)
    executor = Executor(api)
    executor.apply(args.yaml_file)
    return 0


def _cmd_decree(args):
    api = _make_api(args)
    executor = Executor(api)
    executor.decree(args.decree_file)
    return 0


def _cmd_add_user(args):
    api = _make_api(args)
    executor = Executor(api)
    with open(args.user_file) as f:
        import yaml
        data = yaml.safe_load(f)
    executor.add_user(data["add_user"])
    return 0


def _cmd_scroll(args):
    api = _make_api(args)
    executor = Executor(api)
    executor.run_scroll(args.scroll, from_stage=args.from_stage, only_stage=args.only_stage)
    return 0


def _add_connection_args(parser):
    parser.add_argument("--url", help="Zabbix URL (default: http://localhost, or ZABBIX_URL env)")
    parser.add_argument("--token", dest="user_or_token", help="API token (or ZABBIX_TOKEN env)")
    parser.add_argument("--user", dest="user_or_token", help="Username (default: Admin, or ZABBIX_USER env)")
    parser.add_argument("--password", help="Password (or ZABBIX_PASSWORD env)")


def main():
    parser = argparse.ArgumentParser(description="Zbx Templar Executor — apply configuration to Zabbix")
    sub = parser.add_subparsers()

    sa = sub.add_parser("set_super_admin", help="Bootstrap or rotate super admin password")
    sa.add_argument("--new-password", required=True, help="New password")
    _add_connection_args(sa)
    sa.set_defaults(func=_cmd_set_super_admin)

    mac = sub.add_parser("set_macro", help="Set global macros (inline or from file)")
    mac.add_argument("name_or_file", help="Macro name or path to YAML file")
    mac.add_argument("value", nargs="?", help="Macro value (when setting a single macro)")
    mac.add_argument("--type", choices=["text", "secret", "vault"], default="text")
    _add_connection_args(mac)
    mac.set_defaults(func=_cmd_set_macro)

    app = sub.add_parser("apply", help="Import Zabbix-native YAML")
    app.add_argument("yaml_file", help="Path to Zabbix-native YAML file")
    _add_connection_args(app)
    app.set_defaults(func=_cmd_apply)

    dec = sub.add_parser("decree", help="Apply state configuration (user groups, actions, SAML)")
    dec.add_argument("decree_file", help="Path to decree YAML file")
    _add_connection_args(dec)
    dec.set_defaults(func=_cmd_decree)

    usr = sub.add_parser("add_user", help="Create service or special users")
    usr.add_argument("user_file", help="Path to user definition YAML file")
    _add_connection_args(usr)
    usr.set_defaults(func=_cmd_add_user)

    scr = sub.add_parser("scroll", help="Execute a deployment scroll")
    scr.add_argument("scroll", help="Path to scroll YAML file")
    scr.add_argument("--from-stage", help="Start execution from this stage")
    scr.add_argument("--only-stage", help="Execute only this stage")
    _add_connection_args(scr)
    scr.set_defaults(func=_cmd_scroll)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
