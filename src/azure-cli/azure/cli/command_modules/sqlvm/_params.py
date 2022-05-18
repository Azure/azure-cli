# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=too-many-lines

from azure.cli.core.commands.validators import get_default_location_from_resource_group

from azure.mgmt.sqlvirtualmachine.models import (
    SqlServerLicenseType,
    BackupScheduleType,
    FullBackupFrequencyType,
    ConnectivityType,
    SqlWorkloadType,
    DiskConfigurationType,
    DayOfWeek,
    SqlVmGroupImageSku,
    SqlImageSku,
    SqlManagementMode
)

from azure.cli.core.commands.parameters import (
    get_enum_type,
    tags_type,
    get_three_state_flag,
    get_location_type
)

from ._validators import (
    validate_sqlvm_group,
    validate_sqlvm_list,
    validate_load_balancer,
    validate_public_ip_address,
    validate_subnet,
    validate_sqlmanagement,
    validate_expand,
    validate_assessment,
    validate_assessment_start_time_local
)


# pylint: disable=too-many-statements, line-too-long
def load_arguments(self, _):

    for scope in ['sql vm', 'sql vm group']:
        with self.argument_context(scope) as c:
            c.argument('tags', tags_type)

    ###############################################
    #    sql virtual machine groups params        #
    ###############################################

    with self.argument_context('sql vm group') as c:
        c.argument('sql_virtual_machine_group_name',
                   options_list=['--name', '-n'],
                   id_part='name',
                   help='Name of the SQL virtual machine group.')
        c.argument('sql_image_offer',
                   options_list=['--image-offer', '-i'],
                   help='SQL image offer. Examples may include SQL2016-WS2016, SQL2017-WS2016.')
        c.argument('sql_image_sku',
                   options_list=['--image-sku', '-s'],
                   help='SQL image sku.',
                   arg_type=get_enum_type(SqlVmGroupImageSku))
        c.argument('location',
                   help='Location. If not provided, group will be created in the same reosurce group location.'
                   'You can configure the default location using `az configure --defaults location=<location>`.',
                   arg_type=get_location_type(self.cli_ctx),
                   validator=get_default_location_from_resource_group)

    with self.argument_context('sql vm group', arg_group='WSFC Domain Profile') as c:
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
                   options_list=['--storage-account', '-u'],
                   help='Storage account url of the witness storage account.')
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
                   help='Organizational Unit path in which the nodes and cluster will be present. Example: OU=WSCluster,DC=testdomain,DC=com')

    ###############################################
    #    availability group listener params       #
    ###############################################

    with self.argument_context('sql vm group ag-listener') as c:
        c.argument('availability_group_listener_name',
                   options_list=['--name', '-n'],
                   id_part='name',
                   help='Name of the availability group listener.')
        c.argument('sql_virtual_machine_group_name',
                   options_list=['--group-name', '-r'],
                   help='Name of the SQL virtual machine group.',
                   id_part=None)
        c.argument('port',
                   options_list=['--port', '-p'],
                   help='Listener port.',
                   type=int)
        c.argument('availability_group_name',
                   options_list=['--ag-name', '-a'],
                   help='Name of the availability group. Please refer to '
                   'https://docs.microsoft.com/sql/database-engine/availability-groups/windows/use-the-availability-group-wizard-sql-server-management-studio?view=sql-server-2017 '
                   'to create and availability group')

    with self.argument_context('sql vm group ag-listener', arg_group='Load Balancer Configuration') as c:
        c.argument('ip_address',
                   options_list=['--ip-address', '-i'],
                   help='Private IP address bound to the availability group listener.')
        c.argument('subnet_resource_id',
                   options_list=['--subnet', '-u'],
                   validator=validate_subnet,
                   help='The name or resource id of the subnet to include in the private IP.')
        c.argument('vnet_name',
                   options_list=['--vnet-name'],
                   help='Name of the virtual network. Provide only if name of the subnet has been provided.')
        c.argument('public_ip_address_resource_id',
                   options_list=['--public-ip', '-c'],
                   validator=validate_public_ip_address,
                   help='Name or resource ID of the public IP.')
        c.argument('load_balancer_resource_id',
                   options_list=['--load-balancer', '-b'],
                   validator=validate_load_balancer,
                   help='Name or resource ID of the load balancer.')
        c.argument('probe_port',
                   options_list=['--probe-port', '-e'],
                   help='Probe port.',
                   type=int)
        c.argument('sql_virtual_machine_instances',
                   options_list=['--sqlvms', '-q'],
                   nargs='+',
                   validator=validate_sqlvm_list,
                   help='Space-separated list of SQL virtual machine instance name or resource IDs that are enrolled into the availability group.')

    ###############################################
    #      sql virtual machine params             #
    ###############################################

    with self.argument_context('sql vm') as c:
        c.argument('sql_virtual_machine_name',
                   options_list=['--name', '-n'],
                   id_part='name',
                   help='Name of the SQL virtual machine.')
        c.argument('location',
                   help='Location. If not provided, virtual machine should be in the same region of resource group.'
                   'You can configure the default location using `az configure --defaults location=<location>`.',
                   arg_type=get_location_type(self.cli_ctx),
                   validator=get_default_location_from_resource_group)
        c.argument('expand',
                   help='Get the SQLIaaSExtension configuration settings. To view all settings, use *. To select only a few, the settings must be space-separted.',
                   nargs='+',
                   validator=validate_expand,
                   arg_type=get_enum_type(['*', 'AssessmentSettings', 'AutoBackupSettings', 'AutoPatchingSettings', 'KeyVaultCredentialSettings', 'ServerConfigurationsManagementSettings']))
        c.argument('sql_management_mode',
                   help='SQL Server management type. If NoAgent selected, please provide --image-sku and --offer-type.',
                   options_list=['--sql-mgmt-type'],
                   validator=validate_sqlmanagement,
                   arg_type=get_enum_type(SqlManagementMode))

    with self.argument_context('sql vm', arg_group='SQL Server License') as c:
        c.argument('sql_server_license_type',
                   help='SQL Server license type.',
                   options_list=['--license-type', '-i'],
                   arg_type=get_enum_type(SqlServerLicenseType))
        c.argument('sql_image_sku',
                   options_list=['--image-sku'],
                   help='SQL image sku.',
                   arg_type=get_enum_type(SqlImageSku))
        c.argument('sql_image_offer',
                   options_list=['--image-offer'],
                   help='SQL image offer. Examples include SQL2008R2-WS2008, SQL2008-WS2008.')

    with self.argument_context('sql vm add-to-group') as c:
        c.argument('sql_virtual_machine_group_resource_id',
                   options_list=['--sqlvm-group', '-r'],
                   validator=validate_sqlvm_group,
                   help='Name or resource ID of the SQL virtual machine group. If only name provided, SQL virtual machine group should be in the same '
                   'resource group of the SQL virtual machine.')
        c.argument('sql_virtual_machine_name',
                   id_part='name',
                   help="Name of the SQL virtual machine.")

    with self.argument_context('sql vm remove-from-group') as c:
        c.argument('sql_virtual_machine_name',
                   id_part='name',
                   help="Name of the SQL virtual machine.")

    with self.argument_context('sql vm update') as c:
        c.argument('sql_management_mode',
                   help='SQL Server management type. Updates from LightWeight to Full.',
                   options_list=['--sql-mgmt-type'],
                   arg_type=get_enum_type(['Full']))
        c.argument('prompt',
                   options_list=['--yes', '-y'],
                   help="Do not prompt for confirmation. Requires --sql-mgmt-type.")

    with self.argument_context('sql vm add-to-group', arg_group='WSFC Domain Credentials') as c:
        c.argument('cluster_bootstrap_account_password',
                   options_list=['-b', '--bootstrap-acc-pwd'],
                   help='Password for the cluster bootstrap account if provided in the SQL virtual machine group.')
        c.argument('cluster_operator_account_password',
                   options_list=['--operator-acc-pwd', '-p'],
                   help='Password for the cluster operator account provided in the SQL virtual machine group.')
        c.argument('sql_service_account_password',
                   options_list=['--service-acc-pwd', '-s'],
                   help='Password for the SQL service account provided in the SQL virtual machine group.')

    with self.argument_context('sql vm', arg_group='Auto Patching Settings') as c:
        c.argument('enable_auto_patching',
                   help='Enable or disable autopatching on SQL virtual machine. If any autopatching settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('day_of_week',
                   help='Day of week to apply the patch on.',
                   arg_type=get_enum_type(DayOfWeek))
        c.argument('maintenance_window_starting_hour',
                   type=int,
                   options_list=['--maintenance-window-start-hour'],
                   help='Hour of the day when patching is initiated. Local VM time 0-23 hours.')
        c.argument('maintenance_window_duration',
                   type=int,
                   help='Duration of patching. 30-180 minutes.')

    with self.argument_context('sql vm', arg_group='Auto Backup Settings') as c:
        c.argument('enable_auto_backup',
                   help='Enable or disable autobackup on SQL virtual machine. If any backup settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('enable_encryption',
                   help=' Enable encryption for backup on SQL virtual machine.',
                   arg_type=get_three_state_flag())
        c.argument('retention_period',
                   type=int,
                   help='Retention period of backup. 1-30 days.')
        c.argument('storage_account_url',
                   options_list=['--storage-account'],
                   help='Storage account url where backup will be taken to.')
        c.argument('storage_access_key',
                   options_list=['--sa-key'],
                   help='Storage account key where backup will be taken to.')
        c.argument('backup_password',
                   options_list=['--backup-pwd'],
                   help='Password for encryption on backup.')
        c.argument('backup_system_dbs',
                   help='Include system databases on backup.',
                   arg_type=get_three_state_flag())
        c.argument('backup_schedule_type',
                   help='Backup schedule type.',
                   arg_type=get_enum_type(BackupScheduleType))
        c.argument('full_backup_frequency',
                   help='Frequency of full backups. In both cases, full backups begin during the next scheduled time window.',
                   arg_type=get_enum_type(FullBackupFrequencyType))
        c.argument('full_backup_start_time',
                   type=int,
                   options_list=['--full-backup-start-hour'],
                   help='Start time of a given day during which full backups can take place. 0-23 hours.')
        c.argument('full_backup_window_hours',
                   type=int,
                   options_list=['--full-backup-duration'],
                   help='Duration of the time window of a given day during which full backups can take place. 1-23 hours.')
        c.argument('log_backup_frequency',
                   type=int,
                   help='Frequency of log backups. 5-60 minutes.')

    with self.argument_context('sql vm', arg_group='Key Vault Credential Settings') as c:
        c.argument('enable_key_vault_credential',
                   help='Enable or disable key vault credential setting. If any key vault settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('credential_name',
                   help='Credential name')
        c.argument('azure_key_vault_url',
                   options_list=['--key-vault'],
                   help='Azure Key Vault url.')
        c.argument('service_principal_name',
                   options_list=['--sp-name'],
                   help='Service principal name to access key vault.')
        c.argument('service_principal_secret',
                   options_list=['--sp-secret'],
                   help='Service principal name secret to access key vault.')

    with self.argument_context('sql vm', arg_group='SQL Connectivity Update Settings') as c:
        c.argument('connectivity_type',
                   help='SQL Server connectivity option.',
                   arg_type=get_enum_type(ConnectivityType))
        c.argument('port',
                   help='SQL Server port.',
                   type=int)
        c.argument('sql_auth_update_username',
                   help='SQL Server sysadmin login to create.')
        c.argument('sql_auth_update_password',
                   options_list=['--sql-auth-update-pwd'],
                   help='SQL Server sysadmin login password.')

    with self.argument_context('sql vm', arg_group='SQL Workload Type Update Settings') as c:
        c.argument('sql_workload_type',
                   help='SQL Server workload type.',
                   arg_type=get_enum_type(SqlWorkloadType))

    with self.argument_context('sql vm', arg_group='SQL Storage Update Settings') as c:
        c.argument('disk_count',
                   help='Virtual machine disk count.',
                   type=int)
        c.argument('disk_configuration_type',
                   help='Disk configuration to apply to SQL Server.',
                   arg_type=get_enum_type(DiskConfigurationType))

    with self.argument_context('sql vm', arg_group='Additional Features') as c:
        c.argument('enable_r_services',
                   help='Enable or disable R services (SQL 2016 onwards).',
                   arg_type=get_three_state_flag())

    with self.argument_context('sql vm', arg_group='Assessment Settings') as c:
        c.argument('enable_assessment',
                   help='Enable or disable assessment feature. If any assessment settings provided, parameter automatically sets to true.',
                   validator=validate_assessment,
                   arg_type=get_three_state_flag())
        c.argument('enable_assessment_schedule',
                   options_list=['--enable-assessment-schedule', '--am-schedule'],
                   help='Enable or disable assessment Schedule. If any assessment schedule settings provided, parameter automatically sets to true.',
                   arg_type=get_three_state_flag())
        c.argument('assessment_weekly_interval',
                   options_list=['--assessment-weekly-interval', '--am-week-int'],
                   help='Number of weeks to schedule between 2 assessment runs. Supports value from 1-6.',
                   arg_type=get_enum_type(['1', '2', '3', '4', '5', '6']))
        c.argument('assessment_monthly_occurrence',
                   options_list=['--assessment-monthly-occurrence', '--am-month-occ'],
                   help='Occurence of the DayOfWeek day within a month to schedule assessment. Supports values 1,2,3,4 and -1. Use -1 for last DayOfWeek day of the month (for example - last Tuesday of the month).',
                   arg_type=get_enum_type(['1', '2', '3', '4', '-1']))
        c.argument('assessment_day_of_week',
                   options_list=['--assessment-day-of-week', '--am-day'],
                   help='Day of the week to run assessment.',
                   arg_type=get_enum_type(DayOfWeek))
        c.argument('assessment_start_time_local',
                   options_list=['--assessment-start-time-local', '--am-time'],
                   help='Time of the day in HH:mm format. Examples include 17:30, 05:13.',
                   validator=validate_assessment_start_time_local)
