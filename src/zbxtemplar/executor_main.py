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
from zbxtemplar.dicts.ZabbixExport import ZabbixExport
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.ScrollExecutor import ScrollExecutor
from zbxtemplar.executor.operations.ImportOperation import ImportOperation
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
        raise ValueError("Auth required: --token or --password (or ZABBIX_TOKEN / ZABBIX_PASSWORD env)")

    if token:
        return ZabbixAPI(url=url, token=token)
    return ZabbixAPI(url=url, user=user, password=password)


def _set_schema_base(base_dir=None):
    Schema._base_dir = base_dir
    Schema._resolve_envs = True


def _set_super_admin(args, api):
    data = {}
    if args.new_password:
        data["password"] = args.new_password
    if args.username:
        data["username"] = args.username
    current = getattr(args, "current_password", None) or getattr(args, "password", None)
    if current:
        data["current_password"] = current
    _set_schema_base()
    scroll = Scroll.from_data({"set_super_admin": data})
    ScrollExecutor(scroll, api).execute(only_action="set_super_admin")


def _set_macro(args, api):
    _set_schema_base()
    scroll = Scroll.from_data({"set_macro": {"name": args.name, "value": args.value, "type": args.type}})
    ScrollExecutor(scroll, api).execute(only_action="set_macro")


def _apply(args, api):
    path = os.path.abspath(args.file)
    base_dir = os.path.dirname(path)
    _set_schema_base(base_dir)

    if args.from_action and args.only_action:
        raise ValueError("Cannot use both --from-action and --only-action")

    entity_cls = Schema.detect_type(path)

    executor_map = {
        ZabbixExport: ImportOperation,
        Scroll: ScrollExecutor,
        Decree: DecreeExecutor,
    }

    if entity_cls not in executor_map:
        raise ValueError(f"Unsupported file type: {entity_cls.__name__}")

    executor_cls = executor_map[entity_cls]
    has_stages = hasattr(executor_cls, "_ACTIONS")

    if args.from_action or args.only_action:
        if not has_stages:
            raise ValueError(f"--from-action/--only-action not supported for {executor_cls.__name__}")
        valid_actions = [stage.action for stage in executor_cls._ACTIONS]
        val = args.from_action or args.only_action
        if val not in valid_actions:
            raise ValueError(f"Unknown action: {val}. Valid: {', '.join(valid_actions)}")

    if entity_cls == ZabbixExport:
        executor = ImportOperation([path], api, base_dir)
        executor.execute()
    else:
        executor = executor_cls(entity_cls.from_file(path), api, base_dir)
        executor.execute(from_action=args.from_action, only_action=args.only_action)


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

    mac = sub.add_parser("set_macro", parents=[conn], help="Set a global macro by name")
    mac.add_argument("name", help="Macro name")
    mac.add_argument("value", help="Macro value")
    mac.add_argument("--type", choices=["text", "secret", "vault"], default="text")
    mac.set_defaults(func=_set_macro)

    app = sub.add_parser("apply", parents=[conn], help="Apply a Zabbix export, scroll, or decree file")
    app.add_argument("file", help="Path to YAML file (auto-detected: zabbix export, scroll, or decree)")
    app.add_argument("--from-action", help="Start execution from this action (scroll and decree only)")
    app.add_argument("--only-action", help="Execute only this action (scroll and decree only)")
    app.set_defaults(func=_apply)

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
    except KeyboardInterrupt:
        log.run_end(run_id, result="failed", actions=log._actions, duration_ms=int((time.time() - t0) * 1000))
        print("Error: Execution interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        log.run_end(run_id, result="failed", actions=log._actions, duration_ms=int((time.time() - t0) * 1000))
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())