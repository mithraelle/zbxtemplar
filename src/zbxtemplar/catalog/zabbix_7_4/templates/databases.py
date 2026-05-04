"""Auto-generated. Templates/Databases."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'databases.json').read_text(encoding="utf-8"))
}


class Databases:
    """Templates/Databases"""
    Apache_Cassandra_by_JMX: Template = _loaded['Apache Cassandra by JMX']
    ClickHouse_by_HTTP: Template = _loaded['ClickHouse by HTTP']
    CockroachDB_by_HTTP: Template = _loaded['CockroachDB by HTTP']
    GridGain_by_JMX: Template = _loaded['GridGain by JMX']
    Ignite_by_JMX: Template = _loaded['Ignite by JMX']
    MSSQL_by_ODBC: Template = _loaded['MSSQL by ODBC']
    MSSQL_by_Zabbix_agent_2: Template = _loaded['MSSQL by Zabbix agent 2']
    MongoDB_cluster_by_Zabbix_agent_2: Template = _loaded['MongoDB cluster by Zabbix agent 2']
    MongoDB_node_by_Zabbix_agent_2: Template = _loaded['MongoDB node by Zabbix agent 2']
    MySQL_by_ODBC: Template = _loaded['MySQL by ODBC']
    MySQL_by_Zabbix_agent: Template = _loaded['MySQL by Zabbix agent']
    MySQL_by_Zabbix_agent_2: Template = _loaded['MySQL by Zabbix agent 2']
    MySQL_by_Zabbix_agent_2_active: Template = _loaded['MySQL by Zabbix agent 2 active']
    MySQL_by_Zabbix_agent_active: Template = _loaded['MySQL by Zabbix agent active']
    Oracle_by_ODBC: Template = _loaded['Oracle by ODBC']
    Oracle_by_Zabbix_agent_2: Template = _loaded['Oracle by Zabbix agent 2']
    PostgreSQL_by_ODBC: Template = _loaded['PostgreSQL by ODBC']
    PostgreSQL_by_Zabbix_agent: Template = _loaded['PostgreSQL by Zabbix agent']
    PostgreSQL_by_Zabbix_agent_2: Template = _loaded['PostgreSQL by Zabbix agent 2']
    PostgreSQL_by_Zabbix_agent_2_active: Template = _loaded['PostgreSQL by Zabbix agent 2 active']
    PostgreSQL_by_Zabbix_agent_active: Template = _loaded['PostgreSQL by Zabbix agent active']
    Redis_by_Zabbix_agent_2: Template = _loaded['Redis by Zabbix agent 2']
    TiDB_PD_by_HTTP: Template = _loaded['TiDB PD by HTTP']
    TiDB_TiKV_by_HTTP: Template = _loaded['TiDB TiKV by HTTP']
    TiDB_by_HTTP: Template = _loaded['TiDB by HTTP']
    YugabyteDB_Cluster_by_HTTP: Template = _loaded['YugabyteDB Cluster by HTTP']
    YugabyteDB_by_HTTP: Template = _loaded['YugabyteDB by HTTP']
