"""Zbx Templar Inquest — compare local YAML files against live Zabbix state."""
import argparse
import json
import os
import sys
from urllib.parse import urlparse

from zabbix_utils import ZabbixAPI

from zbxtemplar.inquest import Diff, Inquest, RawDiff, SchemaDiff, render


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


def _target_host(args) -> str:
    url = args.url or os.environ.get("ZABBIX_URL", "http://localhost")
    return urlparse(url).netloc or url


def _print_json(diffs: list[Diff]) -> None:
    for diff in diffs:
        entry: dict = {"path": diff.path, "local": diff.local, "remote": diff.remote}
        print(json.dumps(entry, default=str))


def _emit_error(args, exc: BaseException) -> None:
    msg = f"{type(exc).__name__}: {exc}"
    if getattr(args, "json", False):
        print(json.dumps({"event": "error", "message": msg}))
    else:
        print(f"error: {msg}", file=sys.stderr)


def _run(args, comparator, comparator_name: str) -> int:
    try:
        api = _make_api(args)
        target = _target_host(args)
        inquest = Inquest(args.files)
        diffs = inquest.check(comparator, api)
    except Exception as e:
        _emit_error(args, e)
        return 2

    try:
        if args.json:
            _print_json(diffs)
        else:
            checked = inquest.checked(comparator) if comparator_name == "raw" else None
            print(render(
                diffs,
                target=target,
                comparator=comparator_name,
                color=sys.stdout.isatty(),
                checked=checked,
            ))
    except Exception as e:
        _emit_error(args, e)
        return 2

    return 1 if diffs else 0


def cmd_raw(args) -> int:
    return _run(args, RawDiff(), "raw")


def cmd_schema(args) -> int:
    return _run(args, SchemaDiff(), "schema")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zbxtemplar-inquest",
        description="Compare local YAML decree files against live Zabbix state",
        usage="%(prog)s [--url URL] [--token TOKEN] [--user USER] [--password PASSWORD] {raw,schema} file [file ...]",
    )
    parser.add_argument("--url", help="Zabbix URL (default: http://localhost, or ZABBIX_URL env)")
    parser.add_argument("--token", help="API token (or ZABBIX_TOKEN env)")
    parser.add_argument("--user", help="Username (default: Admin, or ZABBIX_USER env)")
    parser.add_argument("--password", help="Password (or ZABBIX_PASSWORD env)")

    sub = parser.add_subparsers(dest="command")

    raw = sub.add_parser("raw", help="Literal field-by-field diff of declared vs deployed state")
    raw.add_argument("files", nargs="+", help="YAML file(s) to load (any format: scroll, decree, zabbix export)")
    raw.add_argument("--json", action="store_true", help="Machine-friendly JSON Lines output")
    raw.set_defaults(func=cmd_raw)

    schema = sub.add_parser("schema", help="Schema-aware diff: honors per-field IGNORE / SubsetBy policies")
    schema.add_argument("files", nargs="+", help="YAML file(s) to load (any format: scroll, decree, zabbix export)")
    schema.add_argument("--json", action="store_true", help="Machine-friendly JSON Lines output")
    schema.set_defaults(func=cmd_schema)

    return parser


def main() -> int:
    try:
        parser = _build_parser()
        args = parser.parse_args()
        if not hasattr(args, "func"):
            parser.print_help()
            return 1
        return args.func(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except SystemExit:
        raise
    except BaseException as e:
        _emit_error(argparse.Namespace(json=("--json" in sys.argv)), e)
        return 2


if __name__ == "__main__":
    sys.exit(main())