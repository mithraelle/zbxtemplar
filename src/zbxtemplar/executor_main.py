import argparse
import os
import secrets
import sys
import time
from datetime import datetime, timezone

from zabbix_utils import ZabbixAPI

from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.dicts.Schema import Schema
from zbxtemplar.dicts.Scroll import Scroll
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.ScrollExecutor import ScrollExecutor
from zbxtemplar.executor.log import log


def _make_run_id():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(2)}"


def _make_api(args):
    url = args.url or os.environ.get("ZABBIX_URL", "http://localhost")
    token = getattr(args, "token", None) or os.environ.get("ZABBIX_TOKEN")
    password = getattr(args, "password", None) or os.environ.get("ZABBIX_PASSWORD")
    user = getattr(args, "user", None) or os.environ.get("ZABBIX_USER", "Admin")

    if not token and not password:
        raise SystemExit("Auth required: --token or --password (or ZABBIX_TOKEN / ZABBIX_PASSWORD env)")

    if token:
        return ZabbixAPI(url=url, token=token)
    return ZabbixAPI(url=url, user=user, password=password)


def _set_schema_base(base_dir=None):
    Schema._base_dir = base_dir
    Schema._resolve_envs = True


def _run_scroll_action(name, data, api, base_dir=None):
    _set_schema_base(base_dir)
    scroll = Scroll.from_data({name: data})
    ScrollExecutor(scroll, api, base_dir).execute(only_action=name)


def _set_super_admin(args, api):
    data = {}
    if args.new_password:
        data["password"] = args.new_password
    if args.username:
        data["username"] = args.username
    current = getattr(args, "current_password", None) or getattr(args, "password", None)
    if current:
        data["current_password"] = current
    _run_scroll_action("set_super_admin", data, api)


def _set_macro(args, api):
    if args.value is not None:
        payload = {"name": args.name_or_file, "value": args.value, "type": args.type}
        _run_scroll_action("set_macro", payload, api)
    else:
        macro_path = os.path.abspath(args.name_or_file)
        base_dir = os.path.dirname(macro_path)
        _run_scroll_action("set_macro", macro_path, api, base_dir)


def _apply(args, api):
    yaml_path = os.path.abspath(args.yaml_file)
    base_dir = os.path.dirname(yaml_path)
    _run_scroll_action("apply", [yaml_path], api, base_dir)


def _decree(args, api):
    decree_path = os.path.abspath(args.decree_file)
    base_dir = os.path.dirname(decree_path)
    _set_schema_base(base_dir)
    decree = Decree.from_file(decree_path)
    DecreeExecutor(decree, api, base_dir).execute()


def _add_user(args, api):
    user_path = os.path.abspath(args.user_file)
    base_dir = os.path.dirname(user_path)
    _set_schema_base(base_dir)
    data = Decree._load_yaml(user_path)
    if not (isinstance(data, dict) and "add_user" in data):
        data = {"add_user": data}
    decree = Decree.from_data(data)
    DecreeExecutor(decree, api, base_dir).execute(only_action="add_user")


def _scroll(args, api):
    scroll_path = os.path.abspath(args.scroll)
    base_dir = os.path.dirname(scroll_path)
    _set_schema_base(base_dir)
    scroll = Scroll.from_file(scroll_path)
    ScrollExecutor(scroll, api, base_dir).execute(from_action=args.from_action, only_action=args.only_action)


def _build_parser():
    conn = argparse.ArgumentParser(add_help=False)
    conn.add_argument("--url", help="Zabbix URL (default: http://localhost, or ZABBIX_URL env)")
    conn.add_argument("--token", help="API token (or ZABBIX_TOKEN env)")
    conn.add_argument("--user", help="Username (default: Admin, or ZABBIX_USER env)")
    conn.add_argument("--password", help="Password (or ZABBIX_PASSWORD env)")
    conn.add_argument("--json", action="store_true", help="Output logs as JSON lines")

    parser = argparse.ArgumentParser(description="Zbx Templar Executor — apply configuration to Zabbix")
    sub = parser.add_subparsers(dest="command")

    sa = sub.add_parser("set_super_admin", parents=[conn], help="Bootstrap or rotate super admin password")
    sa.add_argument("--new-password", required=True, help="New password")
    sa.add_argument("--current-password", help="Current password (required by Zabbix 7.x for self-update)")
    sa.add_argument("--username", help="New login name for the super admin")
    sa.set_defaults(func=_set_super_admin)

    mac = sub.add_parser("set_macro", parents=[conn], help="Set global macros (inline or from file)")
    mac.add_argument("name_or_file", help="Macro name or path to YAML file")
    mac.add_argument("value", nargs="?", help="Macro value (when setting a single macro)")
    mac.add_argument("--type", choices=["text", "secret", "vault"], default="text")
    mac.set_defaults(func=_set_macro)

    app = sub.add_parser("apply", parents=[conn], help="Import Zabbix-native YAML")
    app.add_argument("yaml_file", help="Path to Zabbix-native YAML file")
    app.set_defaults(func=_apply)

    dec = sub.add_parser("decree", parents=[conn], help="Apply state configuration (user groups, actions, SAML)")
    dec.add_argument("decree_file", help="Path to decree YAML file")
    dec.set_defaults(func=_decree)

    usr = sub.add_parser("add_user", parents=[conn], help="Create service or special users")
    usr.add_argument("user_file", help="Path to user definition YAML file")
    usr.set_defaults(func=_add_user)

    scr = sub.add_parser("scroll", parents=[conn], help="Execute a deployment scroll")
    scr.add_argument("scroll", help="Path to scroll YAML file")
    scr.add_argument("--from-action", help="Start execution from this action")
    scr.add_argument("--only-action", help="Execute only this action")
    scr.set_defaults(func=_scroll)

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    log.configure(json_output=getattr(args, "json", False))

    run_id = _make_run_id()
    url = args.url or os.environ.get("ZABBIX_URL", "http://localhost")
    token = getattr(args, "token", None) or os.environ.get("ZABBIX_TOKEN")
    auth = "token" if token else "password"
    log.run_start(run_id, target=url, auth=auth)

    t0 = time.time()
    try:
        args.func(args, _make_api(args))
        log.run_end(run_id, result="ok", actions=log._actions, duration_ms=int((time.time() - t0) * 1000))
        return 0
    except Exception as e:
        log.run_end(run_id, result="failed", actions=log._actions, duration_ms=int((time.time() - t0) * 1000))
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
