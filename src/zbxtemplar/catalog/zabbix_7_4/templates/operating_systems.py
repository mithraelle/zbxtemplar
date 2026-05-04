"""Auto-generated. Templates/Operating systems."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'operating_systems.json').read_text(encoding="utf-8"))
}


class OperatingSystems:
    """Templates/Operating systems"""
    AIX_by_Zabbix_agent: Template = _loaded['AIX by Zabbix agent']
    FreeBSD_by_Zabbix_agent: Template = _loaded['FreeBSD by Zabbix agent']
    HP_UX_by_Zabbix_agent: Template = _loaded['HP-UX by Zabbix agent']
    Linux_by_Prom: Template = _loaded['Linux by Prom']
    Linux_by_SNMP: Template = _loaded['Linux by SNMP']
    Linux_by_Zabbix_agent: Template = _loaded['Linux by Zabbix agent']
    Linux_by_Zabbix_agent_active: Template = _loaded['Linux by Zabbix agent active']
    OpenBSD_by_Zabbix_agent: Template = _loaded['OpenBSD by Zabbix agent']
    Solaris_by_Zabbix_agent: Template = _loaded['Solaris by Zabbix agent']
    Stormshield_SNS_by_SNMP: Template = _loaded['Stormshield SNS by SNMP']
    Windows_by_SNMP: Template = _loaded['Windows by SNMP']
    Windows_by_Zabbix_agent: Template = _loaded['Windows by Zabbix agent']
    Windows_by_Zabbix_agent_active: Template = _loaded['Windows by Zabbix agent active']
    macOS_by_Zabbix_agent: Template = _loaded['macOS by Zabbix agent']
