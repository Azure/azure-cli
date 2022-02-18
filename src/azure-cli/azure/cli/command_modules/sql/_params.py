# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=too-many-lines

import itertools
from enum import Enum

from azure.mgmt.sql.models import (
    Database,
    ElasticPool,
    ElasticPoolPerDatabaseSettings,
    ImportExistingDatabaseDefinition,
    ExportDatabaseDefinition,
    InstancePool,
    ManagedDatabase,
    ManagedInstance,
    ManagedInstanceAdministrator,
    Server,
    ServerAzureADAdministrator,
    Sku,
    BlobAuditingPolicyState,
    CatalogCollationType,
    CreateMode,
    DatabaseLicenseType,
    ElasticPoolLicenseType,
    SampleName,
    SecurityAlertPolicyState,
    ServerConnectionType,
    ServerKeyType,
    StorageKeyType,
    TransparentDataEncryptionStatus
)

from azure.cli.core.commands.parameters import (
    get_three_state_flag,
    get_enum_type,
    get_resource_name_completion_list,
    get_location_type,
    tags_type,
    resource_group_name_type
)

from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group
)

from knack.arguments import CLIArgumentType, ignore_type

from .custom import (
    ClientAuthenticationType,
    ClientType,
    ComputeModelType,
    DatabaseCapabilitiesAdditionalDetails,
    ElasticPoolCapabilitiesAdditionalDetails,
    FailoverPolicyType,
    ResourceIdType,
    SqlServerMinimalTlsVersionType,
    SqlManagedInstanceMinimalTlsVersionType,
    AuthenticationType
)

from ._validators import (
    create_args_for_complex_type,
    validate_managed_instance_storage_size,
    validate_backup_storage_redundancy,
    validate_backup_storage_redundancy_mi,
    validate_subnet
)


#####
#        SizeWithUnitConverter - consider moving to common code (azure.cli.core.commands.parameters)
#####


class SizeWithUnitConverter():  # pylint: disable=too-few-public-methods

    def __init__(
            self,
            unit='kB',
            result_type=int,
            unit_map=None):
        self.unit = unit
        self.result_type = result_type
        self.unit_map = unit_map or dict(B=1, kB=1024, MB=1024 * 1024, GB=1024 * 1024 * 1024,
                                         TB=1024 * 1024 * 1024 * 1024)

    def __call__(self, value):
        numeric_part = ''.join(itertools.takewhile(str.isdigit, value))
        unit_part = value[len(numeric_part):]

        try:
            uvals = (self.unit_map[unit_part] if unit_part else 1) / \
                (self.unit_map[self.unit] if self.unit else 1)
            return self.result_type(uvals * self.result_type(numeric_part))
        except KeyError:
            raise ValueError()

    def __repr__(self):
        return 'Size (in {}) - valid units are {}.'.format(
            self.unit,
            ', '.join(sorted(self.unit_map, key=self.unit_map.__getitem__)))


def get_internal_backup_storage_redundancy(self):
    return {
        'local': 'Local',
        'zone': 'Zone',
        'geo': 'Geo',
    }.get(self.lower(), 'Invalid')


def get_internal_backup_storage_redundancy_mi(self):
    return {
        'local': 'LRS',
        'zone': 'ZRS',
        'geo': 'GRS',
    }.get(self.lower(), 'Invalid')


#####
#        Reusable param type definitions
#####


sku_arg_group = 'Performance Level'

sku_component_arg_group = 'Performance Level (components)'

serverless_arg_group = 'Serverless offering'

server_configure_help = 'You can configure the default using `az configure --defaults sql-server=<name>`'

time_format_help = 'Time should be in following format: "YYYY-MM-DDTHH:MM:SS".'

storage_arg_group = "Storage"
log_analytics_arg_group = "Log Analytics"
event_hub_arg_group = "Event Hub"


def get_location_type_with_default_from_resource_group(cli_ctx):
    return CLIArgumentType(
        arg_type=get_location_type(cli_ctx),
        required=False,
        validator=get_default_location_from_resource_group)


server_param_type = CLIArgumentType(
    options_list=['--server', '-s'],
    configured_default='sql-server',
    help='Name of the Azure SQL server. ' + server_configure_help,
    completer=get_resource_name_completion_list('Microsoft.SQL/servers'),
    # Allow --ids command line argument. id_part=name is 1st name in uri
    id_part='name')

available_param_type = CLIArgumentType(
    options_list=['--available', '-a'],
    help='If specified, show only results that are available in the specified region.')

tier_param_type = CLIArgumentType(
    arg_group=sku_component_arg_group,
    options_list=['--tier', '--edition', '-e'])

capacity_param_type = CLIArgumentType(
    arg_group=sku_component_arg_group,
    options_list=['--capacity', '-c'])

capacity_or_dtu_param_type = CLIArgumentType(
    arg_group=sku_component_arg_group,
    options_list=['--capacity', '-c', '--dtu'])

family_param_type = CLIArgumentType(
    arg_group=sku_component_arg_group,
    options_list=['--family', '-f'])

elastic_pool_id_param_type = CLIArgumentType(
    arg_group=sku_arg_group,
    options_list=['--elastic-pool'])

compute_model_param_type = CLIArgumentType(
    arg_group=serverless_arg_group,
    options_list=['--compute-model'],
    help='The compute model of the database.',
    arg_type=get_enum_type(ComputeModelType))

auto_pause_delay_param_type = CLIArgumentType(
    arg_group=serverless_arg_group,
    options_list=['--auto-pause-delay'],
    help='Time in minutes after which database is automatically paused. '
    'A value of -1 means that automatic pause is disabled.')

min_capacity_param_type = CLIArgumentType(
    arg_group=serverless_arg_group,
    options_list=['--min-capacity'],
    help='Minimal capacity that database will always have allocated, if not paused')

max_size_bytes_param_type = CLIArgumentType(
    options_list=['--max-size'],
    type=SizeWithUnitConverter('B', result_type=int),
    help='The max storage size. If no unit is specified, defaults to bytes (B).')

zone_redundant_param_type = CLIArgumentType(
    options_list=['--zone-redundant', '-z'],
    help='Specifies whether to enable zone redundancy',
    arg_type=get_three_state_flag())

maintenance_configuration_id_param_type = CLIArgumentType(
    options_list=['--maint-config-id', '-m'],
    help='Specified maintenance configuration id or name for this resource.')

ledger_on_param_type = CLIArgumentType(
    options_list=['--ledger-on'],
    help='Create a ledger database, in which the integrity of all data is protected by the ledger feature. '
         'All tables in the ledger database must be ledger tables. '
         'Note: the value of this property cannot be changed after the database has been created. ',
    arg_type=get_three_state_flag("Enabled", "Disabled", False, False))

managed_instance_param_type = CLIArgumentType(
    options_list=['--managed-instance', '--mi'],
    help='Name of the Azure SQL managed instance.')

kid_param_type = CLIArgumentType(
    options_list=['--kid', '-k'],
    help='The Azure Key Vault key identifier of the server key. An example key identifier is '
    '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

server_key_type_param_type = CLIArgumentType(
    options_list=['--server-key-type', '-t'],
    help='The type of the server key',
    arg_type=get_enum_type(ServerKeyType))

storage_param_type = CLIArgumentType(
    options_list=['--storage'],
    type=SizeWithUnitConverter('GB', result_type=int, unit_map=dict(B=1.0 / (1024 * 1024 * 1024),
                                                                    kB=1.0 / (1024 * 1024),
                                                                    MB=1.0 / 1024,
                                                                    GB=1,
                                                                    TB=1024)),
    help='The storage size. If no unit is specified, defaults to gigabytes (GB).',
    validator=validate_managed_instance_storage_size)

backup_storage_redundancy_param_type = CLIArgumentType(
    options_list=['--backup-storage-redundancy', '--bsr'],
    type=get_internal_backup_storage_redundancy,
    help='Backup storage redundancy used to store backups. Allowed values include: Local, Zone, Geo.',
    validator=validate_backup_storage_redundancy)

backup_storage_redundancy_param_type_mi = CLIArgumentType(
    options_list=['--backup-storage-redundancy', '--bsr'],
    type=get_internal_backup_storage_redundancy_mi,
    help='Backup storage redundancy used to store backups. Allowed values include: Local, Zone, Geo.',
    validator=validate_backup_storage_redundancy_mi)

grace_period_param_type = CLIArgumentType(
    help='Interval in hours before automatic failover is initiated '
    'if an outage occurs on the primary server. '
    'This indicates that Azure SQL Database will not initiate '
    'automatic failover before the grace period expires. '
    'Please note that failover operation with --allow-data-loss option '
    'might cause data loss due to the nature of asynchronous synchronization.')

allow_data_loss_param_type = CLIArgumentType(
    help='Complete the failover even if doing so may result in data loss. '
    'This will allow the failover to proceed even if a primary database is unavailable.')

aad_admin_login_param_type = CLIArgumentType(
    options_list=['--display-name', '-u'],
    help='Display name of the Azure AD administrator user or group.')

aad_admin_sid_param_type = CLIArgumentType(
    options_list=['--object-id', '-i'],
    help='The unique ID of the Azure AD administrator.')

read_scale_param_type = CLIArgumentType(
    options_list=['--read-scale'],
    help='If enabled, connections that have application intent set to readonly '
    'in their connection string may be routed to a readonly secondary replica. '
    'This property is only settable for Premium and Business Critical databases.',
    arg_type=get_enum_type(['Enabled', 'Disabled']))

read_replicas_param_type = CLIArgumentType(
    options_list=['--read-replicas', '--ha-replicas'],
    type=int,
    help='The number of high availability replicas to provision for the database. '
    'Only settable for Hyperscale edition.')

blob_storage_target_state_param_type = CLIArgumentType(
    arg_group=storage_arg_group,
    options_list=['--blob-storage-target-state', '--bsts'],
    configured_default='sql-server',
    help='Indicate whether blob storage is a destination for audit records.',
    arg_type=get_enum_type(BlobAuditingPolicyState))

log_analytics_target_state_param_type = CLIArgumentType(
    arg_group=log_analytics_arg_group,
    options_list=['--log-analytics-target-state', '--lats'],
    configured_default='sql-server',
    help='Indicate whether log analytics is a destination for audit records.',
    arg_type=get_enum_type(BlobAuditingPolicyState))

log_analytics_workspace_resource_id_param_type = CLIArgumentType(
    arg_group=log_analytics_arg_group,
    options_list=['--log-analytics-workspace-resource-id', '--lawri'],
    configured_default='sql-server',
    help='The workspace ID (resource ID of a Log Analytics workspace) for a Log Analytics workspace '
         'to which you would like to send Audit Logs.')

event_hub_target_state_param_type = CLIArgumentType(
    arg_group=event_hub_arg_group,
    options_list=['--event-hub-target-state', '--ehts'],
    configured_default='sql-server',
    help='Indicate whether event hub is a destination for audit records.',
    arg_type=get_enum_type(BlobAuditingPolicyState))

event_hub_authorization_rule_id_param_type = CLIArgumentType(
    arg_group=event_hub_arg_group,
    options_list=['--event-hub-authorization-rule-id', '--ehari'],
    configured_default='sql-server',
    help='The resource Id for the event hub authorization rule.')

event_hub_param_type = CLIArgumentType(
    arg_group=event_hub_arg_group,
    options_list=['--event-hub', '--eh'],
    configured_default='sql-server',
    help='The name of the event hub. If none is specified '
         'when providing event_hub_authorization_rule_id, the default event hub will be selected.')

db_service_objective_examples = 'Basic, S0, P1, GP_Gen4_1, GP_Gen5_S_8, BC_Gen5_2, HS_Gen5_32.'
dw_service_objective_examples = 'DW100, DW1000c'


###############################################
#                sql db                       #
###############################################


class Engine(Enum):  # pylint: disable=too-few-public-methods
    """SQL RDBMS engine type."""
    db = 'db'
    dw = 'dw'


def _configure_db_dw_params(arg_ctx):
    """
    Configures params that are based on `Database` resource and therefore apply to one or more DB/DW create/update
    commands. The idea is that this does some basic configuration of each property. Each command can then potentially
    build on top of this (e.g. to give a parameter more specific help text) and .ignore() parameters that aren't
    applicable.

    Normally these param configurations would be implemented at the command group level, but these params are used
    across 2 different param groups - `sql db` and `sql dw`. So extracting it out into this common function prevents
    duplication.
    """

    arg_ctx.argument('max_size_bytes',
                     arg_type=max_size_bytes_param_type)

    arg_ctx.argument('elastic_pool_id',
                     arg_type=elastic_pool_id_param_type)

    arg_ctx.argument('compute_model',
                     arg_type=compute_model_param_type)

    arg_ctx.argument('auto_pause_delay',
                     arg_type=auto_pause_delay_param_type)

    arg_ctx.argument('min_capacity',
                     arg_type=min_capacity_param_type)

    arg_ctx.argument('read_scale',
                     arg_type=read_scale_param_type)

    arg_ctx.argument('high_availability_replica_count',
                     arg_type=read_replicas_param_type)

    creation_arg_group = 'Creation'

    arg_ctx.argument('collation',
                     arg_group=creation_arg_group)

    arg_ctx.argument('catalog_collation',
                     arg_group=creation_arg_group,
                     arg_type=get_enum_type(CatalogCollationType))

    # WideWorldImportersStd and WideWorldImportersFull cannot be successfully created.
    # AdventureWorksLT is the only sample name that is actually supported.
    arg_ctx.argument('sample_name',
                     arg_group=creation_arg_group,
                     arg_type=get_enum_type([SampleName.adventure_works_lt]))

    arg_ctx.argument('license_type',
                     arg_type=get_enum_type(DatabaseLicenseType))

    arg_ctx.argument('zone_redundant',
                     arg_type=zone_redundant_param_type)


def _configure_db_dw_create_params(
        arg_ctx,
        engine,
        create_mode):
    """
    Configures params for db/dw create commands.

    The PUT database REST API has many parameters and many modes (`create_mode`) that control
    which parameters are valid. To make it easier for CLI users to get the param combinations
    correct, these create modes are separated into different commands (e.g.: create, copy,
    restore, etc).

    On top of that, some create modes and some params are not allowed if the database edition is
    DataWarehouse. For this reason, regular database commands are separated from datawarehouse
    commands (`db` vs `dw`.)

    As a result, the param combination matrix is a little complicated. When adding a new param,
    we want to make sure that the param is visible for the appropriate commands. We also want to
    avoid duplication. Instead of spreading out & duplicating the param definitions across all
    the different commands, it has been more effective to define this reusable function.

    The main task here is to create extra params based on the `Database` model, then .ignore() the params that
    aren't applicable to the specified engine and create mode. There is also some minor tweaking of help text
    to make the help text more specific to creation.

    engine: Engine enum value (e.g. `db`, `dw`)
    create_mode: Valid CreateMode enum value (e.g. `default`, `copy`, etc)
    """

    # *** Step 0: Validation ***

    # DW does not support all create modes. Check that engine and create_mode are consistent.
    if engine == Engine.dw and create_mode not in [
            CreateMode.default,
            CreateMode.point_in_time_restore,
            CreateMode.restore]:
        raise ValueError('Engine {} does not support create mode {}'.format(engine, create_mode))

    # *** Step 1: Create extra params ***

    # Create args that will be used to build up the Database object
    #
    # IMPORTANT: It is very easy to add a new parameter and accidentally forget to .ignore() it in
    # some commands that it is not applicable to. Therefore, when adding a new param, you should compare
    # command help before & after your change.
    # e.g.:
    #
    #   # Get initial help text
    #   git checkout dev
    #   $file = 'help_original.txt'
    #   az sql db create -h >> $file
    #   az sql db copy -h >> $file
    #   az sql db restore -h >> $file
    #   az sql db replica create -h >> $file
    #   az sql db update -h >> $file
    #   az sql dw create -h >> $file
    #   az sql dw update -h >> $file
    #
    #   # Get updated help text
    #   git checkout mybranch
    #   $file = 'help_updated.txt'
    #   az sql db create -h >> $file
    #   az sql db copy -h >> $file
    #   az sql db restore -h >> $file
    #   az sql db replica create -h >> $file
    #   az sql db update -h >> $file
    #   az sql dw create -h >> $file
    #   az sql dw update -h >> $file
    #
    # Then compare 'help_original.txt' <-> 'help_updated.txt' in your favourite text diff tool.
    create_args_for_complex_type(
        arg_ctx, 'parameters', Database, [
            'catalog_collation',
            'collation',
            'elastic_pool_id',
            'license_type',
            'max_size_bytes',
            'name',
            'restore_point_in_time',
            'sample_name',
            'sku',
            'source_database_deletion_date',
            'tags',
            'zone_redundant',
            'auto_pause_delay',
            'min_capacity',
            'compute_model',
            'read_scale',
            'high_availability_replica_count',
            'requested_backup_storage_redundancy',
            'maintenance_configuration_id',
            'is_ledger_on',
        ])

    # Create args that will be used to build up the Database's Sku object
    create_args_for_complex_type(
        arg_ctx, 'sku', Sku, [
            'capacity',
            'family',
            'name',
            'tier',
        ])

    # *** Step 2: Apply customizations specific to create (as opposed to update) ***

    arg_ctx.argument('name',  # Note: this is sku name, not database name
                     options_list=['--service-objective'],
                     arg_group=sku_arg_group,
                     required=False,
                     help='The service objective for the new database. For example: ' +
                     (db_service_objective_examples if engine == Engine.db else dw_service_objective_examples))

    arg_ctx.argument('elastic_pool_id',
                     help='The name or resource id of the elastic pool to create the database in.')

    arg_ctx.argument('requested_backup_storage_redundancy',
                     arg_type=backup_storage_redundancy_param_type)

    arg_ctx.argument('maintenance_configuration_id',
                     arg_type=maintenance_configuration_id_param_type)

    arg_ctx.argument('is_ledger_on',
                     arg_type=ledger_on_param_type)

    # *** Step 3: Ignore params that are not applicable (based on engine & create mode) ***

    # Only applicable to default create mode. Also only applicable to db.
    if create_mode != CreateMode.default or engine != Engine.db:
        arg_ctx.ignore('sample_name')
        arg_ctx.ignore('catalog_collation')
        arg_ctx.ignore('maintenance_configuration_id')
        arg_ctx.ignore('is_ledger_on')

    # Only applicable to point in time restore or deleted restore create mode.
    if create_mode not in [CreateMode.restore, CreateMode.point_in_time_restore]:
        arg_ctx.ignore('restore_point_in_time', 'source_database_deletion_date')

    # 'collation', 'tier', and 'max_size_bytes' are ignored (or rejected) when creating a copy
    # or secondary because their values are determined by the source db.
    if create_mode in [CreateMode.copy, CreateMode.secondary]:
        arg_ctx.ignore('collation', 'tier', 'max_size_bytes')

    # collation and max_size_bytes are ignored when restoring because their values are determined by
    # the source db.
    if create_mode in [CreateMode.restore, CreateMode.point_in_time_restore]:
        arg_ctx.ignore('collation', 'max_size_bytes')

    if engine == Engine.dw:
        # Elastic pool is only for SQL DB.
        arg_ctx.ignore('elastic_pool_id')

        # Edition is always 'DataWarehouse'
        arg_ctx.ignore('tier')

        # License types do not yet exist for DataWarehouse
        arg_ctx.ignore('license_type')

        # Family is not applicable to DataWarehouse
        arg_ctx.ignore('family')

        # Provisioning with capacity is not applicable to DataWarehouse
        arg_ctx.ignore('capacity')

        # Serverless offerings are not applicable to DataWarehouse
        arg_ctx.ignore('auto_pause_delay')
        arg_ctx.ignore('min_capacity')
        arg_ctx.ignore('compute_model')

        # ReadScale properties are not valid for DataWarehouse
        # --read-replica-count was accidentally included in previous releases and
        # therefore is hidden using `deprecate_info` instead of `ignore`
        arg_ctx.ignore('read_scale')
        arg_ctx.ignore('high_availability_replica_count')
        arg_ctx.argument('read_replica_count',
                         options_list=['--read-replica-count'],
                         deprecate_info=arg_ctx.deprecate(hide=True))

        # Zone redundant was accidentally included in previous releases and
        # therefore is hidden using `deprecate_info` instead of `ignore`
        arg_ctx.argument('zone_redundant',
                         options_list=['--zone-redundant'],
                         deprecate_info=arg_ctx.deprecate(hide=True))


# pylint: disable=too-many-statements
def load_arguments(self, _):

    with self.argument_context('sql') as c:
        c.argument('location_name', arg_type=get_location_type(self.cli_ctx))
        c.argument('usage_name', options_list=['--usage', '-u'])
        c.argument('tags', arg_type=tags_type)
        c.argument('allow_data_loss',
                   help='If specified, the failover operation will allow data loss.')

    with self.argument_context('sql db') as c:
        _configure_db_dw_params(c)

        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('database_name',
                   options_list=['--name', '-n'],
                   help='Name of the Azure SQL Database.',
                   # Allow --ids command line argument. id_part=child_name_1 is 2nd name in uri
                   id_part='child_name_1')

        # SKU-related params are different from DB versus DW, so we want this configuration to apply here
        # in 'sql db' group but not in 'sql dw' group. If we wanted to apply to both, we would put the
        # configuration into _configure_db_dw_params().
        c.argument('tier',
                   arg_type=tier_param_type,
                   help='The edition component of the sku. Allowed values include: Basic, Standard, '
                   'Premium, GeneralPurpose, BusinessCritical, Hyperscale.')

        c.argument('capacity',
                   arg_type=capacity_param_type,
                   arg_group=sku_component_arg_group,
                   help='The capacity component of the sku in integer number of DTUs or vcores.')

        c.argument('family',
                   arg_type=family_param_type,
                   help='The compute generation component of the sku (for vcore skus only). '
                   'Allowed values include: Gen4, Gen5.')

    with self.argument_context('sql db create') as c:
        _configure_db_dw_create_params(c, Engine.db, CreateMode.default)

        c.argument('yes',
                   options_list=['--yes', '-y'],
                   help='Do not prompt for confirmation.', action='store_true')

    with self.argument_context('sql db copy') as c:
        _configure_db_dw_create_params(c, Engine.db, CreateMode.copy)

        c.argument('dest_name',
                   help='Name of the database that will be created as the copy destination.')

        c.argument('dest_resource_group_name',
                   options_list=['--dest-resource-group'],
                   help='Name of the resouce group to create the copy in.'
                   ' If unspecified, defaults to the origin resource group.')

        c.argument('dest_server_name',
                   options_list=['--dest-server'],
                   help='Name of the server to create the copy in.'
                   ' If unspecified, defaults to the origin server.')

    with self.argument_context('sql db rename') as c:
        c.argument('new_name',
                   help='The new name that the database will be renamed to.')

    with self.argument_context('sql db restore') as c:
        _configure_db_dw_create_params(c, Engine.db, CreateMode.point_in_time_restore)

        c.argument('dest_name',
                   help='Name of the database that will be created as the restore destination.')

        restore_point_arg_group = 'Restore Point'

        c.argument('restore_point_in_time',
                   options_list=['--time', '-t'],
                   arg_group=restore_point_arg_group,
                   help='The point in time of the source database that will be restored to create the'
                   ' new database. Must be greater than or equal to the source database\'s'
                   ' earliestRestoreDate value. Either --time or --deleted-time (or both) must be specified. ' +
                   time_format_help)

        c.argument('source_database_deletion_date',
                   options_list=['--deleted-time'],
                   arg_group=restore_point_arg_group,
                   help='If specified, restore from a deleted database instead of from an existing database.'
                   ' Must match the deleted time of a deleted database in the same server.'
                   ' Either --time or --deleted-time (or both) must be specified. ' +
                   time_format_help)

    with self.argument_context('sql db show') as c:
        # Service tier advisors and transparent data encryption are not included in the first batch
        # of GA commands.
        c.ignore('expand')

    with self.argument_context('sql db list') as c:
        c.argument('elastic_pool_name',
                   options_list=['--elastic-pool'],
                   help='If specified, lists only the databases in this elastic pool')

    with self.argument_context('sql db list-editions') as c:
        c.argument('show_details',
                   options_list=['--show-details', '-d'],
                   help='List of additional details to include in output.',
                   nargs='+',
                   arg_type=get_enum_type(DatabaseCapabilitiesAdditionalDetails))

        c.argument('available', arg_type=available_param_type)

        search_arg_group = 'Search'

        # We could used get_enum_type here, but that will validate the inputs which means there
        # will be no way to query for new editions/service objectives that are made available after
        # this version of CLI is released.
        c.argument('edition',
                   arg_type=tier_param_type,
                   arg_group=search_arg_group,
                   help='Edition to search for. If unspecified, all editions are shown.')

        c.argument('service_objective',
                   arg_group=search_arg_group,
                   help='Service objective to search for. If unspecified, all service objectives are shown.')

        c.argument('dtu',
                   arg_group=search_arg_group,
                   help='Number of DTUs to search for. If unspecified, all DTU sizes are shown.')

        c.argument('vcores',
                   arg_group=search_arg_group,
                   help='Number of vcores to search for. If unspecified, all vcore sizes are shown.')

    with self.argument_context('sql db update') as c:
        c.argument('service_objective',
                   arg_group=sku_arg_group,
                   help='The name of the new service objective. If this is a standalone db service'
                   ' objective and the db is currently in an elastic pool, then the db is removed from'
                   ' the pool.')

        c.argument('elastic_pool_id',
                   help='The name or resource id of the elastic pool to move the database into.')

        c.argument('max_size_bytes', help='The new maximum size of the database expressed in bytes.')

        c.argument('requested_backup_storage_redundancy',
                   arg_type=backup_storage_redundancy_param_type)

        c.argument('maintenance_configuration_id', arg_type=maintenance_configuration_id_param_type)

    with self.argument_context('sql db export') as c:
        # Create args that will be used to build up the ExportDatabaseDefinition object
        create_args_for_complex_type(
            c, 'parameters', ExportDatabaseDefinition, [
                'administrator_login',
                'administrator_login_password',
                'authentication_type',
                'storage_key',
                'storage_key_type',
                'storage_uri',
            ])

        c.argument('administrator_login',
                   options_list=['--admin-user', '-u'])

        c.argument('administrator_login_password',
                   options_list=['--admin-password', '-p'])

        c.argument('authentication_type',
                   options_list=['--auth-type', '-a'],
                   arg_type=get_enum_type(AuthenticationType))

        c.argument('storage_key_type',
                   arg_type=get_enum_type(StorageKeyType))

    with self.argument_context('sql db import') as c:
        # Create args that will be used to build up the ImportExistingDatabaseDefinition object
        create_args_for_complex_type(c, 'parameters', ImportExistingDatabaseDefinition, [
            'administrator_login',
            'administrator_login_password',
            'authentication_type',
            'storage_key',
            'storage_key_type',
            'storage_uri'
        ])

        c.argument('administrator_login',
                   options_list=['--admin-user', '-u'])

        c.argument('administrator_login_password',
                   options_list=['--admin-password', '-p'])

        c.argument('authentication_type',
                   options_list=['--auth-type', '-a'],
                   arg_type=get_enum_type(AuthenticationType))

        c.argument('storage_key_type',
                   arg_type=get_enum_type(StorageKeyType))

        # The parameter name '--name' is used for 'database_name', so we need to give a different name
        # for the import extension 'name' parameter to avoid conflicts. This parameter is actually not
        # needed, but we still need to avoid this conflict.
        c.argument('name', options_list=['--not-name'], arg_type=ignore_type)

    with self.argument_context('sql db show-connection-string') as c:
        c.argument('client_provider',
                   options_list=['--client', '-c'],
                   help='Type of client connection provider.',
                   arg_type=get_enum_type(ClientType))

        auth_group = 'Authentication'

        c.argument('auth_type',
                   options_list=['--auth-type', '-a'],
                   arg_group=auth_group,
                   help='Type of authentication.',
                   arg_type=get_enum_type(ClientAuthenticationType))

    #####
    #           sql db op
    #####
    with self.argument_context('sql db op') as c:
        c.argument('database_name',
                   options_list=['--database', '-d'],
                   required=True,
                   help='Name of the Azure SQL Database.')

        c.argument('operation_id',
                   options_list=['--name', '-n'],
                   required=True,
                   help='The unique name of the operation to cancel.')

    #####
    #           sql mi op
    #####
    with self.argument_context('sql mi op') as c:
        c.argument('managed_instance_name',
                   options_list=['--managed-instance', '--mi'],
                   required=True,
                   help='Name of the Azure SQL Managed Instance.')

    with self.argument_context('sql mi op cancel') as c:
        c.argument('operation_id',
                   options_list=['--name', '-n'],
                   required=True,
                   help='The unique name of the operation to cancel.')

    with self.argument_context('sql mi op show') as c:
        c.argument('operation_id',
                   options_list=['--name', '-n'],
                   required=True,
                   help='The unique name of the operation to show.')

    #####
    #           sql db replica
    #####
    with self.argument_context('sql db replica create') as c:
        _configure_db_dw_create_params(c, Engine.db, CreateMode.secondary)

        c.argument('partner_resource_group_name',
                   options_list=['--partner-resource-group'],
                   help='Name of the resource group to create the new replica in.'
                   ' If unspecified, defaults to the origin resource group.')

        c.argument('partner_server_name',
                   options_list=['--partner-server'],
                   help='Name of the server to create the new replica in.')

        c.argument('partner_database_name',
                   options_list=['--partner-database'],
                   help='Name of the new replica.'
                   ' If unspecified, defaults to the source database name.')

        c.argument('secondary_type',
                   options_list=['--secondary-type'],
                   help='Type of secondary to create.'
                   ' Allowed values include: Geo, Named.')

    with self.argument_context('sql db replica set-primary') as c:
        c.argument('database_name',
                   help='Name of the database to fail over.')

        c.argument('server_name',
                   help='Name of the server containing the secondary replica that will become'
                   ' the new primary. ' + server_configure_help)

        c.argument('resource_group_name',
                   help='Name of the resource group containing the secondary replica that'
                   ' will become the new primary.')

    with self.argument_context('sql db replica delete-link') as c:
        c.argument('partner_server_name',
                   options_list=['--partner-server'],
                   help='Name of the server that the other replica is in.')

        c.argument('partner_resource_group_name',
                   options_list=['--partner-resource-group'],
                   help='Name of the resource group that the other replica is in. If unspecified,'
                   ' defaults to the first database\'s resource group.')

    #####
    #           sql db audit-policy & threat-policy
    #####
    def _configure_security_policy_storage_params(arg_ctx):

        arg_ctx.argument('storage_account',
                         options_list=['--storage-account'],
                         arg_group=storage_arg_group,
                         help='Name of the storage account.')

        arg_ctx.argument('storage_account_access_key',
                         options_list=['--storage-key'],
                         arg_group=storage_arg_group,
                         help='Access key for the storage account.')

        arg_ctx.argument('storage_endpoint',
                         arg_group=storage_arg_group,
                         help='The storage account endpoint.')

    with self.argument_context('sql db audit-policy update') as c:
        _configure_security_policy_storage_params(c)

        policy_arg_group = 'Policy'

        c.argument('state',
                   arg_group=policy_arg_group,
                   help='Auditing policy state',
                   arg_type=get_enum_type(BlobAuditingPolicyState))

        c.argument('audit_actions_and_groups',
                   options_list=['--actions'],
                   arg_group=policy_arg_group,
                   help='List of actions and action groups to audit.',
                   nargs='+')

        c.argument('retention_days',
                   arg_group=policy_arg_group,
                   help='The number of days to retain audit logs.')

        c.argument('blob_storage_target_state',
                   blob_storage_target_state_param_type)

        c.argument('log_analytics_target_state',
                   log_analytics_target_state_param_type)

        c.argument('log_analytics_workspace_resource_id',
                   log_analytics_workspace_resource_id_param_type)

        c.argument('event_hub_target_state',
                   event_hub_target_state_param_type)

        c.argument('event_hub_authorization_rule_id',
                   event_hub_authorization_rule_id_param_type)

        c.argument('event_hub', event_hub_param_type)

    with self.argument_context('sql db threat-policy update') as c:
        _configure_security_policy_storage_params(c)

        policy_arg_group = 'Policy'
        notification_arg_group = 'Notification'

        c.argument('state',
                   arg_group=policy_arg_group,
                   help='Threat detection policy state',
                   arg_type=get_enum_type(SecurityAlertPolicyState))

        c.argument('retention_days',
                   arg_group=policy_arg_group,
                   help='The number of days to retain threat detection logs.')

        c.argument('disabled_alerts',
                   arg_group=policy_arg_group,
                   options_list=['--disabled-alerts'],
                   help='List of disabled alerts.',
                   nargs='+')

        c.argument('email_addresses',
                   arg_group=notification_arg_group,
                   options_list=['--email-addresses'],
                   help='List of email addresses that alerts are sent to.',
                   nargs='+')

        c.argument('email_account_admins',
                   arg_group=notification_arg_group,
                   options_list=['--email-account-admins'],
                   help='Whether the alert is sent to the account administrators.')

        # TODO: use server default

    #####
    #           sql db transparent-data-encryption
    #####
    with self.argument_context('sql db tde') as c:
        c.argument('database_name',
                   options_list=['--database', '-d'],
                   required=True,
                   help='Name of the Azure SQL Database.')

    with self.argument_context('sql db tde set') as c:
        c.argument('status',
                   options_list=['--status'],
                   required=True,
                   help='Status of the transparent data encryption.',
                   arg_type=get_enum_type(TransparentDataEncryptionStatus))

    #####
    #           sql db ledger-digest-uploads
    ######
    with self.argument_context('sql db ledger-digest-uploads enable') as c:
        c.argument('endpoint',
                   options_list=['--endpoint'],
                   help='The endpoint of a digest storage, '
                   'which can be either an Azure Blob storage or a ledger in Azure Confidential Ledger.')

    ###############################################
    #                sql db ltr                   #
    ###############################################
    with self.argument_context('sql db ltr-policy set') as c:
        create_args_for_complex_type(
            c, 'parameters', Database, [
                'weekly_retention',
                'monthly_retention',
                'yearly_retention',
                'week_of_year'])

        c.argument('weekly_retention',
                   help='Retention for the weekly backup. '
                   'If just a number is passed instead of an ISO 8601 string, days will be assumed as the units.'
                   'There is a minimum of 7 days and a maximum of 10 years.')

        c.argument('monthly_retention',
                   help='Retention for the monthly backup. '
                   'If just a number is passed instead of an ISO 8601 string, days will be assumed as the units.'
                   'There is a minimum of 7 days and a maximum of 10 years.')

        c.argument('yearly_retention',
                   help='Retention for the yearly backup. '
                   'If just a number is passed instead of an ISO 8601 string, days will be assumed as the units.'
                   'There is a minimum of 7 days and a maximum of 10 years.')

        c.argument('week_of_year',
                   help='The Week of Year, 1 to 52, in which to take the yearly LTR backup.')

    with self.argument_context('sql db ltr-backup') as c:
        c.argument('location_name',
                   required=True,
                   arg_type=get_location_type(self.cli_ctx),
                   help='The location of the desired backups.')

        c.argument('backup_name',
                   options_list=['--name', '-n'],
                   help='The name of the LTR backup. '
                   'Use \'az sql db ltr-backup show\' or \'az sql db ltr-backup list\' for backup name.')

        c.argument('long_term_retention_server_name',
                   options_list=['--server', '-s'],
                   help='Name of the Azure SQL Server. '
                   'If specified, retrieves all requested backups under this server.')

        c.argument('long_term_retention_database_name',
                   options_list=['--database', '-d'],
                   help='Name of the Azure SQL Database. '
                   'If specified (along with server name), retrieves all requested backups under this database.')

    with self.argument_context('sql db ltr-backup list') as c:
        c.argument('database_state',
                   required=False,
                   options_list=['--database-state', '--state'],
                   help='\'All\', \'Live\', or \'Deleted\'. '
                   'Will fetch backups only from databases of specified state. '
                   'If no state provied, defaults to \'All\'.')

        c.argument('only_latest_per_database',
                   options_list=['--only-latest-per-database', '--latest'],
                   required=False,
                   help='If true, will only return the latest backup for each database')

    with self.argument_context('sql db ltr-backup restore') as c:
        c.argument('target_database_name',
                   options_list=['--dest-database'],
                   required=True,
                   help='Name of the database that will be created as the restore destination.')

        c.argument('target_server_name',
                   options_list=['--dest-server'],
                   required=True,
                   help='Name of the server to restore database to.')

        c.argument('target_resource_group_name',
                   options_list=['--dest-resource-group'],
                   required=True,
                   help='Name of the resource group of the server to restore database to.')

        c.argument('long_term_retention_backup_resource_id',
                   options_list=['--backup-id'],
                   required=True,
                   help='The resource id of the long term retention backup to be restored. '
                   'Use \'az sql db ltr-backup show\' or \'az sql db ltr-backup list\' for backup id.')

        c.argument('requested_backup_storage_redundancy',
                   required=False,
                   arg_type=backup_storage_redundancy_param_type)

    ###############################################
    #                sql db str                   #
    ###############################################
    with self.argument_context('sql db str-policy set') as c:
        create_args_for_complex_type(
            c, 'parameters', Database, [
                'retention_days',
                'diffbackup_hours'
            ])

        c.argument(
            'retention_days',
            options_list=['--retention-days'],
            required=True,
            help='New backup short term retention policy retention in days.'
            'Valid retention days for live database of (DTU) Basic can be 1-7 days; Rest models can be 1-35 days.')

        c.argument(
            'diffbackup_hours',
            options_list=['--diffbackup-hours'],
            required=True,
            help='New backup short term retention policy differential backup interval in hours.'
            'Valid differential backup interval for live database can be 12 or 24 hours.')

    ###############################################
    #                sql dw                       #
    ###############################################
    with self.argument_context('sql dw') as c:
        _configure_db_dw_params(c)

        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('database_name',
                   options_list=['--name', '-n'],
                   help='Name of the data warehouse.',
                   # Allow --ids command line argument. id_part=child_name_1 is 2nd name in uri
                   id_part='child_name_1')

        c.argument('service_objective',
                   help='The service objective of the data warehouse. For example: ' +
                   dw_service_objective_examples)

        c.argument('collation',
                   help='The collation of the data warehouse.')

    with self.argument_context('sql dw create') as c:
        _configure_db_dw_create_params(c, Engine.dw, CreateMode.default)

    with self.argument_context('sql dw show') as c:
        # Service tier advisors and transparent data encryption are not included in the first batch
        # of GA commands.
        c.ignore('expand')

    # Data Warehouse restore will not be included in the first batch of GA commands
    # (list_restore_points also applies to db, but it's not very useful. It's
    # mainly useful for dw.)
    # with ParametersContext(command='sql dw restore-point') as c:
    #     c.register_alias('database_name', ('--database', '-d'))

    ###############################################
    #                sql elastic-pool             #
    ###############################################
    with self.argument_context('sql elastic-pool') as c:
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('elastic_pool_name',
                   options_list=['--name', '-n'],
                   help='The name of the elastic pool.',
                   # Allow --ids command line argument. id_part=child_name_1 is 2nd name in uri
                   id_part='child_name_1')

        # --db-dtu-max and --db-dtu-min were the original param names, which is consistent with the
        # 2014-04-01 REST API.
        # --db-max-dtu and --db-min-dtu are aliases which are consistent with the `sql elastic-pool
        # list-editions --show-details db-max-dtu db-min-dtu` parameter values. These are more
        # consistent with other az sql commands, but the original can't be removed due to
        # compatibility.
        c.argument('max_capacity',
                   options_list=['--db-dtu-max', '--db-max-dtu', '--db-max-capacity'],
                   help='The maximum capacity (in DTUs or vcores) any one database can consume.')

        c.argument('min_capacity',
                   options_list=['--db-dtu-min', '--db-min-dtu', '--db-min-capacity'],
                   help='The minumum capacity (in DTUs or vcores) each database is guaranteed.')

        # --storage was the original param name, which is consistent with the underlying REST API.
        # --max-size is an alias which is consistent with the `sql elastic-pool list-editions
        # --show-details max-size` parameter value and also matches `sql db --max-size` parameter name.
        c.argument('max_size_bytes',
                   arg_type=max_size_bytes_param_type,
                   options_list=['--max-size', '--storage'])

        c.argument('license_type',
                   arg_type=get_enum_type(ElasticPoolLicenseType))

        c.argument('zone_redundant',
                   arg_type=zone_redundant_param_type)

        c.argument('tier',
                   arg_type=tier_param_type,
                   help='The edition component of the sku. Allowed values include: Basic, Standard, '
                   'Premium, GeneralPurpose, BusinessCritical.')

        c.argument('capacity',
                   arg_type=capacity_or_dtu_param_type,
                   help='The capacity component of the sku in integer number of DTUs or vcores.')

        c.argument('family',
                   arg_type=family_param_type,
                   help='The compute generation component of the sku (for vcore skus only). '
                   'Allowed values include: Gen4, Gen5.')

        c.argument('maintenance_configuration_id',
                   arg_type=maintenance_configuration_id_param_type)

    with self.argument_context('sql elastic-pool create') as c:
        # Create args that will be used to build up the ElasticPool object
        create_args_for_complex_type(
            c, 'parameters', ElasticPool, [
                'license_type',
                'max_size_bytes',
                'name',
                'per_database_settings',
                'tags',
                'zone_redundant',
                'maintenance_configuration_id',
            ])

        # Create args that will be used to build up the ElasticPoolPerDatabaseSettings object
        create_args_for_complex_type(
            c, 'per_database_settings', ElasticPoolPerDatabaseSettings, [
                'max_capacity',
                'min_capacity',
            ])

        # Create args that will be used to build up the ElasticPool Sku object
        create_args_for_complex_type(
            c, 'sku', Sku, [
                'capacity',
                'family',
                'name',
                'tier',
            ])

        c.ignore('name')  # Hide sku name

    with self.argument_context('sql elastic-pool list-editions') as c:
        # Note that `ElasticPoolCapabilitiesAdditionalDetails` intentionally match param names to
        # other commands, such as `sql elastic-pool create --db-max-dtu --db-min-dtu --max-size`.
        c.argument('show_details',
                   options_list=['--show-details', '-d'],
                   help='List of additional details to include in output.',
                   nargs='+',
                   arg_type=get_enum_type(ElasticPoolCapabilitiesAdditionalDetails))

        c.argument('available',
                   arg_type=available_param_type)

        search_arg_group = 'Search'

        # We could used 'arg_type=get_enum_type' here, but that will validate the inputs which means there
        # will be no way to query for new editions that are made available after
        # this version of CLI is released.
        c.argument('edition',
                   arg_type=tier_param_type,
                   arg_group=search_arg_group,
                   help='Edition to search for. If unspecified, all editions are shown.')

        c.argument('dtu',
                   arg_group=search_arg_group,
                   help='Number of DTUs to search for. If unspecified, all DTU sizes are shown.')

        c.argument('vcores',
                   arg_group=search_arg_group,
                   help='Number of vcores to search for. If unspecified, all vcore sizes are shown.')

    with self.argument_context('sql elastic-pool update') as c:
        c.argument('database_dtu_max',
                   help='The maximum DTU any one database can consume.')

        c.argument('database_dtu_min',
                   help='The minimum DTU all databases are guaranteed.')

        c.argument('storage_mb',
                   help='Storage limit for the elastic pool in MB.')

    #####
    #           sql elastic-pool op
    #####
    with self.argument_context('sql elastic-pool op') as c:
        c.argument('elastic_pool_name',
                   options_list=['--elastic-pool'],
                   help='Name of the Azure SQL Elastic Pool.')

        c.argument('operation_id',
                   options_list=['--name', '-n'],
                   help='The unique name of the operation to cancel.')

    ###############################################
    #             sql failover-group              #
    ###############################################

    with self.argument_context('sql failover-group') as c:
        c.argument('failover_group_name', options_list=['--name', '-n'], help="The name of the Failover Group")
        c.argument('server_name', arg_type=server_param_type)
        c.argument('partner_server', help="The name of the partner server of a Failover Group")
        c.argument('partner_resource_group', help="The name of the resource group of the partner server")
        c.argument('failover_policy', help="The failover policy of the Failover Group",
                   arg_type=get_enum_type(FailoverPolicyType))
        c.argument('grace_period',
                   arg_type=grace_period_param_type)
        c.argument('add_db', nargs='+',
                   help='List of databases to add to Failover Group')
        c.argument('remove_db', nargs='+',
                   help='List of databases to remove from Failover Group')
        c.argument('allow_data_loss',
                   arg_type=allow_data_loss_param_type)

    ###############################################
    #             sql instance pool               #
    ###############################################

    with self.argument_context('sql instance-pool') as c:
        c.argument('instance_pool_name',
                   options_list=['--name', '-n'],
                   help="Instance Pool Name")

        c.argument(
            'tier',
            arg_type=tier_param_type,
            required=True,
            help='The edition component of the sku. Allowed value: GeneralPurpose.')

        c.argument('family',
                   arg_type=family_param_type,
                   required=True,
                   help='The compute generation component of the sku. '
                   'Allowed value: Gen5')

        c.argument('license_type',
                   arg_type=get_enum_type(DatabaseLicenseType),
                   help='The license type to apply for this instance pool.')

    with self.argument_context('sql instance-pool create') as c:
        # Create args that will be used to build up the InstancePool object
        create_args_for_complex_type(
            c, 'parameters', InstancePool, [
                'location',
                'license_type',
                'subnet_id',
                'vcores',
                'tags'
            ])

        c.argument('vcores',
                   required=True,
                   arg_type=capacity_param_type,
                   help='Capacity of the instance pool in vcores.')

        c.argument(
            'subnet_id',
            options_list=['--subnet'],
            required=True,
            help='Name or ID of the subnet that allows access to an Instance Pool. '
                 'If subnet name is provided, --vnet-name must be provided.')

        # Create args that will be used to build up the Instance Pool's Sku object
        create_args_for_complex_type(
            c, 'sku', Sku, [
                'family',
                'name',
                'tier',
            ])

        c.ignore('name')  # Hide sku name

        c.extra('vnet_name',
                options_list=['--vnet-name'],
                help='The virtual network name',
                validator=validate_subnet)

    ###############################################
    #                sql server                   #
    ###############################################
    with self.argument_context('sql server') as c:
        c.argument('server_name',
                   arg_type=server_param_type,
                   options_list=['--name', '-n'])

        c.argument('administrator_login',
                   options_list=['--admin-user', '-u'])

        c.argument('administrator_login_password',
                   options_list=['--admin-password', '-p'])

        c.argument('assign_identity',
                   options_list=['--assign_identity', '-i'],
                   help='Generate and assign an Azure Active Directory Identity for this server '
                   'for use with key management services like Azure KeyVault.')

        c.argument('minimal_tls_version',
                   arg_type=get_enum_type(SqlServerMinimalTlsVersionType),
                   help='The minimal TLS version enforced by the sql server for inbound connections.')

        c.argument('enable_public_network',
                   options_list=['--enable-public-network', '-e'],
                   arg_type=get_three_state_flag(),
                   help='Set whether public network access to server is allowed or not. When false,'
                   'only connections made through Private Links can reach this server.',
                   is_preview=True)

        c.argument('restrict_outbound_network_access',
                   options_list=['--restrict-outbound-network-access', '-r'],
                   arg_type=get_three_state_flag(),
                   help='Set whether outbound network access to server is restricted or not. When true,'
                   'the outbound connections from the server will be restricted.',
                   is_preview=True)

        c.argument('primary_user_assigned_identity_id',
                   options_list=['--primary-user-assigned-identity-id', '--pid'],
                   help='The ID of the primary user managed identity.')

        c.argument('key_id',
                   options_list=['--key-id', '-k'],
                   help='The key vault URI for encryption.')

        c.argument('user_assigned_identity_id',
                   options_list=['--user-assigned-identity-id', '-a'],
                   nargs='+',
                   help='Generate and assign an User Managed Identity(UMI) for this server.')

        c.argument('identity_type',
                   options_list=['--identity-type', '-t'],
                   arg_type=get_enum_type(ResourceIdType),
                   help='Type of Identity to be used. Possible values are SystemAsssigned,'
                   'UserAssigned, SystemAssigned,UserAssigned and None.')

        c.argument('federated_client_id',
                   options_list=['--federated-client-id', '--fid'],
                   help='The federated client id used in cross tenant CMK scenario.')

    with self.argument_context('sql server create') as c:
        c.argument('location',
                   arg_type=get_location_type_with_default_from_resource_group(self.cli_ctx))

        # Create args that will be used to build up the Server object
        create_args_for_complex_type(
            c, 'parameters', Server, [
                'administrator_login',
                'administrator_login_password',
                'location',
                'minimal_tls_version'
            ])

        c.argument('administrator_login',
                   required=False)

        c.argument('administrator_login_password',
                   required=False)

        c.argument('assign_identity',
                   options_list=['--assign-identity', '-i'],
                   help='Generate and assign an Azure Active Directory Identity for this server '
                   'for use with key management services like Azure KeyVault.')

        c.argument('enable_ad_only_auth',
                   options_list=['--enable-ad-only-auth'],
                   help='Enable Azure Active Directory Only Authentication for this server.')

        c.argument('external_admin_name',
                   options_list=['--external-admin-name'],
                   help='Display name of the Azure AD administrator user, group or application.')

        c.argument('external_admin_sid',
                   options_list=['--external-admin-sid'],
                   help='The unique ID of the Azure AD administrator. Object Id for User or Group, '
                   'Client Id for Applications')

        c.argument('external_admin_principal_type',
                   options_list=['--external-admin-principal-type'],
                   help='User, Group or Application')

    with self.argument_context('sql server update') as c:
        c.argument('administrator_login_password',
                   help='The administrator login password.')

    with self.argument_context('sql server show') as c:
        c.argument('expand_ad_admin',
                   options_list=['--expand-ad-admin'],
                   help='Expand the Active Directory Administrator for the server.')

    with self.argument_context('sql server list') as c:
        c.argument('expand_ad_admin',
                   options_list=['--expand-ad-admin'],
                   help='Expand the Active Directory Administrator for the server.')

    #####
    #           sql server ad-admin
    ######
    with self.argument_context('sql server ad-admin') as c:
        # The options list should be ['--server', '-s'], but in the originally released version it was
        # ['--server-name'] which we must keep for backward compatibility - but we should deprecate it.
        c.argument('server_name',
                   options_list=['--server-name', '--server', '-s'])

        c.argument('login',
                   arg_type=aad_admin_login_param_type)

        c.argument('sid',
                   arg_type=aad_admin_sid_param_type)

        c.ignore('tenant_id')

    with self.argument_context('sql server ad-admin create') as c:
        # Create args that will be used to build up the ServerAzureADAdministrator object
        create_args_for_complex_type(
            c, 'parameters', ServerAzureADAdministrator, [
                'login',
                'sid',
            ])

    #####
    #           sql server audit-policy
    ######
    with self.argument_context('sql server audit-policy update') as c:
        c.argument('storage_account',
                   options_list=['--storage-account'],
                   arg_group=storage_arg_group,
                   help='Name of the storage account.')

        c.argument('storage_account_access_key',
                   options_list=['--storage-key'],
                   arg_group=storage_arg_group,
                   help='Access key for the storage account.')

        c.argument('storage_endpoint',
                   arg_group=storage_arg_group,
                   help='The storage account endpoint.')
        _configure_security_policy_storage_params(c)

        policy_arg_group = 'Policy'

        c.argument('state',
                   arg_group=policy_arg_group,
                   help='Auditing policy state',
                   arg_type=get_enum_type(BlobAuditingPolicyState))

        c.argument('audit_actions_and_groups',
                   options_list=['--actions'],
                   arg_group=policy_arg_group,
                   help='List of actions and action groups to audit.',
                   nargs='+')

        c.argument('retention_days',
                   arg_group=policy_arg_group,
                   help='The number of days to retain audit logs.')

        c.argument('blob_storage_target_state',
                   blob_storage_target_state_param_type)

        c.argument('log_analytics_target_state',
                   log_analytics_target_state_param_type)

        c.argument('log_analytics_workspace_resource_id',
                   log_analytics_workspace_resource_id_param_type)

        c.argument('event_hub_target_state',
                   event_hub_target_state_param_type)

        c.argument('event_hub_authorization_rule_id',
                   event_hub_authorization_rule_id_param_type)

        c.argument('event_hub', event_hub_param_type)

    #####
    #           sql server ms-support audit-policy
    ######
    with self.argument_context('sql server ms-support audit-policy update') as c:
        c.argument('storage_account',
                   options_list=['--storage-account'],
                   arg_group=storage_arg_group,
                   help='Name of the storage account.')

        c.argument('storage_account_access_key',
                   options_list=['--storage-key'],
                   arg_group=storage_arg_group,
                   help='Access key for the storage account.')

        c.argument('storage_endpoint',
                   arg_group=storage_arg_group,
                   help='The storage account endpoint.')
        _configure_security_policy_storage_params(c)

        policy_arg_group = 'Policy'

        c.argument('state',
                   arg_group=policy_arg_group,
                   help='Auditing policy state',
                   arg_type=get_enum_type(BlobAuditingPolicyState))

        c.argument('blob_storage_target_state',
                   blob_storage_target_state_param_type)

        c.argument('log_analytics_target_state',
                   log_analytics_target_state_param_type)

        c.argument('log_analytics_workspace_resource_id',
                   log_analytics_workspace_resource_id_param_type)

        c.argument('event_hub_target_state',
                   event_hub_target_state_param_type)

        c.argument('event_hub_authorization_rule_id',
                   event_hub_authorization_rule_id_param_type)

        c.argument('event_hub', event_hub_param_type)

    #####
    #           sql server conn-policy
    #####
    with self.argument_context('sql server conn-policy') as c:
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('connection_type',
                   options_list=['--connection-type', '-t'],
                   arg_type=get_enum_type(ServerConnectionType),
                   help='The required parameters for updating a secure connection policy. The value is default',)

    #####
    #           sql server dns-alias
    #####
    with self.argument_context('sql server dns-alias') as c:
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('dns_alias_name',
                   options_list=('--name', '-n'),
                   help='Name of the DNS alias.')

        c.argument('original_server_name',
                   options_list=('--original-server'),
                   help='The name of the server to which alias is currently pointing')

        c.argument('original_resource_group_name',
                   options_list=('--original-resource-group'),
                   help='Name of the original resource group.')

        c.argument('original_subscription_id',
                   options_list=('--original-subscription-id'),
                   help='ID of the original subscription.')

    #####
    #           sql server firewall-rule
    #####
    with self.argument_context('sql server firewall-rule') as c:
        # Help text needs to be specified because 'sql server firewall-rule update' is a custom
        # command.
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('firewall_rule_name',
                   options_list=['--name', '-n'],
                   help='The name of the firewall rule.',
                   # Allow --ids command line argument. id_part=child_name_1 is 2nd name in uri
                   id_part='child_name_1')

        c.argument('start_ip_address',
                   options_list=['--start-ip-address'],
                   help='The start IP address of the firewall rule. Must be IPv4 format. Use value'
                   ' \'0.0.0.0\' to represent all Azure-internal IP addresses.')

        c.argument('end_ip_address',
                   options_list=['--end-ip-address'],
                   help='The end IP address of the firewall rule. Must be IPv4 format. Use value'
                   ' \'0.0.0.0\' to represent all Azure-internal IP addresses.')

    #####
    #           sql server outbound firewall-rule
    #####
    with self.argument_context('sql server outbound-firewall-rule') as c:
        # Help text needs to be specified because 'sql server outbound-firewall-rule update' is a custom
        # command.
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('outbound_rule_fqdn',
                   options_list=['--outbound-rule-fqdn', '-n'],
                   help='The allowed FQDN for the outbound firewall rule.')

    #####
    #           sql server key
    #####
    with self.argument_context('sql server key') as c:
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('key_name',
                   options_list=['--name', '-n'])

        c.argument('kid',
                   arg_type=kid_param_type,
                   required=True)

    #####
    #           sql server tde-key
    #####
    with self.argument_context('sql server tde-key') as c:
        c.argument('server_name',
                   arg_type=server_param_type)

    with self.argument_context('sql server tde-key set') as c:
        c.argument('kid',
                   arg_type=kid_param_type)

        c.argument('server_key_type',
                   arg_type=server_key_type_param_type)

        c.argument('auto_rotation_enabled',
                   options_list=['--auto-rotation-enabled'],
                   help='The key auto rotation opt in status. Can be either true or false.',
                   arg_type=get_three_state_flag())

    #####
    #           sql server vnet-rule
    #####
    with self.argument_context('sql server vnet-rule') as c:
        # Help text needs to be specified because 'sql server vnet-rule create' is a custom
        # command.
        c.argument('server_name',
                   arg_type=server_param_type)

        c.argument('virtual_network_rule_name',
                   options_list=['--name', '-n'],
                   help='The name of the virtual network rule.')

        c.argument('virtual_network_subnet_id',
                   options_list=['--subnet'],
                   help='Name or ID of the subnet that allows access to an Azure Sql Server. '
                   'If subnet name is provided, --vnet-name must be provided.')

        c.argument('ignore_missing_vnet_service_endpoint',
                   options_list=['--ignore-missing-endpoint', '-i'],
                   help='Create firewall rule before the virtual network has vnet service endpoint enabled',
                   arg_type=get_three_state_flag())

    with self.argument_context('sql server vnet-rule create') as c:
        c.extra('vnet_name',
                options_list=['--vnet-name'],
                help='The virtual network name')

    ###############################################
    #           sql server trust groups           #
    ###############################################

    with self.argument_context('sql stg') as c:
        c.argument('resource_group_name',
                   help='The resource group name')

    with self.argument_context('sql stg create') as c:
        c.argument('name',
                   options_list=['--name', '-n'],
                   help='The name of the Server Trust Group.')

        c.argument('location',
                   help='The location name of the Server Trust Group.')

        c.argument('group_member',
                   options_list=['--group-member', '-m'],
                   help="""Managed Instance that is to be a member of the group.
                   Specify resource group, subscription id and the name of the instance.""",
                   nargs='+')

        c.argument('trust_scope',
                   help='The trust scope of the Server Trust Group.',
                   nargs='+')

    with self.argument_context('sql stg show') as c:
        c.argument('location',
                   help='The location of the Server Trust Group.')

        c.argument('name',
                   options_list=['--name', '-n'],
                   help='The name of the Server Trust Group.')

    with self.argument_context('sql stg delete') as c:
        c.argument('location',
                   help='The location of the Server Trust Group.')

        c.argument('name',
                   options_list=['--name', '-n'],
                   help='The name of the Server Trust Group.')

    with self.argument_context('sql stg list') as c:
        c.argument('location',
                   help='The location of the Server Trust Group.',
                   arg_group='List By Location')

        c.argument('instance_name',
                   help='Managed Instance name.',
                   arg_group='List By Instance')

    ###############################################
    #                sql managed instance         #
    ###############################################
    with self.argument_context('sql mi') as c:
        c.argument('managed_instance_name',
                   help='The managed instance name',
                   options_list=['--name', '-n'],
                   # Allow --ids command line argument. id_part=name is 1st name in uri
                   id_part='name')

        c.argument('tier',
                   arg_type=tier_param_type,
                   help='The edition component of the sku. Allowed values include: '
                   'GeneralPurpose, BusinessCritical.')

        c.argument('family',
                   arg_type=family_param_type,
                   help='The compute generation component of the sku. '
                   'Allowed values include: Gen4, Gen5.')

        c.argument('storage_size_in_gb',
                   options_list=['--storage'],
                   arg_type=storage_param_type,
                   help='The storage size of the managed instance. '
                   'Storage size must be specified in increments of 32 GB')

        c.argument('license_type',
                   arg_type=get_enum_type(DatabaseLicenseType),
                   help='The license type to apply for this managed instance.')

        c.argument('vcores',
                   arg_type=capacity_param_type,
                   help='The capacity of the managed instance in integer number of vcores.')

        c.argument('collation',
                   help='The collation of the managed instance.')

        c.argument('proxy_override',
                   arg_type=get_enum_type(ServerConnectionType),
                   help='The connection type used for connecting to the instance.')

        c.argument('minimal_tls_version',
                   arg_type=get_enum_type(SqlManagedInstanceMinimalTlsVersionType),
                   help='The minimal TLS version enforced by the managed instance for inbound connections.',
                   is_preview=True)

        c.argument('public_data_endpoint_enabled',
                   arg_type=get_three_state_flag(),
                   help='Whether or not the public data endpoint is enabled for the instance.')

        c.argument('timezone_id',
                   help='The time zone id for the instance to set. '
                   'A list of time zone ids is exposed through the sys.time_zone_info (Transact-SQL) view.')

        c.argument('tags', arg_type=tags_type)

        c.argument('primary_user_assigned_identity_id',
                   options_list=['--primary-user-assigned-identity-id', '--pid'],
                   help='The ID of the primary user managed identity.')

        c.argument('key_id',
                   options_list=['--key-id', '-k'],
                   help='The key vault URI for encryption.')

        c.argument('user_assigned_identity_id',
                   options_list=['--user-assigned-identity-id', '-a'],
                   nargs='+',
                   help='Generate and assign an User Managed Identity(UMI) for this server.')

        c.argument('identity_type',
                   options_list=['--identity-type', '-t'],
                   arg_type=get_enum_type(ResourceIdType),
                   help='Type of Identity to be used. Possible values are SystemAsssigned,'
                   'UserAssigned, SystemAssignedUserAssigned and None.')

    with self.argument_context('sql mi create') as c:
        c.argument('location',
                   arg_type=get_location_type_with_default_from_resource_group(self.cli_ctx))

        # Create args that will be used to build up the ManagedInstance object
        create_args_for_complex_type(
            c, 'parameters', ManagedInstance, [
                'administrator_login',
                'administrator_login_password',
                'license_type',
                'minimal_tls_version',
                'virtual_network_subnet_id',
                'vcores',
                'storage_size_in_gb',
                'collation',
                'proxy_override',
                'public_data_endpoint_enabled',
                'timezone_id',
                'tags',
                'storage_account_type',
                'yes',
                'maintenance_configuration_id',
                'primary_user_assigned_identity_id',
                'key_id'
            ])

        # Create args that will be used to build up the Managed Instance's Sku object
        create_args_for_complex_type(
            c, 'sku', Sku, [
                'family',
                'name',
                'tier',
            ])

        c.ignore('name')  # Hide sku name

        c.argument('administrator_login',
                   options_list=['--admin-user', '-u'],
                   required=False)

        c.argument('administrator_login_password',
                   options_list=['--admin-password', '-p'],
                   required=False)

        c.extra('vnet_name',
                options_list=['--vnet-name'],
                help='The virtual network name',
                validator=validate_subnet)

        c.argument('virtual_network_subnet_id',
                   options_list=['--subnet'],
                   required=True,
                   help='Name or ID of the subnet that allows access to an Azure Sql Managed Instance. '
                   'If subnet name is provided, --vnet-name must be provided.')

        c.argument('assign_identity',
                   options_list=['--assign-identity', '-i'],
                   help='Generate and assign an Azure Active Directory Identity for this managed instance '
                   'for use with key management services like Azure KeyVault.')

        c.argument('storage_account_type',
                   arg_type=backup_storage_redundancy_param_type_mi)

        c.argument('yes',
                   options_list=['--yes', '-y'],
                   help='Do not prompt for confirmation.', action='store_true')

        c.argument('maintenance_configuration_id',
                   options_list=['--maint-config-id', '-m'],
                   help='Assign maintenance configuration to this managed instance.')

        c.argument('enable_ad_only_auth',
                   options_list=['--enable-ad-only-auth'],
                   help='Enable Azure Active Directory Only Authentication for this server.')

        c.argument('external_admin_name',
                   options_list=['--external-admin-name'],
                   help='Display name of the Azure AD administrator user, group or application.')

        c.argument('external_admin_sid',
                   options_list=['--external-admin-sid'],
                   help='The unique ID of the Azure AD administrator. Object Id for User or Group, '
                   'Client Id for Applications')

        c.argument('external_admin_principal_type',
                   options_list=['--external-admin-principal-type'],
                   help='User, Group or Application')

    with self.argument_context('sql mi update') as c:
        # Create args that will be used to build up the ManagedInstance object
        create_args_for_complex_type(
            c, 'parameters', ManagedInstance, [
                'administrator_login_password',
                'tags',
            ])

        c.argument('administrator_login_password',
                   options_list=['--admin-password', '-p'])

        c.argument('assign_identity',
                   options_list=['--assign-identity', '-i'],
                   help='Generate and assign an Azure Active Directory Identity for this managed instance '
                   'for use with key management services like Azure KeyVault. '
                   'If identity is already assigned - do nothing.')

        c.argument('maintenance_configuration_id',
                   options_list=['--maint-config-id', '-m'],
                   help='Change maintenance configuration for this managed instance.')

        # Create args that will be used to build up the Managed Instance's Sku object
        create_args_for_complex_type(
            c, 'sku', Sku, [
                'family',
                'name',
                'tier',
            ])

        c.ignore('name')  # Hide sku name

        c.extra('vnet_name',
                options_list=['--vnet-name'],
                help='The virtual network name',
                validator=validate_subnet)

        c.argument('virtual_network_subnet_id',
                   options_list=['--subnet'],
                   required=False,
                   help='Name or ID of the subnet that allows access to an Azure Sql Managed Instance. '
                   'If subnet name is provided, --vnet-name must be provided.')

    with self.argument_context('sql mi show') as c:
        c.argument('expand_ad_admin',
                   options_list=['--expand-ad-admin'],
                   help='Expand the Active Directory Administrator for the server.')

    with self.argument_context('sql mi list') as c:
        c.argument('expand_ad_admin',
                   options_list=['--expand-ad-admin'],
                   help='Expand the Active Directory Administrator for the server.')

    #####
    #           sql managed instance key
    #####
    with self.argument_context('sql mi key') as c:
        c.argument('managed_instance_name',
                   arg_type=managed_instance_param_type)

        c.argument('key_name',
                   options_list=['--name', '-n'])

        c.argument('kid',
                   arg_type=kid_param_type,
                   required=True,)

    #####
    #           sql managed instance ad-admin
    ######
    with self.argument_context('sql mi ad-admin') as c:
        c.argument('managed_instance_name',
                   arg_type=managed_instance_param_type)

        c.argument('login',
                   arg_type=aad_admin_login_param_type)

        c.argument('sid',
                   arg_type=aad_admin_sid_param_type)

    with self.argument_context('sql mi ad-admin create') as c:
        # Create args that will be used to build up the ManagedInstanceAdministrator object
        create_args_for_complex_type(
            c, 'properties', ManagedInstanceAdministrator, [
                'login',
                'sid',
            ])

    with self.argument_context('sql mi ad-admin update') as c:
        # Create args that will be used to build up the ManagedInstanceAdministrator object
        create_args_for_complex_type(
            c, 'properties', ManagedInstanceAdministrator, [
                'login',
                'sid',
            ])

    #####
    #           sql server tde-key
    #####
    with self.argument_context('sql mi tde-key') as c:
        c.argument('managed_instance_name',
                   arg_type=managed_instance_param_type)

    with self.argument_context('sql mi tde-key set') as c:
        c.argument('kid',
                   arg_type=kid_param_type)

        c.argument('server_key_type',
                   arg_type=server_key_type_param_type)

        c.argument('auto_rotation_enabled',
                   options_list=['--auto-rotation-enabled'],
                   help='The key auto rotation opt in status. Can be either true or false.',
                   arg_type=get_three_state_flag())

    ###############################################
    #                sql managed db               #
    ###############################################
    with self.argument_context('sql midb') as c:
        c.argument('managed_instance_name',
                   arg_type=managed_instance_param_type,
                   # Allow --ids command line argument. id_part=name is 1st name in uri
                   id_part='name')

        c.argument('database_name',
                   options_list=['--name', '-n'],
                   help='The name of the Azure SQL Managed Database.',
                   # Allow --ids command line argument. id_part=child_name_1 is 2nd name in uri
                   id_part='child_name_1')

    with self.argument_context('sql midb create') as c:
        create_args_for_complex_type(
            c, 'parameters', ManagedDatabase, [
                'collation',
            ])

        c.argument('collation',
                   required=False,
                   help='The collation of the Azure SQL Managed Database collation to use, '
                   'e.g.: SQL_Latin1_General_CP1_CI_AS or Latin1_General_100_CS_AS_SC')

    with self.argument_context('sql midb restore') as c:
        create_args_for_complex_type(
            c, 'parameters', ManagedDatabase, [
                'deleted_time',
                'target_managed_database_name',
                'target_managed_instance_name',
                'restore_point_in_time'
            ])

        c.argument('deleted_time',
                   options_list=['--deleted-time'],
                   help='If specified, restore from a deleted database instead of from an existing database.'
                   ' Must match the deleted time of a deleted database on the source Managed Instance.')

        c.argument('target_managed_database_name',
                   options_list=['--dest-name'],
                   required=True,
                   help='Name of the managed database that will be created as the restore destination.')

        c.argument('target_managed_instance_name',
                   options_list=['--dest-mi'],
                   help='Name of the managed instance to restore managed database to. '
                   'This can be same managed instance, or another managed instance on same subscription. '
                   'When not specified it defaults to source managed instance.')

        c.argument('target_resource_group_name',
                   options_list=['--dest-resource-group'],
                   help='Name of the resource group of the managed instance to restore managed database to. '
                   'When not specified it defaults to source resource group.')

        restore_point_arg_group = 'Restore Point'

        c.argument('restore_point_in_time',
                   options_list=['--time', '-t'],
                   arg_group=restore_point_arg_group,
                   required=True,
                   help='The point in time of the source database that will be restored to create the'
                   ' new database. Must be greater than or equal to the source database\'s'
                   ' earliestRestoreDate value. ' + time_format_help)

    with self.argument_context('sql midb short-term-retention-policy set') as c:
        create_args_for_complex_type(
            c, 'parameters', ManagedDatabase, [
                'deleted_time',
                'retention_days'
            ])

        c.argument(
            'deleted_time',
            options_list=['--deleted-time'],
            help='If specified, updates retention days for a deleted database, instead of an existing database.'
            'Must match the deleted time of a deleted database on the source Managed Instance.')

        c.argument(
            'retention_days',
            options_list=['--retention-days'],
            required=True,
            help='New backup short term retention policy in days.'
            'Valid policy for live database is 7-35 days, valid policy for dropped databases is 0-35 days.')

    with self.argument_context('sql midb short-term-retention-policy show') as c:
        c.argument(
            'deleted_time',
            options_list=['--deleted-time'],
            help='If specified, shows retention days for a deleted database, instead of an existing database.'
            'Must match the deleted time of a deleted database on the source Managed Instance.')

    with self.argument_context('sql midb ltr-policy set') as c:
        create_args_for_complex_type(
            c, 'parameters', ManagedDatabase, [
                'weekly_retention',
                'monthly_retention',
                'yearly_retention',
                'week_of_year'
            ])

        c.argument('weekly_retention',
                   help='Retention for the weekly backup. '
                   'If just a number is passed instead of an ISO 8601 string, days will be assumed as the units.'
                   'There is a minimum of 7 days and a maximum of 10 years.')

        c.argument('monthly_retention',
                   help='Retention for the monthly backup. '
                   'If just a number is passed instead of an ISO 8601 string, days will be assumed as the units.'
                   'There is a minimum of 7 days and a maximum of 10 years.')

        c.argument('yearly_retention',
                   help='Retention for the yearly backup. '
                   'If just a number is passed instead of an ISO 8601 string, days will be assumed as the units.'
                   'There is a minimum of 7 days and a maximum of 10 years.')

        c.argument('week_of_year',
                   help='The Week of Year, 1 to 52, in which to take the yearly LTR backup.')

    with self.argument_context('sql midb ltr-backup') as c:
        c.argument('location_name',
                   arg_type=get_location_type(self.cli_ctx),
                   help='The location of the desired backup(s).',
                   id_part=None)

        c.argument('database_name',
                   options_list=['--database', '-d'],
                   id_part=None)

        c.argument('managed_instance_name',
                   options_list=['--managed-instance', '--mi'],
                   id_part=None)

        c.argument('backup_name',
                   options_list=['--name', '-n'],
                   help='The name of the LTR backup. '
                   'Use \'az sql midb ltr-backup show\' or \'az sql midb ltr-backup list\' for backup name.',
                   id_part=None)

        c.argument('backup_id',
                   options_list=['--backup-id', '--id'],
                   help='The resource id of the backups. '
                   'Use \'az sql midb ltr-backup show\' or \'az sql midb ltr-backup list\' for backup id. '
                   'If provided, other arguments are not required. ')

    with self.argument_context('sql midb ltr-backup list') as c:
        c.argument('database_name',
                   options_list=['--database', '-d'],
                   help='The name of the Azure SQL Managed Database. '
                   'If specified (along with instance name), retrieves all requested backups under this database.')

        c.argument('managed_instance_name',
                   options_list=['--managed-instance', '--mi'],
                   help='Name of the Azure SQL managed instance. '
                   'If specified, retrieves all requested backups under this managed instance.')

        c.argument('database_state',
                   required=False,
                   options_list=['--database-state', '--state'],
                   help='\'All\', \'Live\', or \'Deleted\'. '
                   'Will fetch backups only from databases of specified state. '
                   'If no state provied, defaults to \'All\'.')

        c.argument('only_latest_per_database',
                   action='store_true',
                   options_list=['--only-latest-per-database', '--latest'],
                   required=False,
                   help='If true, will only return the latest backup for each database')

    with self.argument_context('sql midb ltr-backup restore') as c:
        c.argument('target_managed_database_name',
                   options_list=['--dest-database'],
                   required=True,
                   help='Name of the managed database that will be created as the restore destination.')

        c.argument('target_managed_instance_name',
                   options_list=['--dest-mi'],
                   required=True,
                   help='Name of the managed instance to restore managed database to.')

        c.argument('target_resource_group_name',
                   options_list=['--dest-resource-group'],
                   required=True,
                   help='Name of the resource group of the managed instance to restore managed database to.')

        c.argument('long_term_retention_backup_resource_id',
                   options_list=['--backup-id', '--id'],
                   required=True,
                   help='The resource id of the long term retention backup to be restored. '
                   'Use \'az sql midb ltr-backup show\' or \'az sql midb ltr-backup list\' for backup id.')

        c.argument('storage_account_type',
                   arg_type=backup_storage_redundancy_param_type_mi)

    with self.argument_context('sql midb log-replay start') as c:
        create_args_for_complex_type(
            c, 'parameters', ManagedDatabase, [
                'auto_complete',
                'last_backup_name',
                'storage_container_uri',
                'storage_container_sas_token'
            ])

        c.argument('auto_complete',
                   required=False,
                   options_list=['--auto-complete', '-a'],
                   action='store_true',
                   help='The flag that in usage with last_backup_name automatically completes log replay servise.')

        c.argument('last_backup_name',
                   required=False,
                   options_list=['--last-backup-name', '--last-bn'],
                   help='The name of the last backup to restore.')

        c.argument('storage_container_uri',
                   required=True,
                   options_list=['--storage-uri', '--su'],
                   help='The URI of the storage container where backups are.')

        c.argument('storage_container_sas_token',
                   required=True,
                   options_list=['--storage-sas', '--ss'],
                   help='The authorization Sas token to access storage container where backups are.')

    with self.argument_context('sql midb log-replay complete') as c:
        create_args_for_complex_type(
            c, 'parameters', ManagedDatabase, [
                'last_backup_name'
            ])

        c.argument('last_backup_name',
                   required=False,
                   options_list=['--last-backup-name', '--last-bn'],
                   help='The name of the last backup to restore.')

    ###############################################
    #                sql virtual cluster          #
    ###############################################
    with self.argument_context('sql virtual-cluster') as c:
        c.argument('virtual_cluster_name',
                   help='The virtual cluster name',
                   options_list=['--name', '-n'],
                   # Allow --ids command line argument. id_part=name is 1st name in uri
                   id_part='name')

        c.argument('resource_group_name', arg_type=resource_group_name_type)

    ###############################################
    #             sql instance failover-group     #
    ###############################################

    with self.argument_context('sql instance-failover-group') as c:
        c.argument('failover_group_name',
                   options_list=['--name', '-n'],
                   help="The name of the Instance Failover Group")

        c.argument('managed_instance',
                   arg_type=managed_instance_param_type,
                   options_list=['--source-mi', '--mi'])

        c.argument('partner_managed_instance',
                   help="The name of the partner managed instance of a Instance Failover Group",
                   options_list=['--partner-mi'])

        c.argument('partner_resource_group',
                   help="The name of the resource group of the partner managed instance")

        c.argument('failover_policy',
                   help="The failover policy of the Instance Failover Group",
                   arg_type=get_enum_type(FailoverPolicyType))

        c.argument('grace_period',
                   arg_type=grace_period_param_type)

        c.argument('allow_data_loss',
                   arg_type=allow_data_loss_param_type)

    ###################################################
    #             sql sensitivity classification      #
    ###################################################
    with self.argument_context('sql db classification') as c:
        c.argument('schema_name',
                   required=True,
                   help='The name of the schema.',
                   options_list=['--schema'])

        c.argument('table_name',
                   required=True,
                   help='The name of the table.',
                   options_list=['--table'])

        c.argument('column_name',
                   required=True,
                   help='The name of the column.',
                   options_list=['--column'])

        c.argument('information_type',
                   required=False,
                   help='The information type.')

        c.argument('label_name',
                   required=False,
                   help='The label name.',
                   options_list=['--label'])

    with self.argument_context('sql db classification recommendation list') as c:
        c.ignore('skip_token')
