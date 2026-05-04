"""Auto-generated. Templates/Video surveillance."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'video_surveillance.json').read_text(encoding="utf-8"))
}


class VideoSurveillance:
    """Templates/Video surveillance"""
    Hikvision_camera_by_HTTP: Template = _loaded['Hikvision camera by HTTP']
