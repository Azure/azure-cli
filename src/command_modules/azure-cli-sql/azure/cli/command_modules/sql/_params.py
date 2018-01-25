# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import itertools
from enum import Enum

from knack.arguments import CLIArgumentType, ignore_type

from azure.cli.core.commands import patch_arg_make_required, patch_arg_make_optional
from azure.mgmt.sql.models.database import Database
from azure.mgmt.sql.models.elastic_pool import ElasticPool
from azure.mgmt.sql.models.import_extension_request \
    import ImportExtensionRequest
from azure.mgmt.sql.models.export_request import ExportRequest
from azure.mgmt.sql.models.server import Server
from azure.mgmt.sql.models.server_azure_ad_administrator import ServerAzureADAdministrator
from azure.mgmt.sql.models.sql_management_client_enums import (
    AuthenticationType,
    BlobAuditingPolicyState,
    CreateMode,
    SecurityAlertPolicyState,
    SecurityAlertPolicyEmailAccountAdmins,
    ServerConnectionType,
    ServerKeyType,
    StorageKeyType,
    TransparentDataEncryptionStatus)

from azure.cli.core.commands.parameters import (get_three_state_flag, get_enum_type,
                                                get_resource_name_completion_list,
                                                get_location_type)
from .custom import (
    ClientAuthenticationType,
    ClientType,
    DatabaseCapabilitiesAdditionalDetails,
    ElasticPoolCapabilitiesAdditionalDetails
)

#####
#           Reusable param type definitions
#####


server_param_type = CLIArgumentType(
    options_list=['--server', '-s'],
    help='Name of the Azure SQL server.')

#####
#        SizeWithUnitConverter - consider moving to common code (azure.cli.core.commands.parameters)
#####


class SizeWithUnitConverter(object):  # pylint: disable=too-few-public-methods

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
            return self.result_type(uvals) * self.result_type(numeric_part)
        except KeyError:
            raise ValueError()

    def __repr__(self):
        return 'Size (in {}) - valid units are {}.'.format(
            self.unit,
            ', '.join(sorted(self.unit_map, key=self.unit_map.__getitem__)))


###############################################
#                sql db                       #
###############################################


class Engine(Enum):  # pylint: disable=too-few-public-methods
    """SQL RDBMS engine type."""
    db = 'db'
    dw = 'dw'


def _configure_db_create_params(
        arg_ctx,
        engine,
        create_mode):
    """
    Configures params for db/dw create/update commands.

    The PUT database REST API has many parameters and many modes (`create_mode`) that control
    which parameters are valid. To make it easier for CLI users to get the param combinations
    correct, these create modes are separated into different commands (e.g.: create, copy,
    restore, etc).

    On top of that, some create modes and some params are not allowed if the database edition is
    DataWarehouse. For this reason, regular database commands are separated from datawarehouse
    commands (`db` vs `dw`.)

    As a result, the param combination matrix is a little complicated. This function configures
    which params are ignored for a PUT database command based on a command's SQL engine type and
    create mode.

    engine: Engine enum value (e.g. `db`, `dw`)
    create_mode: Valid CreateMode enum value (e.g. `default`, `copy`, etc)
    """

    # This line to be removed when zone redundancy is fully supported in production.
    arg_ctx.ignore('zone_redundant')

    # DW does not support all create modes. Check that engine and create_mode are consistent.
    if engine == Engine.dw and create_mode not in [
            CreateMode.default,
            CreateMode.point_in_time_restore,
            CreateMode.restore]:
        raise ValueError('Engine {} does not support create mode {}'.format(engine, create_mode))

    # Include all Database params as a starting point. We will filter from there.
    arg_ctx.expand('parameters', Database)

    # The following params are always ignored because their values are filled in by wrapper
    # functions.
    arg_ctx.ignore('location', 'create_mode', 'source_database_id')

    # Read scale is only applicable to sql db (not dw). However it is a preview feature and will
    # be not exposed for now.
    arg_ctx.ignore('read_scale')

    # Service objective id is not user-friendly and won't be exposed.
    # Better to use service objective name instead.
    arg_ctx.ignore('requested_service_objective_id')

    # Only applicable to default create mode. Also only applicable to db.
    if create_mode != CreateMode.default or engine != Engine.db:
        arg_ctx.ignore('sample_name', 'zone_redundant')

    # Only applicable to point in time restore or deleted restore create mode.
    if create_mode not in [CreateMode.restore, CreateMode.point_in_time_restore]:
        arg_ctx.ignore('restore_point_in_time', 'source_database_deletion_date')

    # 'collation', 'edition', and 'max_size_bytes' are ignored (or rejected) when creating a copy
    # or secondary because their values are determined by the source db.
    if create_mode in [CreateMode.copy, CreateMode.non_readable_secondary,
                       CreateMode.online_secondary]:
        arg_ctx.ignore('collation', 'edition', 'max_size_bytes')

    # collation and max_size_bytes are ignored when restoring because their values are determined by
    # the source db.
    if create_mode in [CreateMode.restore, CreateMode.point_in_time_restore]:
        arg_ctx.ignore('collation', 'max_size_bytes')

    if engine == Engine.dw:
        # Elastic pool is only for SQL DB.
        arg_ctx.ignore('elastic_pool_name')

        # Edition is always 'DataWarehouse'
        arg_ctx.ignore('edition')

    # recovery_services_recovery_point_resource_id is only for long-term-retention restore
    if create_mode != CreateMode.restore_long_term_retention_backup:
        arg_ctx.ignore('recovery_services_recovery_point_resource_id')


# pylint: disable=too-many-statements
def load_arguments(self, _):

    with self.argument_context('sql') as c:
        c.argument('location_name', arg_type=get_location_type(self.cli_ctx))
        c.argument('usage_name', options_list=['--usage', '-u'])

    with self.argument_context('sql db') as c:
        c.argument('database_name',
                   options_list=['--name', '-n'],
                   help='Name of the Azure SQL Database.')
        c.argument('server_name', arg_type=server_param_type)
        c.argument('elastic_pool_name', options_list=['--elastic-pool'])
        c.argument('requested_service_objective_name', options_list=['--service-objective'])
        c.argument('max_size_bytes', options_list=['--max-size'],
                   type=SizeWithUnitConverter('B', result_type=int),
                   help='The max storage size of the database. Only the following'
                   ' sizes are supported (in addition to limitations being placed on'
                   ' each edition): 100MB, 500MB, 1GB, 5GB, 10GB, 20GB,'
                   ' 30GB, 150GB, 200GB, 500GB. If no unit is specified, defaults to bytes (B).')

        # Adjust help text.
        c.argument('edition',
                   options_list=['--edition'],
                   help='The edition of the database.')

    with self.argument_context('sql db create') as c:
        _configure_db_create_params(c, Engine.db, CreateMode.default)

    with self.argument_context('sql db copy') as c:
        _configure_db_create_params(c, Engine.db, CreateMode.copy)

        c.argument('elastic_pool_name',
                   help='Name of the elastic pool to create the new database in.')

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

        c.argument('requested_service_objective_name',
                   options_list=['--service-objective'],
                   help='Name of the service objective for the new database.')

    with self.argument_context('sql db restore') as c:
        _configure_db_create_params(c, Engine.db, CreateMode.point_in_time_restore)

        c.argument('dest_name',
                   help='Name of the database that will be created as the restore destination.')

        restore_point_arg_group = 'Restore Point'

        c.argument('restore_point_in_time',
                   options_list=['--time', '-t'],
                   arg_group=restore_point_arg_group,
                   help='The point in time of the source database that will be restored to create the'
                   ' new database. Must be greater than or equal to the source database\'s'
                   ' earliestRestoreDate value. Either --time or --deleted-time (or both) must be specified.')

        c.argument('source_database_deletion_date',
                   options_list=['--deleted-time'],
                   arg_group=restore_point_arg_group,
                   help='If specified, restore from a deleted database instead of from an existing database.'
                   ' Must match the deleted time of a deleted database in the same server.'
                   ' Either --time or --deleted-time (or both) must be specified.')

        c.argument('edition',
                   help='The edition for the new database.')
        c.argument('elastic_pool_name',
                   help='Name of the elastic pool to create the new database in.')
        c.argument('requested_service_objective_name',
                   help='Name of service objective for the new database.')

    with self.argument_context('sql db show') as c:
        # Service tier advisors and transparent data encryption are not included in the first batch
        # of GA commands.
        c.ignore('expand')

    with self.argument_context('sql db list') as c:
        c.argument('elastic_pool_name',
                   help='If specified, lists only the databases in this elastic pool')

    with self.argument_context('sql db list-editions') as c:
        c.argument('show_details',
                   options_list=['--show-details', '-d'],
                   help='List of additional details to include in output.',
                   nargs='+',
                   arg_type=get_enum_type(DatabaseCapabilitiesAdditionalDetails))

        search_arg_group = 'Search'

        # We could used get_enum_type here, but that will validate the inputs which means there
        # will be no way to query for new editions/service objectives that are made available after
        # this version of CLI is released.
        c.argument('edition',
                   arg_group=search_arg_group,
                   help='Edition to search for. If unspecified, all editions are shown.')
        c.argument('service_objective',
                   arg_group=search_arg_group,
                   help='Service objective to search for. If unspecified, all editions are shown.')

    with self.argument_context('sql db update') as c:
        c.argument('requested_service_objective_name',
                   help='The name of the new service objective. If this is a standalone db service'
                   ' objective and the db is currently in an elastic pool, then the db is removed from'
                   ' the pool.')
        c.argument('elastic_pool_name', help='The name of the elastic pool to move the database into.')
        c.argument('max_size_bytes', help='The new maximum size of the database expressed in bytes.')

    with self.argument_context('sql db export') as c:
        c.expand('parameters', ExportRequest)
        c.argument('administrator_login', options_list=['--admin-user', '-u'])
        c.argument('administrator_login_password', options_list=['--admin-password', '-p'])
        c.argument('authentication_type', options_list=['--auth-type', '-a'],
                   arg_type=get_enum_type(AuthenticationType))
        c.argument('storage_key_type', arg_type=get_enum_type(StorageKeyType))

    with self.argument_context('sql db import') as c:
        c.expand('parameters', ImportExtensionRequest)
        c.argument('administrator_login', options_list=['--admin-user', '-u'])
        c.argument('administrator_login_password', options_list=['--admin-password', '-p'])
        c.argument('authentication_type', options_list=['--auth-type', '-a'],
                   arg_type=get_enum_type(AuthenticationType))
        c.argument('storage_key_type', arg_type=get_enum_type(StorageKeyType))

        c.ignore('type')

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
    #           sql db replica
    #####
    with self.argument_context('sql db replica create') as c:
        _configure_db_create_params(c, Engine.db, CreateMode.online_secondary)

        c.argument('elastic_pool_name',
                   options_list=['--elastic-pool'],
                   help='Name of elastic pool to create the new replica in.')

        c.argument('requested_service_objective_name',
                   options_list=['--service-objective'],
                   help='Name of service objective for the new replica.')

        c.argument('partner_resource_group_name',
                   options_list=['--partner-resource-group'],
                   help='Name of the resource group to create the new replica in.'
                   ' If unspecified, defaults to the origin resource group.')

        c.argument('partner_server_name',
                   options_list=['--partner-server'],
                   help='Name of the server to create the new replica in.')

    with self.argument_context('sql db replica set-primary') as c:
        c.argument('database_name', help='Name of the database to fail over.')
        c.argument('server_name',
                   help='Name of the server containing the secondary replica that will become'
                   ' the new primary.')
        c.argument('resource_group_name',
                   help='Name of the resource group containing the secondary replica that'
                   ' will become the new primary.')
        c.argument('allow_data_loss',
                   help='If specified, the failover operation will allow data loss.')

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
        storage_arg_group = 'Storage'

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
                   help='Whether the alert is sent to the account administrators.',
                   arg_type=get_enum_type(SecurityAlertPolicyEmailAccountAdmins))

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

    ###############################################
    #                sql dw                       #
    ###############################################
    with self.argument_context('sql dw') as c:
        c.argument('database_name', options_list=['--name', '-n'],
                   help='Name of the data warehouse.')

        c.argument('server_name', arg_type=server_param_type)

        c.argument('max_size_bytes', options_list=['--max-size'],
                   type=SizeWithUnitConverter('B', result_type=int),
                   help='The max storage size of the data warehouse. If no unit is specified, defaults'
                   'to bytes (B).')

        c.argument('requested_service_objective_name',
                   options_list=['--service-objective'],
                   help='The service objective of the data warehouse.')

        c.argument('collation',
                   options_list=['--collation'],
                   help='The collation of the data warehouse.')

    with self.argument_context('sql dw create') as c:
        _configure_db_create_params(c, Engine.dw, CreateMode.default)

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
        # This line to be removed when zone redundancy is fully supported in production.
        c.ignore('zone_redundant')

        c.argument('elastic_pool_name',
                   options_list=['--name', '-n'],
                   help='The name of the elastic pool.')
        c.argument('server_name', arg_type=server_param_type)

        # --db-dtu-max and --db-dtu-min were the original param names, which is consistent with the
        # underlying REST API.
        # --db-max-dtu and --db-min-dtu are aliases which are consistent with the `sql elastic-pool
        # list-editions --show-details db-max-dtu db-min-dtu` parameter values. These are more
        # consistent with other az sql commands, but the original can't be removed due to
        # compatibility.
        c.argument('database_dtu_max', options_list=['--db-dtu-max', '--db-max-dtu'])
        c.argument('database_dtu_min', options_list=['--db-dtu-min', '--db-min-dtu'])

        # --storage was the original param name, which is consistent with the underlying REST API.
        # --max-size is an alias which is consistent with the `sql elastic-pool list-editions
        # --show-details max-size` parameter value and also matches `sql db --max-size` parameter name.
        c.argument('storage_mb', options_list=['--storage', '--max-size'],
                   type=SizeWithUnitConverter('MB', result_type=int),
                   help='The max storage size of the elastic pool. If no unit is specified, defaults'
                   ' to megabytes (MB).')

    with self.argument_context('sql elastic-pool create') as c:
        c.expand('parameters', ElasticPool)
        # We have a wrapper function that determines server location so user doesn't need to specify
        # it as param.
        c.ignore('location')

    with self.argument_context('sql elastic-pool list-editions') as c:
        # Note that `ElasticPoolCapabilitiesAdditionalDetails` intentionally match param names to
        # other commands, such as `sql elastic-pool create --db-max-dtu --db-min-dtu --max-size`.
        c.argument('show_details',
                   options_list=['--show-details', '-d'],
                   help='List of additional details to include in output.',
                   nargs='+',
                   arg_type=get_enum_type(ElasticPoolCapabilitiesAdditionalDetails))

        search_arg_group = 'Search'

        # We could used 'arg_type=get_enum_type' here, but that will validate the inputs which means there
        # will be no way to query for new editions that are made available after
        # this version of CLI is released.
        c.argument('edition',
                   arg_group=search_arg_group,
                   help='Edition to search for. If unspecified, all editions are shown.')
        c.argument('dtu',
                   arg_group=search_arg_group,
                   help='Elastic pool DTU limit to search for. If unspecified, all DTU limits are shown.')

    with self.argument_context('sql elastic-pool update') as c:
        c.argument('database_dtu_max', help='The maximum DTU any one database can consume.')
        c.argument('database_dtu_min', help='The minimum DTU all databases are guaranteed.')
        c.argument('dtu', help='TThe total shared DTU for the elastic eool.')
        c.argument('storage_mb', help='Storage limit for the elastic pool in MB.')

    ###############################################
    #                sql server                   #
    ###############################################
    with self.argument_context('sql server') as c:
        c.argument('server_name', options_list=['--name', '-n'])
        c.argument('administrator_login', options_list=['--admin-user', '-u'])
        c.argument('administrator_login_password', options_list=['--admin-password', '-p'])

    with self.argument_context('sql server create') as c:
        # Both administrator_login and administrator_login_password are required for server creation.
        # However these two parameters are given default value in the create_or_update function
        # signature, therefore, they can't be automatically converted to requirement arguments.
        c.expand('parameters', Server, patches={
            'administrator_login': patch_arg_make_required,
            'administrator_login_password': patch_arg_make_required
        })

        c.argument('assign_identity',
                   options_list=['--assign-identity', '-i'],
                   help='Generate and assign an Azure Active Directory Identity for this server'
                   'for use with key management services like Azure KeyVault.')

        # 12.0 is the only server version allowed and it's already the default.
        c.ignore('version')

        # Identity will be handled with its own parameter.
        c.ignore('identity')

    with self.argument_context('sql server update') as c:
        c.argument('administrator_login_password', help='The administrator login password.')
        c.argument('assign_identity',
                   options_list=['--assign_identity', '-i'],
                   help='Generate and assign an Azure Active Directory Identity for this server'
                   'for use with key management services like Azure KeyVault.')

    #####
    #           sql server ad-admin
    ######
    with self.argument_context('sql server ad-admin') as c:
        c.argument('server_name', options_list=['--server-name', '-s'],
                   help='The name of the SQL Server')
        c.argument('login', options_list=['--display-name', '-u'],
                   help='Display name of the Azure AD administrator user or group.')
        c.argument('sid', options_list=['--object-id', '-i'],
                   help='The unique ID of the Azure AD administrator ')
        c.ignore('tenant_id')

    with self.argument_context('sql server ad-admin create') as c:
        c.expand('properties', ServerAzureADAdministrator, patches={
            'tenant_id': patch_arg_make_optional})

    #####
    #           sql server conn-policy
    #####
    with self.argument_context('sql server conn-policy') as c:
        c.argument('server_name', arg_type=server_param_type)
        c.argument('connection_type', options_list=['--connection-type', '-t'],
                   arg_type=get_enum_type(ServerConnectionType))

    #####
    #           sql server firewall-rule
    #####
    with self.argument_context('sql server firewall-rule') as c:
        # Help text needs to be specified because 'sql server firewall-rule update' is a custom
        # command.
        c.argument('server_name', arg_type=server_param_type)

        c.argument('firewall_rule_name',
                   options_list=['--name', '-n'],
                   help='The name of the firewall rule.')

        c.argument('start_ip_address',
                   options_list=['--start-ip-address'],
                   help='The start IP address of the firewall rule. Must be IPv4 format. Use value'
                   ' \'0.0.0.0\' to represent all Azure-internal IP addresses.')

        c.argument('end_ip_address',
                   options_list=['--end-ip-address'],
                   help='The end IP address of the firewall rule. Must be IPv4 format. Use value'
                   ' \'0.0.0.0\' to represent all Azure-internal IP addresses.')

    #####
    #           sql server key
    #####
    with self.argument_context('sql server key') as c:
        c.argument('server_name', arg_type=server_param_type)
        c.argument('key_name', options_list=['--name', '-n'])
        c.argument('kid',
                   options_list=['--kid', '-k'],
                   required=True,
                   help='The Azure Key Vault key identifier of the server key. An example key identifier is '
                   '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

    #####
    #           sql server tde-key
    #####
    with self.argument_context('sql server tde-key') as c:
        c.argument('server_name', arg_type=server_param_type)

    with self.argument_context('sql server tde-key set') as c:
        c.argument('kid',
                   options_list=['--kid', '-k'],
                   help='The Azure Key Vault key identifier of the server key to be made encryption protector.'
                   'An example key identifier is '
                   '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')
        c.argument('server_key_type',
                   options_list=['--server-key-type', '-t'],
                   help='The type of the server key',
                   arg_type=get_enum_type(ServerKeyType))

    #####
    #           sql server vnet-rule
    #####
    with self.argument_context('sql server vnet-rule') as c:
        # Help text needs to be specified because 'sql server vnet-rule create' is a custom
        # command.
        c.argument('server_name',
                   options_list=['--server', '-s'],
                   completer=get_resource_name_completion_list('Microsoft.SQL/servers'))

        c.argument('virtual_network_rule_name',
                   options_list=['--name', '-n'])

        c.argument('virtual_network_subnet_id',
                   options_list=['--subnet'],
                   help='Name or ID of the subnet that allows access to an Azure Sql Server. '
                   'If subnet name is provided, --vnet-name must be provided.')

        c.argument('ignore_missing_vnet_service_endpoint',
                   options_list=['--ignore-missing-endpoint', '-i'],
                   help='Create firewall rule before the virtual network has vnet service endpoint enabled',
                   arg_type=get_three_state_flag())

    with self.argument_context('sql server vnet-rule create') as c:
        c.extra('vnet_name', options_list=['--vnet-name'], help='The virtual network name')
