"""Auto-generated. Templates/Telephony."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'telephony.json').read_text(encoding="utf-8"))
}


class Telephony:
    """Templates/Telephony"""
    Asterisk_by_HTTP: Template = _loaded['Asterisk by HTTP']
