import json
from dataclasses import dataclass
from enum import Enum


class DiffKind(Enum):
    CHANGED = "changed"
    ADDED = "added"
    MISSING = "missing"
    TYPE_MISMATCH = "type_mismatch"


@dataclass
class Diff:
    path: str    # dot-separated: "user_group.Operations.gui_access"
    local: str | list[str] | None   # value from Context (None when only on the server)
    remote: str | list[str] | None  # value from APIContext (None when only in the files)


class Inquest:
    def __init__(self, files: list[str]):
        from zbxtemplar.modules import Context
        self._ctx = Context()
        self._api_ctx = None
        for f in files:
            self._ctx.load(f)

    def check(self, comparator, api) -> list[Diff]:
        from zbxtemplar.modules import APIContext
        self._api_ctx = APIContext.from_context(self._ctx, api)
        return comparator.compare(self._ctx, self._api_ctx)

    def checked(self, comparator) -> list[tuple[str, str]]:
        return comparator.checked(self._ctx, self._api_ctx)


_ANSI = {"g": "\033[32m", "y": "\033[33m", "r": "\033[31m", "dim": "\033[2m", "reset": "\033[0m"}
_NO_ANSI = {k: "" for k in _ANSI}


def _entity_root(diff: Diff) -> str:
    parts = diff.path.split(".")
    if parts[0] == "saml":
        return "saml"
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else parts[0]


def _has_issues(label: str, name: str, diffs: list[Diff]) -> bool:
    if not name:  # saml-style top-level entity
        return any(d.path == label or d.path.startswith(f"{label}.") for d in diffs)
    prefix = f"{label}.{name}"
    for d in diffs:
        if d.path == prefix or d.path.startswith(f"{prefix}."):
            return True
        if d.path == label and isinstance(d.local, list) and name in d.local:
            return True
    return False


def render(
    diffs: list[Diff],
    *,
    target: str,
    comparator: str,
    color: bool = False,
    checked: list[tuple[str, str]] | None = None,
) -> str:
    """Format a comparator result as a human-readable report.

    When ``checked`` is given, entities with no diffs are listed as OK.
    """
    c = _ANSI if color else _NO_ANSI

    def status(tag: str, col: str, label: str, name: str = "") -> str:
        suffix = f"  {name}" if name else ""
        return f"  {col}{tag:<6}{c['reset']} {label:<16}{suffix}"

    def fmt_value(v) -> str:
        s = json.dumps(v, default=str, sort_keys=False)
        if len(s) <= 80:
            return s
        return "\n        " + json.dumps(v, default=str, indent=2).replace("\n", "\n        ")

    lines = [f"\nChecking declared state against {target} ({comparator})"]

    by_entity: dict[str, list[Diff]] = {}
    for d in diffs:
        by_entity.setdefault(_entity_root(d), []).append(d)

    if diffs:
        n_d, n_e = len(diffs), len(by_entity)
        lines.append(
            f"  {n_d} diff{'s' if n_d != 1 else ''} across "
            f"{n_e} entit{'ies' if n_e != 1 else 'y'}"
        )
    elif not checked:
        lines.append("  no diffs")
        lines.append("")
        return "\n".join(lines)
    else:
        lines.append("  no diffs")
    lines.append("")

    for root, entity_diffs in by_entity.items():
        if "." not in root and root != "saml":
            for d in entity_diffs:
                if isinstance(d.local, list):
                    for n in d.local:
                        lines.append(status("MISS", c["r"], root, n))
                if isinstance(d.remote, list):
                    for n in d.remote:
                        lines.append(status("EXTRA", c["g"], root, n))
            continue

        parts = root.split(".", 1)
        label, name = parts[0], parts[1] if len(parts) > 1 else ""
        if any(d.path == root and d.remote is None for d in entity_diffs):
            lines.append(status("MISS", c["r"], label, name))
            continue

        lines.append(status("DIFF", c["y"], label, name))
        for d in entity_diffs:
            rel = d.path[len(root):].lstrip(".")
            if isinstance(d.local, list) and d.remote is None:
                lines.append(f"      {c['r']}- {rel}{c['reset']}: {fmt_value(d.local)}")
            elif isinstance(d.remote, list) and d.local is None:
                lines.append(f"      {c['g']}+ {rel}{c['reset']}: {fmt_value(d.remote)}")
            else:
                lines.append(f"      {c['y']}~ {rel}{c['reset']}:")
                lines.append(f"        {c['dim']}local:{c['reset']}  {fmt_value(d.local)}")
                lines.append(f"        {c['dim']}remote:{c['reset']} {fmt_value(d.remote)}")

    if checked:
        for label, name in checked:
            if not _has_issues(label, name, diffs):
                lines.append(status("OK", c["g"], label, name))

    lines.append("")
    lines.append(
        f"  {c['dim']}Legend:{c['reset']}  "
        f"{c['g']}OK{c['reset']}=match  "
        f"{c['y']}DIFF{c['reset']}=fields differ  "
        f"{c['r']}MISS{c['reset']}=not found on remote   "
        f"{c['dim']}|{c['reset']}  "
        f"{c['g']}+ key{c['reset']}=only on remote  "
        f"{c['r']}- key{c['reset']}=only on local  "
        f"{c['y']}~ key{c['reset']}=value differs"
    )
    lines.append("")
    return "\n".join(lines)