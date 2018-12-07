# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=too-many-lines

from azure.mgmt.sqlvirtualmachine.models import (
    SqlServerLicenseType,
    BackupScheduleType,
    FullBackupFrequencyType,
    ConnectivityType,
    SqlWorkloadType,
    DiskConfigurationType,
    SqlImageSku,
    DayOfWeek,
    SqlVmGroupImageSku
)

from azure.cli.core.commands.parameters import (
    get_enum_type,
    tags_type,
    get_three_state_flag
)


# pylint: disable=too-many-statements, line-too-long
def load_arguments(self, _):

    for scope in ['sqlvm', 'sqlvm group']:
        with self.argument_context(scope) as c:
            c.argument('tags', tags_type)

    ###############################################
    #    sql virtual machine groups params        #
    ###############################################

    with self.argument_context('sqlvm group') as c:
        c.argument('sql_virtual_machine_group_name',
                   options_list=['--name', '-n'],
                   help='Name of the SQL virtual machine group.')
        c.argument('sql_image_offer',
                   options_list=['--image-offer', '-i'],
                   help='SQL image offer. Examples may include SQL2016-WS2016, SQL2017-WS2016.')
        c.argument('sql_image_sku',
                   options_list=['--image-sku', '-s'],
                   help='SQL image sku.',
                   arg_type=get_enum_type(SqlVmGroupImageSku))

    with self.argument_context('sqlvm group', arg_group='WSFC Domain Profile') as c:
        c.argument('domain_fqdn',
                   options_list=['--domain-fqdn', '-f'],
                   help='Fully qualified name of the domain.')
        c.argument('cluster_operator_account',
                   options_list=['--operator-acc', '-p'],
                   help='Account name used for operating cluster i.e. will be part of administrators group on all the participating virtual machines in the cluster.')
        c.argument('sql_service_account',
                   options_list=['--service-acc', '-e'],
                   help='Account name under which SQL service will run on all participating SQL virtual machines in the cluster.')
        c.argument('storage_account_url',
                   options_list=['--sa-url', '-u'],
                   help='Fully qualified ARM resource id of the witness storage account.')
        c.argument('storage_account_key',
                   options_list=['--sa-key', '-k'],
                   help='Primary key of the witness storage account.')
        c.argument('cluster_bootstrap_account',
                   options_list=['--bootstrap-acc'],
                   help='Account name used for creating cluster (at minimum needs permissions to \'Create Computer Objects\' in domain).')
        c.argument('file_share_witness_path',
                   options_list=['--fsw-path'],
                   help='Optional path for fileshare witness.')
        c.argument('ou_path',
                   help='Organizational Unit path in which the nodes and cluster will be present.')

    ###############################################
    #    availability group listener params       #
    ###############################################

    with self.argument_context('sqlvm aglistener') as c:
        c.argument('availability_group_listener_name',
                   options_list=['--name', '-n'],
                   help='Name of the availability group listener.')
        c.argument('sql_virtual_machine_group_name',
                   options_list=['--group-name', '-r'],
                   help='Name of the SQL virtual machine group.')
        c.argument('port',
                   options_list=['--port', '-p'],
                   help='Listener port.',
                   type=int)
        c.argument('availability_group_name',
                   options_list=['--ag-name', '-a'],
                   help='Name of the availability group.')
        c.argument('sqlvm_resource_id',
                   options_list=['--sqlvm-rid', '-s'],
                   help='Resource id of the SQL virtual machine.')

    with self.argument_context('sqlvm aglistener', arg_group='Load Balancer Configuration') as c:
        c.argument('ip_address',
                   options_list=['--ip-address', '-i'],
                   help='Private IP address bound to the availability group listener.')
        c.argument('subnet_resource_id',
                   options_list=['--subnet-rid', '-u'],
                   help='Subnet used to include private IP.')
        c.argument('public_ip_address_resource_id',
                   options_list=['--public-ip-rid', '-c'],
                   help='Resource id of the public IP.')
        c.argument('load_balancer_resource_id',
                   options_list=['--lb-rid', '-b'],
                   help='Resource id of the load balancer.')
        c.argument('probe_port',
                   options_list=['--probe-port', '-e'],
                   help='Probe port.',
                   type=int)
        c.argument('sql_virtual_machine_instances',
                   options_list=['--sqlvm-rids', '-l'],
                   nargs='+',
                   help='Space-separated list of SQL virtual machine instance resource id\'s that are enrolled into the availability group listener.')


    ###############################################
    #      sql virtual machine params             #
    ###############################################

    with self.argument_context('sqlvm') as c:
        c.argument('sql_virtual_machine_name',
                   options_list=['--name', '-n'])
        c.argument('sql_virtual_machine_group_resource_id',
                   options_list=['--sqlvm-group-rid'],
                   help='ARM resource id of the SQL virtual machine group this SQL virtual machine is or will be part of.')
        c.argument('sql_server_license_type',
                   help='SQL Server license type.',
                   options_list=['--license-type'],
                   arg_type=get_enum_type(SqlServerLicenseType))

    with self.argument_context('sqlvm', arg_group='WSFC Domain Credentials') as c:
        c.argument('cluster_bootstrap_account_password',
                   options_list=['--boostrap-acc-pwd'],
                   help='Cluster bootstrap account password.')
        c.argument('cluster_operator_account_password',
                   options_list=['--operator-acc-pwd'],
                   help='Cluster operator account password.')
        c.argument('sql_service_account_password',
                   options_list=['--service-acc-pwd'],
                   help='SQL service account password.')

    with self.argument_context('sqlvm add-to-group') as c:
        c.argument('sql_virtual_machine_group_resource_id',
                   options_list=['--sqlvm-group-rid', '-r'],
                   help='ARM resource id of the SQL virtual machine group this SQL virtual machine is or will be part of.')

    with self.argument_context('sqlvm add-to-group', arg_group='WSFC Domain Credentials') as c:
        c.argument('cluster_bootstrap_account_password',
                   options_list=['--boostrap-acc-pwd', '-b'],
                   help='Cluster bootstrap account password.')
        c.argument('cluster_operator_account_password',
                   options_list=['--operator-acc-pwd', '-p'],
                   help='Cluster operator account password.')
        c.argument('sql_service_account_password',
                   options_list=['--service-acc-pwd', '-s'],
                   help='SQL service account password.')

    with self.argument_context('sqlvm', arg_group='Auto Patching Settings') as c:
        c.argument('enable_auto_patching',
                   help='Enable or disable autopatching on SQL virtual machine. If any autopatching settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('day_of_week',
                   help='Day of week to apply the patch on.',
                   arg_type=get_enum_type(DayOfWeek))
        c.argument('maintenance_window_starting_hour',
                   type=int,
                   help='Hour of the day when patching is initiated. Local VM time 0-23 hours.')
        c.argument('maintenance_window_duration',
                   type=int,
                   help='Duration of patching. 30-180 minutes.')

    with self.argument_context('sqlvm', arg_group='Auto Backup Settings') as c:
        c.argument('enable_auto_backup',
                   help='Enable or disable autobackup on SQL virtual machine. If any backup settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('enable_encryption',
                   help=' Enable encryption for backup on SQL virtual machine.')
        c.argument('retention_period',
                   type=int,
                   help='Retention period of backup.')
        c.argument('storage_account_url',
                   help='Storage account url where backup will be taken to.')
        c.argument('storage_access_key',
                   help='Storage account key where backup will be taken to.')
        c.argument('backup_password',
                   help='Password for encryption on backup.')
        c.argument('backup_system_dbs',
                   help='Include system databases on backup.')
        c.argument('backup_schedule_type',
                   help='Backup schedule type.',
                   arg_type=get_enum_type(BackupScheduleType))
        c.argument('full_backup_frequency',
                   help='Frequency of full backups. In both cases, full backups begin during the next scheduled time window.',
                   arg_type=get_enum_type(FullBackupFrequencyType))
        c.argument('full_backup_start_time',
                   type=int,
                   help='Start time of a given day during which full backups can take place. 0-23 hours.')
        c.argument('full_backup_window_hours',
                   type=int,
                   help='Duration of the time window of a given day during which full backups can take place. 1-23 hours.')
        c.argument('log_backup_frequency',
                   type=int,
                   help='Frequency of log backups. 5-60 minutes.')

    with self.argument_context('sqlvm', arg_group='Key Vault Credential Settings') as c:
        c.argument('enable_key_vault_credential',
                   help='Enable or disable key vault credential setting. If any key vault settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('credential_name',
                   help='Credential name')
        c.argument('azure_key_vault_url',
                   help='Azure Key Vault url.')
        c.argument('service_principal_name',
                   help='Service principal name to access key vault.')
        c.argument('service_principal_secret',
                   help='Service principal name secret to access key vault.')

    with self.argument_context('sqlvm', arg_group='SQL Connectivity Update Settings') as c:
        c.argument('connectivity_type',
                   help='SQL Server connectivity option.',
                   arg_type=get_enum_type(ConnectivityType))
        c.argument('port',
                   help='SQL Server port.',
                   type=int)
        c.argument('sql_auth_update_username',
                   help='SQL Server sysadmin login to create.')
        c.argument('sql_auth_update_password',
                   help='SQL Server sysadmin login password.')

    with self.argument_context('sqlvm', arg_group='SQL Workload Type Update Settings') as c:
        c.argument('sql_workload_type',
                   help='SQL Server workload type.',
                   arg_type=get_enum_type(SqlWorkloadType))

    with self.argument_context('sqlvm', arg_group='SQL Storage Update Settings') as c:
        c.argument('disk_count',
                   help='Virtual machine disk count.',
                   type=int)
        c.argument('disk_configuration_type',
                   help='Disk configuration to apply to SQL Server.',
                   arg_type=get_enum_type(DiskConfigurationType))

    with self.argument_context('sqlvm', arg_group='Additional Features') as c:
        c.argument('enable_r_services',
                   help='Enable or disable R services (SQL 2016 onwards).',
                   arg_type=get_three_state_flag())
