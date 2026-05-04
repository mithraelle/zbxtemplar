"""Auto-generated. Templates/Cloud."""
import json
from pathlib import Path

from zbxtemplar.zabbix.Template import Template

_loaded = {
    t["name"]: Template.from_dict(t)
    for t in json.loads((Path(__file__).parent / "data" / 'cloud.json').read_text(encoding="utf-8"))
}


class Cloud:
    """Templates/Cloud"""
    AWS_Backup_Vault_by_HTTP: Template = _loaded['AWS Backup Vault by HTTP']
    AWS_Cost_Explorer_by_HTTP: Template = _loaded['AWS Cost Explorer by HTTP']
    AWS_EC2_by_HTTP: Template = _loaded['AWS EC2 by HTTP']
    AWS_ECS_Cluster_by_HTTP: Template = _loaded['AWS ECS Cluster by HTTP']
    AWS_ECS_Serverless_Cluster_by_HTTP: Template = _loaded['AWS ECS Serverless Cluster by HTTP']
    AWS_ELB_Application_Load_Balancer_by_HTTP: Template = _loaded['AWS ELB Application Load Balancer by HTTP']
    AWS_ELB_Network_Load_Balancer_by_HTTP: Template = _loaded['AWS ELB Network Load Balancer by HTTP']
    AWS_Lambda_by_HTTP: Template = _loaded['AWS Lambda by HTTP']
    AWS_RDS_instance_by_HTTP: Template = _loaded['AWS RDS instance by HTTP']
    AWS_S3_bucket_by_HTTP: Template = _loaded['AWS S3 bucket by HTTP']
    AWS_by_HTTP: Template = _loaded['AWS by HTTP']
    Azure_Backup_Jobs_by_HTTP: Template = _loaded['Azure Backup Jobs by HTTP']
    Azure_Cosmos_DB_for_MongoDB_by_HTTP: Template = _loaded['Azure Cosmos DB for MongoDB by HTTP']
    Azure_Cost_Management_by_HTTP: Template = _loaded['Azure Cost Management by HTTP']
    Azure_Microsoft_SQL_DTU_Database_by_HTTP: Template = _loaded['Azure Microsoft SQL DTU Database by HTTP']
    Azure_Microsoft_SQL_Database_by_HTTP: Template = _loaded['Azure Microsoft SQL Database by HTTP']
    Azure_Microsoft_SQL_Serverless_Database_by_HTTP: Template = _loaded['Azure Microsoft SQL Serverless Database by HTTP']
    Azure_MySQL_Flexible_Server_by_HTTP: Template = _loaded['Azure MySQL Flexible Server by HTTP']
    Azure_MySQL_Single_Server_by_HTTP: Template = _loaded['Azure MySQL Single Server by HTTP']
    Azure_PostgreSQL_Flexible_Server_by_HTTP: Template = _loaded['Azure PostgreSQL Flexible Server by HTTP']
    Azure_PostgreSQL_Single_Server_by_HTTP: Template = _loaded['Azure PostgreSQL Single Server by HTTP']
    Azure_SQL_Managed_Instance_by_HTTP: Template = _loaded['Azure SQL Managed Instance by HTTP']
    Azure_VM_Scale_Set_by_HTTP: Template = _loaded['Azure VM Scale Set by HTTP']
    Azure_Virtual_Machine_by_HTTP: Template = _loaded['Azure Virtual Machine by HTTP']
    Azure_by_HTTP: Template = _loaded['Azure by HTTP']
    GCP_Cloud_SQL_MSSQL_Replica_by_HTTP: Template = _loaded['GCP Cloud SQL MSSQL Replica by HTTP']
    GCP_Cloud_SQL_MSSQL_by_HTTP: Template = _loaded['GCP Cloud SQL MSSQL by HTTP']
    GCP_Cloud_SQL_MySQL_Replica_by_HTTP: Template = _loaded['GCP Cloud SQL MySQL Replica by HTTP']
    GCP_Cloud_SQL_MySQL_by_HTTP: Template = _loaded['GCP Cloud SQL MySQL by HTTP']
    GCP_Cloud_SQL_PostgreSQL_Replica_by_HTTP: Template = _loaded['GCP Cloud SQL PostgreSQL Replica by HTTP']
    GCP_Cloud_SQL_PostgreSQL_by_HTTP: Template = _loaded['GCP Cloud SQL PostgreSQL by HTTP']
    GCP_Compute_Engine_Instance_by_HTTP: Template = _loaded['GCP Compute Engine Instance by HTTP']
    GCP_by_HTTP: Template = _loaded['GCP by HTTP']
    OpenStack_Nova_by_HTTP: Template = _loaded['OpenStack Nova by HTTP']
    OpenStack_by_HTTP: Template = _loaded['OpenStack by HTTP']
    Oracle_Cloud_Autonomous_Database_by_HTTP: Template = _loaded['Oracle Cloud Autonomous Database by HTTP']
    Oracle_Cloud_Block_Volume_by_HTTP: Template = _loaded['Oracle Cloud Block Volume by HTTP']
    Oracle_Cloud_Boot_Volume_by_HTTP: Template = _loaded['Oracle Cloud Boot Volume by HTTP']
    Oracle_Cloud_Compute_by_HTTP: Template = _loaded['Oracle Cloud Compute by HTTP']
    Oracle_Cloud_Networking_by_HTTP: Template = _loaded['Oracle Cloud Networking by HTTP']
    Oracle_Cloud_Object_Storage_by_HTTP: Template = _loaded['Oracle Cloud Object Storage by HTTP']
    Oracle_Cloud_by_HTTP: Template = _loaded['Oracle Cloud by HTTP']
