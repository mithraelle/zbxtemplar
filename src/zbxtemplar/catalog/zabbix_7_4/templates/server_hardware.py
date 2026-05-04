"""Auto-generated. Templates/Server hardware."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'server_hardware.json').read_text(encoding="utf-8"))
}


class ServerHardware:
    """Templates/Server hardware"""
    Chassis_by_IPMI: Template = _loaded['Chassis by IPMI']
    Cisco_UCS_Manager_by_SNMP: Template = _loaded['Cisco UCS Manager by SNMP']
    Cisco_UCS_by_SNMP: Template = _loaded['Cisco UCS by SNMP']
    DELL_PowerEdge_R660_by_HTTP: Template = _loaded['DELL PowerEdge R660 by HTTP']
    DELL_PowerEdge_R660_by_SNMP: Template = _loaded['DELL PowerEdge R660 by SNMP']
    DELL_PowerEdge_R720_by_HTTP: Template = _loaded['DELL PowerEdge R720 by HTTP']
    DELL_PowerEdge_R720_by_SNMP: Template = _loaded['DELL PowerEdge R720 by SNMP']
    DELL_PowerEdge_R740_by_HTTP: Template = _loaded['DELL PowerEdge R740 by HTTP']
    DELL_PowerEdge_R740_by_SNMP: Template = _loaded['DELL PowerEdge R740 by SNMP']
    DELL_PowerEdge_R750_by_HTTP: Template = _loaded['DELL PowerEdge R750 by HTTP']
    DELL_PowerEdge_R750_by_SNMP: Template = _loaded['DELL PowerEdge R750 by SNMP']
    DELL_PowerEdge_R820_by_HTTP: Template = _loaded['DELL PowerEdge R820 by HTTP']
    DELL_PowerEdge_R820_by_SNMP: Template = _loaded['DELL PowerEdge R820 by SNMP']
    DELL_PowerEdge_R840_by_HTTP: Template = _loaded['DELL PowerEdge R840 by HTTP']
    DELL_PowerEdge_R840_by_SNMP: Template = _loaded['DELL PowerEdge R840 by SNMP']
    Dell_iDRAC_by_SNMP: Template = _loaded['Dell iDRAC by SNMP']
    HP_iLO_by_SNMP: Template = _loaded['HP iLO by SNMP']
    HPE_ProLiant_BL460_by_SNMP: Template = _loaded['HPE ProLiant BL460 by SNMP']
    HPE_ProLiant_BL920_by_SNMP: Template = _loaded['HPE ProLiant BL920 by SNMP']
    HPE_ProLiant_DL360_by_SNMP: Template = _loaded['HPE ProLiant DL360 by SNMP']
    HPE_ProLiant_DL380_by_SNMP: Template = _loaded['HPE ProLiant DL380 by SNMP']
    HPE_Synergy_by_HTTP: Template = _loaded['HPE Synergy by HTTP']
    HPE_iLO_by_HTTP: Template = _loaded['HPE iLO by HTTP']
    IBM_IMM_by_SNMP: Template = _loaded['IBM IMM by SNMP']
    Intel_SR1530_IPMI: Template = _loaded['Intel SR1530 IPMI']
    Intel_SR1630_IPMI: Template = _loaded['Intel SR1630 IPMI']
    SMART_by_Zabbix_agent_2: Template = _loaded['SMART by Zabbix agent 2']
    SMART_by_Zabbix_agent_2_active: Template = _loaded['SMART by Zabbix agent 2 active']
    Supermicro_Aten_by_SNMP: Template = _loaded['Supermicro Aten by SNMP']
