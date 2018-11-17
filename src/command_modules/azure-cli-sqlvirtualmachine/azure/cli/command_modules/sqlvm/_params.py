# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=too-many-lines

import itertools
from enum import Enum

from knack.arguments import CLIArgumentType, ignore_type

from azure.mgmt.sqlvirtualmachine.models import (
    SqlVirtualMachine,
    SqlVirtualMachineGroup,
    AvailabilityGroupListener,
    SqlServerLicenseType,
    AutoPatchingSettings,
    BackupScheduleType,
    FullBackupFrequencyType,
    ConnectivityType,
    SqlWorkloadType,
    DiskConfigurationType,
    SqlImageSku,
    DayOfWeek
)

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_resource_name_completion_list,
    get_location_type,
    tags_type
)


# pylint: disable=too-many-statements
def load_arguments(self, _):

    for scope in ['sqlvm', 'sqlvm group']:
        with self.argument_context(scope) as c:
            c.argument('tags', tags_type)

    ###############################################
    #    sql virtual machine groups params        #
    ###############################################

    with self.argument_context('sqlvm group') as c:
        c.argument('sql_virtual_machine_group_name',
                   options_list=['--name', '-n'])

    with self.argument_context('sqlvm group create') as c:
        c.argument('sql-image-offer',
                    help='SQL image offer. Examples may include SQL2016-WS2016, SQL2017-WS2016.')
        c.argument('sql_image_sku',
                    help='SQL image sku.',
                    arg_type=get_enum_type(SqlImageSku))

    with self.argument_context('sqlvm group create', arg_group='WSFC Domain Profile') as c:
        c.argument('domain_fqdn',
                    help='Fully qualified name of the domain.')
        c.argument('cluster_operator_account',
                    help='Account name used for operating cluster i.e. will be part of administrators group on all the participating virtual machines in the cluster.')
        c.argument('sql_service_account',
                    help='Account name under which SQL service will run on all participating SQL virtual machines in the cluster.')
        c.argument('storage_account_url',
                    help='Fully qualified ARM resource id of the witness storage account.')
        c.argument('storage_account_key',
                    help='Primary key of the witness storage account.')
        c.argument('cluster_bootstrap_account',
                    help='Account name used for creating cluster (at minimum needs permissions to \'Create Computer Objects\' in domain).')
        c.argument('file_share_witness_path',
                    help='Optional path for fileshare witness.')
        c.argument('ou_path',
                    help='Organizational Unit path in which the nodes and cluster will be present.')

    ###############################################
    #    availability group listener params       #
    ###############################################

    with self.argument_context('sqlvm aglistener') as c:
        c.argument('availability_group_listener_name',
                    options_list=['--name', '-n'])
        c.argument('sql_virtual_machine_group_name',
                    options_list=['--group-name, -gn'])

    with self.argument_context('sqlvm aglistener create') as c:
        c.argument('port',
                    help='Listener port.',
                    type=int)

    with self.argument_context('sqlvm aglistener create', arg_group='Load Balancer Configuration') as c:
        c.argument('ip_address',
                    help='Private IP address bound to the availability group listener.')
        c.argument('subnet_resource_id',
                    help='Subnet used to include private IP.')
        c.argument('public_ip_address_resource_id',
                    help='Resource id of the public IP.')
        c.argument('load_balancer_resource_id',
                    help='Subnet used to include private IP.')
        c.argument('probe_port',
                    help='Probe port.',
                    type=int)
        c.argument('sql_virtual_machine_instances', nargs='+',
                    help='Space-separated list of SQL virtual machine instance resource id\'s that are enrolled into the availability group listener.')


    ###############################################
    #      sql virtual machine params             #
    ###############################################

    with self.argument_context('sqlvm') as c:
        c.argument('sql_virtual_machine_name',
                   options_list=['--name', '-n'])

    with self.argument_context('sqlvm create') as c:
        c.argument('sql_virtual_machine_group_resource_id',
                    help='ARM resource id of the SQL virtual machine group this SQL virtual machine is or will be part of.')
        c.argument('sql_server_license_type',
                    help='SQL Server license type.',
                    arg_type=get_enum_type(SqlServerLicenseType))

    with self.argument_context('sqlvm create', arg_group='WSFC Domain Credentials') as c:
        c.argument('cluster_bootstrap_account_password',
                    help='Cluster bootstrap account password.')
        c.argument('cluster_operator_account_password',
                    help='Cluster operator account password.')
        c.argument('sql_service_account_password',
                    help='SQL service account password.')

    with self.argument_context('sqlvm create', arg_group='Auto Patching Settings') as c:
         c.argument('enable_auto_patching',
                     help='Enable autopatching on SQL virtual machine.')
         c.argument('day_of_week',
                     help='Day of week to apply the patch on.',
                     arg_type=get_enum_type(DayOfWeek))
         c.argument('maintenance_window_starting_hour',
                     type=int,
                     help='Hour of the day when patching is initiated.')
         c.argument('maintenance_window_duration',
                     type=int,
                     help='Duration of patching.')

    with self.argument_context('sqlvm create', arg_group='Auto Backup Settings') as c:
         c.argument('enable_auto_backup',
                     help='Enable autobackup on SQL virtual machine.')
         c.argument('enable_encryption',
                     help='Enable encryption for backup on SQL virtual machine.')
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
                     help='Include or exclude system databases from auto backup.')
         c.argument('backup_schedule_type',
                     arg_type=get_enum_type(BackupScheduleType),
                     help='Backup schedule type.')
         c.argument('full_backup_frequency',
                     arg_type=get_enum_type(FullBackupFrequencyType),
                     help='Frequency of full backups. In both cases, full backups begin during the next scheduled time window.')
         c.argument('full_backup_start_time',
                     type=int,
                     help='Start time of a given day during which full backups can take place. 0-23 hours.')
         c.argument('full_backup_window_hours',
                     type=int,
                     help='Duration of the time window of a given day during which full backups can take place. 1-23 hours.')
         c.argument('log_backup_frequency',
                     type=int,
                     help='Frequency of log backups. 5-60 minutes.')

    with self.argument_context('sqlvm create', arg_group='Key Vault Credential Settings') as c:
         c.argument('enable_key_vault_credential',
                     help='Enable key vault credential setting.')
         c.argument('credential_name',
                     help='Credential name')
         c.argument('azure_key_vault_url',
                     help='Azure Key Vault url.')
         c.argument('service_principal_name',
                     help='Service principal name to access key vault.')
         c.argument('service_principal_secret',
                     help='Service principal name secret to access key vault.')

    with self.argument_context('sqlvm create', arg_group='SQL Connectivity Update Settings') as c:
        c.argument('connectivity_type',
                    help='SQL Server connectivity option.',
                    arg_type=get_enum_type(ConnectivityType))
        c.argument('port',
                    help='SQL Server port.',
                    type=int)
        c.argument('sql_auth_update_user_name',
                    help='SQL Server sysadmin login to create.')
        c.argument('sql_auth_update_password',
                    help='SQL Server sysadmin login password.')

    with self.argument_context('sqlvm create', arg_group='SQL Workload Type Update Settings') as c:
        c.argument('sql_workload_type',
                    help='SQL Server workload type.',
                    arg_type=get_enum_type(SqlWorkloadType))

    with self.argument_context('sqlvm create', arg_group='SQL Storage Update Settings') as c:
        c.argument('disk_count',
                    help='Virtual machine disk count.',
                    type=int)
        c.argument('disk_configuration_type',
                    help='Disk configuration to apply to SQL Server.',
                    arg_type=get_enum_type(DiskConfigurationType))

    with self.argument_context('sqlvm create', arg_group='Additional Features Server Configurations') as c:
        c.argument('is_rservices_enabled',
                    help='Enable or disable R services (SQL 2016 onwards).')
        c.argument('backup_permissions_for_azure_backup_svc',
                    help='Enable or disable Azure Backup service.')






