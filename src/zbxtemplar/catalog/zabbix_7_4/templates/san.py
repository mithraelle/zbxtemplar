"""Auto-generated. Templates/SAN."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'san.json').read_text(encoding="utf-8"))
}


class SAN:
    """Templates/SAN"""
    HPE_MSA_2040_Storage_by_HTTP: Template = _loaded['HPE MSA 2040 Storage by HTTP']
    HPE_MSA_2060_Storage_by_HTTP: Template = _loaded['HPE MSA 2060 Storage by HTTP']
    HPE_Primera_by_HTTP: Template = _loaded['HPE Primera by HTTP']
    Huawei_OceanStor_5300_V5_by_SNMP: Template = _loaded['Huawei OceanStor 5300 V5 by SNMP']
    Huawei_OceanStor_Dorado_by_SNMP: Template = _loaded['Huawei OceanStor Dorado by SNMP']
    NetApp_AFF_A700_by_HTTP: Template = _loaded['NetApp AFF A700 by HTTP']
    NetApp_FAS3220_by_SNMP: Template = _loaded['NetApp FAS3220 by SNMP']
    Pure_Storage_FlashArray_v1_by_HTTP: Template = _loaded['Pure Storage FlashArray v1 by HTTP']
    Pure_Storage_FlashArray_v2_by_HTTP: Template = _loaded['Pure Storage FlashArray v2 by HTTP']
