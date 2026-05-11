"""Refresh all templates from a Zabbix server using configuration.export.

After pulling, dumps templates grouped by their ``Templates/XXX`` template group
into ``src/zbxtemplar/catalog/zabbix_7_4/templates/data/<basename>.json`` and
regenerates the package ``__init__.py`` exposing template names for IDE
autocomplete.

Usage:
    python scripts/refresh_catalog.py [--reset]
"""
import argparse
import json
import re
from pathlib import Path

from zabbix_utils import ZabbixAPI

import integration_test as it
from zbxtemplar.modules import APIContext


CATALOG = Path(__file__).resolve().parents[1] / "src" / "zbxtemplar" / "catalog" / "zabbix_7_4" / "templates"


def _ident(s: str, lowercase: bool = False) -> str:
    pattern = r"[^a-z0-9]+" if lowercase else r"[^A-Za-z0-9]+"
    out = re.sub(pattern, "_", s.lower() if lowercase else s).strip("_")
    if out and out[0].isdigit():
        out = "_" + out
    return out


def _pascal(s: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", s) if p]
    out = "".join(p[:1].upper() + p[1:] for p in parts)
    if out and out[0].isdigit():
        out = "_" + out
    return out


def dump_catalog(ctx: APIContext) -> None:
    data_dir = CATALOG / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for f in data_dir.glob("*.json"):
        f.unlink()
    for f in CATALOG.glob("*.py"):
        f.unlink()

    groups: dict[str, list] = {}
    for t in ctx._templates.values():
        for g in t.groups:
            if not g.name.startswith("Templates/"):
                continue
            xxx = g.name[len("Templates/"):]
            if not xxx:
                continue
            groups.setdefault(xxx, []).append(t)

    init_lines = [
        '"""Auto-generated catalog of Zabbix templates.',
        '',
        'Run `python scripts/refresh_catalog.py` to refresh.',
        '"""',
    ]

    for xxx in sorted(groups):
        cls_name = _pascal(xxx)
        basename = _ident(xxx, lowercase=True)
        templates = sorted(groups[xxx], key=lambda x: x.name)

        (data_dir / f"{basename}.json").write_text(
            json.dumps([t.to_dict() for t in templates], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        mod_lines = [
            f'"""Auto-generated. Templates/{xxx}."""',
            'import json',
            'from pathlib import Path',
            '',
            'from zbxtemplar.zabbix.Template import Template',
            '',
            '_loaded = {',
            '    t["name"]: Template.from_dict(t)',
            f'    for t in json.loads((Path(__file__).parent / "data" / {basename + ".json"!r}).read_text(encoding="utf-8"))',
            '}',
            '',
            '',
            f'class {cls_name}:',
            f'    """Templates/{xxx}"""',
        ]
        for t in templates:
            mod_lines.append(f'    {_ident(t.name)}: Template = _loaded[{t.name!r}]')
        mod_lines.append('')

        (CATALOG / f"{basename}.py").write_text("\n".join(mod_lines), encoding="utf-8")
        init_lines.append(
            f'from zbxtemplar.catalog.zabbix_7_4.templates.{basename} import {cls_name} as {cls_name}'
        )
    init_lines.append('')

    (CATALOG / "__init__.py").write_text("\n".join(init_lines), encoding="utf-8")
    entries = sum(len(v) for v in groups.values())
    unique = len({t.name for ts in groups.values() for t in ts})
    print(f"Dumped {unique} unique template(s) ({entries} entries) across {len(groups)} group(s) to {CATALOG}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Rerun docker setup from scripts/integration_test.py before pulling",
    )
    args = parser.parse_args()

    if args.reset:
        it.docker_up()
        it.wait_zabbix()

    api = ZabbixAPI(url=it.ZBX_URL, user="Admin", password="zabbix")
    ctx = APIContext(api)
    ctx.pull_templates()

    print(f"Pulled {len(ctx._templates)} template(s)")
    dump_catalog(ctx)


if __name__ == "__main__":
    main()