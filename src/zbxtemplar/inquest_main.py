"""Zbx Templar Inquest — compare local YAML files against live Zabbix state."""
import argparse
import json
import os
import sys
from urllib.parse import urlparse

from zabbix_utils import ZabbixAPI

from zbxtemplar.inquest import Diff, Inquest, RawDiff, SchemaDiff


_USE_COLOR = sys.stdout.isatty()


def _c(code: str) -> str:
    return code if _USE_COLOR else ""


GREEN  = _c("\033[32m")
YELLOW = _c("\033[33m")
RED    = _c("\033[31m")
DIM    = _c("\033[2m")
RESET  = _c("\033[0m")

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


def _fmt_value(value) -> str:
    s = json.dumps(value, default=str, sort_keys=False)
    if len(s) <= 80:
        return s
    return "\n        " + json.dumps(value, default=str, sort_keys=False, indent=2).replace("\n", "\n        ")


def _print_status(tag: str, color: str, label: str, name: str = "") -> None:
    name_part = f"  {name}" if name else ""
    print(f"  {color}{tag:<6}{RESET} {label:<16}{name_part}")


def _entity_root(diff: Diff) -> str:
    parts = diff.path.split(".")
    if parts[0] == "saml":
        return "saml"
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else parts[0]


def _print_entity_diffs(entity_root: str, diffs: list[Diff]) -> None:
    for diff in diffs:
        rel = diff.path[len(entity_root):].lstrip(".")
        if diff.local is None:
            print(f"      {GREEN}+ {rel}{RESET}: {_fmt_value(diff.remote)}")
        elif diff.remote is None:
            print(f"      {RED}- {rel}{RESET}: {_fmt_value(diff.local)}")
        else:
            print(f"      {YELLOW}~ {rel}{RESET}:")
            print(f"        {DIM}local:{RESET}  {_fmt_value(diff.local)}")
            print(f"        {DIM}remote:{RESET} {_fmt_value(diff.remote)}")


def _print_legend() -> None:
    print()
    print(f"  {DIM}Legend:{RESET}  "
          f"{GREEN}OK{RESET}=match  "
          f"{YELLOW}DIFF{RESET}=fields differ  "
          f"{RED}MISS{RESET}=not found on remote   "
          f"{DIM}|{RESET}  "
          f"{GREEN}+ key{RESET}=only on remote  "
          f"{RED}- key{RESET}=only on local  "
          f"{YELLOW}~ key{RESET}=value differs")


def _print_human(diffs: list[Diff], target: str, comparator: str) -> None:
    print(f"\nChecking declared state against {target} ({comparator})")
    if not diffs:
        print("  no diffs")
        print()
        return

    from collections import defaultdict
    by_entity: dict[str, list[Diff]] = defaultdict(list)
    for diff in diffs:
        by_entity[_entity_root(diff)].append(diff)

    print(f"  {len(diffs)} diff{'s' if len(diffs) != 1 else ''} across {len(by_entity)} entit{'ies' if len(by_entity) != 1 else 'y'}")
    print()

    for root, entity_diffs in by_entity.items():
        parts = root.split(".", 1)
        label, name = parts[0], parts[1] if len(parts) > 1 else ""

        if "." not in root and root != "saml":
            for d in entity_diffs:
                if isinstance(d.local, list):
                    for n in d.local:
                        _print_status("MISS", RED, label, n)
                if isinstance(d.remote, list):
                    for n in d.remote:
                        _print_status("EXTRA", GREEN, label, n)
            continue

        if any(d.path == root and d.remote is None for d in entity_diffs):
            _print_status("MISS", RED, label, name)
        else:
            _print_status("DIFF", YELLOW, label, name)
            _print_entity_diffs(root, entity_diffs)

    _print_legend()
    print()

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
            _print_human(diffs, target, comparator_name)
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