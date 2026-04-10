import argparse
import os
import sys

from zabbix_utils import ZabbixAPI

from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.ScrollExecutor import ScrollExecutor


def _make_api(args):
    url = args.url or os.environ.get("ZABBIX_URL", "http://localhost")
    token = args.user_or_token or os.environ.get("ZABBIX_TOKEN")
    password = args.password or os.environ.get("ZABBIX_PASSWORD")
    user = os.environ.get("ZABBIX_USER", "Admin")

    if not token and not password:
        raise SystemExit("Auth required: --token or --password (or ZABBIX_TOKEN / ZABBIX_PASSWORD env)")

    if token:
        return ZabbixAPI(url=url, token=token)
    return ZabbixAPI(url=url, user=user, password=password)


def _set_macro(args, api):
    if args.value is not None:
        payload = {"name": args.name_or_file, "value": args.value, "type": args.type}
    else:
        payload = args.name_or_file
    ScrollExecutor(api).set_macro(payload)


def _build_parser():
    conn = argparse.ArgumentParser(add_help=False)
    conn.add_argument("--url", help="Zabbix URL (default: http://localhost, or ZABBIX_URL env)")
    conn.add_argument("--token", dest="user_or_token", help="API token (or ZABBIX_TOKEN env)")
    conn.add_argument("--user", dest="user_or_token", help="Username (default: Admin, or ZABBIX_USER env)")
    conn.add_argument("--password", help="Password (or ZABBIX_PASSWORD env)")

    parser = argparse.ArgumentParser(description="Zbx Templar Executor — apply configuration to Zabbix")
    sub = parser.add_subparsers()

    sa = sub.add_parser("set_super_admin", parents=[conn], help="Bootstrap or rotate super admin password")
    sa.add_argument("--new-password", required=True, help="New password")
    sa.set_defaults(func=lambda args, api: ScrollExecutor(api).set_super_admin(args.new_password))

    mac = sub.add_parser("set_macro", parents=[conn], help="Set global macros (inline or from file)")
    mac.add_argument("name_or_file", help="Macro name or path to YAML file")
    mac.add_argument("value", nargs="?", help="Macro value (when setting a single macro)")
    mac.add_argument("--type", choices=["text", "secret", "vault"], default="text")
    mac.set_defaults(func=_set_macro)

    app = sub.add_parser("apply", parents=[conn], help="Import Zabbix-native YAML")
    app.add_argument("yaml_file", help="Path to Zabbix-native YAML file")
    app.set_defaults(func=lambda args, api: ScrollExecutor(api).apply(args.yaml_file))

    dec = sub.add_parser("decree", parents=[conn], help="Apply state configuration (user groups, actions, SAML)")
    dec.add_argument("decree_file", help="Path to decree YAML file")
    dec.set_defaults(func=lambda args, api: DecreeExecutor(api).execute(args.decree_file))

    usr = sub.add_parser("add_user", parents=[conn], help="Create service or special users")
    usr.add_argument("user_file", help="Path to user definition YAML file")
    usr.set_defaults(func=lambda args, api: DecreeExecutor(api).add_user(args.user_file))

    scr = sub.add_parser("scroll", parents=[conn], help="Execute a deployment scroll")
    scr.add_argument("scroll", help="Path to scroll YAML file")
    scr.add_argument("--from-stage", help="Start execution from this stage")
    scr.add_argument("--only-stage", help="Execute only this stage")
    scr.set_defaults(func=lambda args, api: ScrollExecutor(api).run_scroll(
        args.scroll, from_stage=args.from_stage, only_stage=args.only_stage
    ))

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        args.func(args, _make_api(args))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())