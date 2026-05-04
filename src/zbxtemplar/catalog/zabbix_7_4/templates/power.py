"""Auto-generated. Templates/Power."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'power.json').read_text(encoding="utf-8"))
}


class Power:
    """Templates/Power"""
    APC_Smart_UPS_2200_RM_by_SNMP: Template = _loaded['APC Smart-UPS 2200 RM by SNMP']
    APC_Smart_UPS_3000_XLM_by_SNMP: Template = _loaded['APC Smart-UPS 3000 XLM by SNMP']
    APC_Smart_UPS_RT_1000_RM_XL_by_SNMP: Template = _loaded['APC Smart-UPS RT 1000 RM XL by SNMP']
    APC_Smart_UPS_RT_1000_XL_by_SNMP: Template = _loaded['APC Smart-UPS RT 1000 XL by SNMP']
    APC_Smart_UPS_SRT_5000_by_SNMP: Template = _loaded['APC Smart-UPS SRT 5000 by SNMP']
    APC_Smart_UPS_SRT_8000_by_SNMP: Template = _loaded['APC Smart-UPS SRT 8000 by SNMP']
    APC_UPS_Galaxy_3500_by_SNMP: Template = _loaded['APC UPS Galaxy 3500 by SNMP']
    APC_UPS_Symmetra_LX_by_SNMP: Template = _loaded['APC UPS Symmetra LX by SNMP']
    APC_UPS_Symmetra_RM_by_SNMP: Template = _loaded['APC UPS Symmetra RM by SNMP']
    APC_UPS_Symmetra_RX_by_SNMP: Template = _loaded['APC UPS Symmetra RX by SNMP']
    APC_UPS_by_SNMP: Template = _loaded['APC UPS by SNMP']
