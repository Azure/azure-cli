# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=C0302
from enum import Enum
import re

# url parse package has different names in Python 2 and 3. 'six' package works cross-version.
from six.moves.urllib.parse import (quote, urlparse)  # pylint: disable=import-error

from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import (
    get_mgmt_service_client,
    get_subscription_id)
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt.sql.models.server_key import ServerKey
from azure.mgmt.sql.models.encryption_protector import EncryptionProtector
from azure.mgmt.sql.models.resource_identity import ResourceIdentity
from azure.mgmt.sql.models.sql_management_client_enums import (
    BlobAuditingPolicyState,
    CreateMode,
    DatabaseEdition,
    IdentityType,
    ReplicationRole,
    SecurityAlertPolicyState,
    ServerKeyType,
    ServiceObjectiveName,
    StorageKeyType
)
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient

from ._util import (
    get_sql_servers_operations
)

###############################################
#                Common funcs                 #
###############################################


# Determines server location
def _get_server_location(cli_ctx, server_name, resource_group_name):
    server_client = get_sql_servers_operations(cli_ctx, None)
    # pylint: disable=no-member
    return server_client.get(
        server_name=server_name,
        resource_group_name=resource_group_name).location


_DEFAULT_SERVER_VERSION = "12.0"

###############################################
#                sql db                       #
###############################################


# pylint: disable=too-few-public-methods
class ClientType(Enum):
    ado_net = 'ado.net'
    sqlcmd = 'sqlcmd'
    jdbc = 'jdbc'
    php_pdo = 'php_pdo'
    php = 'php'
    odbc = 'odbc'


class ClientAuthenticationType(Enum):
    sql_password = 'SqlPassword'
    active_directory_password = 'ADPassword'
    active_directory_integrated = 'ADIntegrated'


def _get_server_dns_suffx(cli_ctx):
    # Allow dns suffix to be overridden by environment variable for testing purposes
    from os import getenv
    return getenv('_AZURE_CLI_SQL_DNS_SUFFIX', default=cli_ctx.cloud.suffixes.sql_server_hostname)


def db_show_conn_str(
        cmd,
        client_provider,
        database_name='<databasename>',
        server_name='<servername>',
        auth_type=ClientAuthenticationType.sql_password.value):

    server_suffix = _get_server_dns_suffx(cmd.cli_ctx)

    conn_str_props = {
        'server': server_name,
        'server_fqdn': '{}{}'.format(server_name, server_suffix),
        'server_suffix': server_suffix,
        'db': database_name
    }

    formats = {
        ClientType.ado_net.value: {
            ClientAuthenticationType.sql_password.value:
                'Server=tcp:{server_fqdn},1433;Database={db};User ID=<username>;'
                'Password=<password>;Encrypt=true;Connection Timeout=30;',
            ClientAuthenticationType.active_directory_password.value:
                'Server=tcp:{server_fqdn},1433;Database={db};User ID=<username>;'
                'Password=<password>;Encrypt=true;Connection Timeout=30;'
                'Authentication="Active Directory Password"',
            ClientAuthenticationType.active_directory_integrated.value:
                'Server=tcp:{server_fqdn},1433;Database={db};Encrypt=true;'
                'Connection Timeout=30;Authentication="Active Directory Integrated"'
        },
        ClientType.sqlcmd.value: {
            ClientAuthenticationType.sql_password.value:
                'sqlcmd -S tcp:{server_fqdn},1433 -d {db} -U <username> -P <password> -N -l 30',
            ClientAuthenticationType.active_directory_password.value:
                'sqlcmd -S tcp:{server_fqdn},1433 -d {db} -U <username> -P <password> -G -N -l 30',
            ClientAuthenticationType.active_directory_integrated.value:
                'sqlcmd -S tcp:{server_fqdn},1433 -d {db} -G -N -l 30',
        },
        ClientType.jdbc.value: {
            ClientAuthenticationType.sql_password.value:
                'jdbc:sqlserver://{server_fqdn}:1433;database={db};user=<username>@{server};'
                'password=<password>;encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{server_suffix};loginTimeout=30',
            ClientAuthenticationType.active_directory_password.value:
                'jdbc:sqlserver://{server_fqdn}:1433;database={db};user=<username>;'
                'password=<password>;encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{server_suffix};loginTimeout=30;'
                'authentication=ActiveDirectoryPassword',
            ClientAuthenticationType.active_directory_integrated.value:
                'jdbc:sqlserver://{server_fqdn}:1433;database={db};'
                'encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{server_suffix};loginTimeout=30;'
                'authentication=ActiveDirectoryIntegrated',
        },
        ClientType.php_pdo.value: {
            # pylint: disable=line-too-long
            ClientAuthenticationType.sql_password.value:
                '$conn = new PDO("sqlsrv:server = tcp:{server_fqdn},1433; Database = {db}; LoginTimeout = 30; Encrypt = 1; TrustServerCertificate = 0;", "<username>", "<password>");',
            ClientAuthenticationType.active_directory_password.value:
                CLIError('PHP Data Object (PDO) driver only supports SQL Password authentication.'),
            ClientAuthenticationType.active_directory_integrated.value:
                CLIError('PHP Data Object (PDO) driver only supports SQL Password authentication.'),
        },
        ClientType.php.value: {
            # pylint: disable=line-too-long
            ClientAuthenticationType.sql_password.value:
                '$connectionOptions = array("UID"=>"<username>@{server}", "PWD"=>"<password>", "Database"=>{db}, "LoginTimeout" => 30, "Encrypt" => 1, "TrustServerCertificate" => 0); $serverName = "tcp:{server_fqdn},1433"; $conn = sqlsrv_connect($serverName, $connectionOptions);',
            ClientAuthenticationType.active_directory_password.value:
                CLIError('PHP sqlsrv driver only supports SQL Password authentication.'),
            ClientAuthenticationType.active_directory_integrated.value:
                CLIError('PHP sqlsrv driver only supports SQL Password authentication.'),
        },
        ClientType.odbc.value: {
            ClientAuthenticationType.sql_password.value:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{server_fqdn},1433;'
                'Database={db};Uid=<username>@{server};Pwd=<password>;Encrypt=yes;'
                'TrustServerCertificate=no;',
            ClientAuthenticationType.active_directory_password.value:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{server_fqdn},1433;'
                'Database={db};Uid=<username>@{server};Pwd=<password>;Encrypt=yes;'
                'TrustServerCertificate=no;Authentication=ActiveDirectoryPassword',
            ClientAuthenticationType.active_directory_integrated.value:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{server_fqdn},1433;'
                'Database={db};Encrypt=yes;TrustServerCertificate=no;'
                'Authentication=ActiveDirectoryIntegrated',
        }
    }

    f = formats[client_provider][auth_type]

    if isinstance(f, Exception):
        # Error
        raise f

    # Success
    return f.format(**conn_str_props)


# Helper class to bundle up database identity properties
class DatabaseIdentity(object):  # pylint: disable=too-few-public-methods
    def __init__(self, cli_ctx, database_name, server_name, resource_group_name):
        self.database_name = database_name
        self.server_name = server_name
        self.resource_group_name = resource_group_name
        self.cli_ctx = cli_ctx

    def id(self):
        return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/databases/{}'.format(
            quote(get_subscription_id(self.cli_ctx)),
            quote(self.resource_group_name),
            quote(self.server_name),
            quote(self.database_name))


# Creates a database or datawarehouse. Wrapper function which uses the server location so that
# the user doesn't need to specify location.
def _db_dw_create(
        cli_ctx,
        client,
        db_id,
        no_wait,
        kwargs):

    # Determine server location
    kwargs['location'] = _get_server_location(
        cli_ctx,
        server_name=db_id.server_name,
        resource_group_name=db_id.resource_group_name)

    # Create
    return sdk_no_wait(no_wait, client.create_or_update,
                       server_name=db_id.server_name,
                       resource_group_name=db_id.resource_group_name,
                       database_name=db_id.database_name,
                       parameters=kwargs)


# Creates a database. Wrapper function which uses the server location so that the user doesn't
# need to specify location.
def db_create(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        no_wait=False,
        **kwargs):

    # Verify edition
    edition = kwargs.get('edition')  # kwags['edition'] throws KeyError if not in dictionary
    if edition and edition.lower() == DatabaseEdition.data_warehouse.value.lower():  # pylint: disable=no-member
        raise CLIError('Azure SQL Data Warehouse can be created with the command'
                       ' `az sql dw create`.')

    return _db_dw_create(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        no_wait,
        kwargs)


# Common code for special db create modes.
def _db_create_special(
        cli_ctx,
        client,
        source_db,
        dest_db,
        no_wait,
        kwargs):

    # Determine server location
    kwargs['location'] = _get_server_location(
        cli_ctx,
        server_name=dest_db.server_name,
        resource_group_name=dest_db.resource_group_name)

    # Set create mode properties
    kwargs['source_database_id'] = source_db.id()

    # Create
    return sdk_no_wait(no_wait, client.create_or_update,
                       server_name=dest_db.server_name,
                       resource_group_name=dest_db.resource_group_name,
                       database_name=dest_db.database_name,
                       parameters=kwargs)


# Copies a database. Wrapper function to make create mode more convenient.
def db_copy(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        dest_name,
        dest_server_name=None,
        dest_resource_group_name=None,
        no_wait=False,
        **kwargs):

    # Determine optional values
    dest_server_name = dest_server_name or server_name
    dest_resource_group_name = dest_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = 'Copy'

    return _db_create_special(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        DatabaseIdentity(cmd.cli_ctx, dest_name, dest_server_name, dest_resource_group_name),
        no_wait,
        kwargs)


# Copies a replica. Wrapper function to make create mode more convenient.
def db_create_replica(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        # Replica must have the same database name as the source db
        partner_server_name,
        partner_resource_group_name=None,
        no_wait=False,
        **kwargs):

    # Determine optional values
    partner_resource_group_name = partner_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = CreateMode.online_secondary.value

    # Replica must have the same database name as the source db
    return _db_create_special(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        DatabaseIdentity(cmd.cli_ctx, database_name, partner_server_name, partner_resource_group_name),
        no_wait,
        kwargs)


# Renames a database.
def db_rename(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        new_name):

    client.rename(
        resource_group_name,
        server_name,
        database_name,
        id=DatabaseIdentity(
            cmd.cli_ctx,
            new_name,
            server_name,
            resource_group_name
        ).id())

    return client.get(
        resource_group_name,
        server_name,
        new_name)


# Creates a database from a database point in time backup or deleted database backup.
# Wrapper function to make create mode more convenient.
def db_restore(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        dest_name,
        restore_point_in_time=None,
        source_database_deletion_date=None,
        no_wait=False,
        **kwargs):

    if not (restore_point_in_time or source_database_deletion_date):
        raise CLIError('Either --time or --deleted-time must be specified.')

    # Set create mode properties
    is_deleted = source_database_deletion_date is not None

    kwargs['restore_point_in_time'] = restore_point_in_time
    kwargs['source_database_deletion_date'] = source_database_deletion_date
    kwargs['create_mode'] = 'Restore' if is_deleted else 'PointInTimeRestore'

    return _db_create_special(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        # Cross-server restore is not supported. So dest server/group must be the same as source.
        DatabaseIdentity(cmd.cli_ctx, dest_name, server_name, resource_group_name),
        no_wait,
        kwargs)


# Fails over a database. Wrapper function which uses the server location so that the user doesn't
# need to specify replication link id.
# pylint: disable=inconsistent-return-statements
def db_failover(
        client,
        database_name,
        server_name,
        resource_group_name,
        allow_data_loss=False):

    # List replication links
    links = list(client.list_by_database(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name))

    if not links:
        raise CLIError('The specified database has no replication links.')

    # If a replica is primary, then it has 1 or more links (to its secondaries).
    # If a replica is secondary, then it has exactly 1 link (to its primary).
    primary_link = next((l for l in links if l.partner_role == ReplicationRole.primary), None)
    if not primary_link:
        # No link to a primary, so this must already be a primary. Do nothing.
        return

    # Choose which failover method to use
    if allow_data_loss:
        failover_func = client.failover_allow_data_loss
    else:
        failover_func = client.failover

    # Execute failover from the primary to this database
    return failover_func(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        link_id=primary_link.name)


class DatabaseCapabilitiesAdditionalDetails(Enum):  # pylint: disable=too-few-public-methods
    max_size = 'max-size'


def db_list_capabilities(
        client,
        location,
        edition=None,
        service_objective=None,
        show_details=None):

    # Fixup parameters
    if not show_details:
        show_details = []

    # Get capabilities tree from server
    capabilities = client.list_by_location(location)

    # Get subtree related to databases
    editions = next(sv for sv in capabilities.supported_server_versions
                    if sv.name == _DEFAULT_SERVER_VERSION).supported_editions

    # Filter by edition
    if edition:
        editions = [e for e in editions if e.name.lower() == edition.lower()]

    # Filter by service objective
    if service_objective:
        for e in editions:
            e.supported_service_level_objectives = [
                slo for slo in e.supported_service_level_objectives
                if slo.name.lower() == service_objective.lower()]

    # Remove editions with no service objectives (due to filters)
    editions = [e for e in editions if e.supported_service_level_objectives]

    # Optionally hide supported max sizes
    if DatabaseCapabilitiesAdditionalDetails.max_size.value not in show_details:
        for e in editions:
            for slo in e.supported_service_level_objectives:
                slo.supported_max_sizes = []

    return editions


# pylint: disable=inconsistent-return-statements
def db_delete_replica_link(
        client,
        database_name,
        server_name,
        resource_group_name,
        # Partner dbs must have the same name as one another
        partner_server_name,
        partner_resource_group_name=None,
        # Base command code handles confirmation, but it passes '--yes' parameter to us if
        # provided. We don't care about this parameter and it gets handled weirdly if we
        # expliclty specify it with default value here (e.g. `yes=None` or `yes=True`), receiving
        # it in kwargs seems to work.
        **kwargs):  # pylint: disable=unused-argument

    # Determine optional values
    partner_resource_group_name = partner_resource_group_name or resource_group_name

    # Find the replication link
    links = list(client.list_by_database(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name))

    # The link doesn't tell us the partner resource group name, so we just have to count on
    # partner server name being unique
    link = next((l for l in links if l.partner_server == partner_server_name), None)
    if not link:
        # No link exists, nothing to be done
        return

    return client.delete(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        link_id=link.name)


def db_export(
        client,
        database_name,
        server_name,
        resource_group_name,
        storage_key_type,
        storage_key,
        **kwargs):
    storage_key = pad_sas_key(storage_key_type, storage_key)

    kwargs['storage_key_type'] = storage_key_type
    kwargs['storage_key'] = storage_key

    return client.export(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        storage_key_type=storage_key_type,
        storage_key=storage_key,
        parameters=kwargs)


def db_import(
        client,
        database_name,
        server_name,
        resource_group_name,
        storage_key_type,
        storage_key,
        **kwargs):
    storage_key = pad_sas_key(storage_key_type, storage_key)

    kwargs['storage_key_type'] = storage_key_type
    kwargs['storage_key'] = storage_key

    return client.create_import_operation(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        storage_key_type=storage_key_type,
        storage_key=storage_key,
        parameters=kwargs)


def pad_sas_key(
        storage_key_type,
        storage_key):
    # Import/Export API requires that "?" precede SAS key as an argument.
    # Add ? prefix if it wasn't included.
    if storage_key_type.lower() == StorageKeyType.shared_access_key.value.lower():  # pylint: disable=no-member
        if storage_key[0] != '?':
            storage_key = '?' + storage_key
    return storage_key


# Lists databases in a server or elastic pool.
def db_list(
        client,
        server_name,
        resource_group_name,
        elastic_pool_name=None):

    if elastic_pool_name:
        # List all databases in the elastic pool
        return client.list_by_elastic_pool(
            server_name=server_name,
            resource_group_name=resource_group_name,
            elastic_pool_name=elastic_pool_name,
            filter=filter)

        # List all databases in the server
    return client.list_by_server(resource_group_name=resource_group_name, server_name=server_name)


# Update database. Custom update function to apply parameters to instance.
def db_update(
        instance,
        elastic_pool_name=None,
        max_size_bytes=None,
        requested_service_objective_name=None,
        zone_redundant=None):

    # Verify edition
    if instance.edition.lower() == DatabaseEdition.data_warehouse.value.lower():  # pylint: disable=no-member
        raise CLIError('Azure SQL Data Warehouse can be updated with the command'
                       ' `az sql dw update`.')

    # Null out edition. The service will choose correct edition based on service objective and
    # elastic pool.
    instance.edition = None

    # Verify that elastic_pool_name and requested_service_objective_name param values are not
    # totally inconsistent. If elastic pool and service objective name are both specified, and
    # they are inconsistent (i.e. service objective is not 'ElasticPool'), then the service
    # actually ignores the value of service objective name (!!). We are trying to protect the CLI
    # user from this unintuitive behavior.
    if (elastic_pool_name and
            requested_service_objective_name and
            requested_service_objective_name != ServiceObjectiveName.elastic_pool.value):
        raise CLIError('If elastic pool is specified, service objective must be'
                       ' unspecified or equal \'{}\'.'.format(
                           ServiceObjectiveName.elastic_pool.value))

    # Update instance pool and service objective. The service treats these properties like PATCH,
    # so if either of these properties is null then the service will keep the property unchanged -
    # except if pool is null/empty and service objective is a standalone SLO value (e.g. 'S0',
    # 'S1', etc), in which case the pool being null/empty is meaningful - it means remove from
    # pool.
    instance.elastic_pool_name = elastic_pool_name
    instance.requested_service_objective_name = requested_service_objective_name

    # Null out requested_service_objective_id, because if requested_service_objective_id is
    # specified then requested_service_objective_name is ignored.
    instance.requested_service_objective_id = None

    # Null out edition so that edition gets chosen automatically by choice of SLO/pool
    instance.edition = None

    # Set other properties
    instance.max_size_bytes = max_size_bytes or instance.max_size_bytes

    instance.zone_redundant = zone_redundant

    return instance


#####
#           sql db audit-policy & threat-policy
#####


# Finds a storage account's resource group by querying ARM resource cache.
# Why do we have to do this: so we know the resource group in order to later query the storage API
# to determine the account's keys and endpoint. Why isn't this just a command line parameter:
# because if it was a command line parameter then the customer would need to specify storage
# resource group just to update some unrelated property, which is annoying and makes no sense to
# the customer.
def _find_storage_account_resource_group(cli_ctx, name):
    storage_type = 'Microsoft.Storage/storageAccounts'
    classic_storage_type = 'Microsoft.ClassicStorage/storageAccounts'

    query = "name eq '{}' and (resourceType eq '{}' or resourceType eq '{}')".format(
        name, storage_type, classic_storage_type)

    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    resources = list(client.resources.list(filter=query))

    if not resources:
        raise CLIError("No storage account with name '{}' was found.".format(name))

    if len(resources) > 1:
        raise CLIError("Multiple storage accounts with name '{}' were found.".format(name))

    if resources[0].type == classic_storage_type:
        raise CLIError("The storage account with name '{}' is a classic storage account which is"
                       " not supported by this command. Use a non-classic storage account or"
                       " specify storage endpoint and key instead.".format(name))

    # Split the uri and return just the resource group
    return resources[0].id.split('/')[4]


# Determines storage account name from endpoint url string.
# e.g. 'https://mystorage.blob.core.windows.net' -> 'mystorage'
def _get_storage_account_name(storage_endpoint):
    return urlparse(storage_endpoint).netloc.split('.')[0]


# Gets storage account key by querying storage ARM API.
def _get_storage_endpoint(
        cli_ctx,
        storage_account,
        resource_group_name):

    # Get storage account
    client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    account = client.storage_accounts.get_properties(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Get endpoint
    # pylint: disable=no-member
    endpoints = account.primary_endpoints
    try:
        return endpoints.blob
    except AttributeError:
        raise CLIError("The storage account with name '{}' (id '{}') has no blob endpoint. Use a"
                       " different storage account.".format(account.name, account.id))


# Gets storage account key by querying storage ARM API.
def _get_storage_key(
        cli_ctx,
        storage_account,
        resource_group_name,
        use_secondary_key):

    # Get storage keys
    client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    keys = client.storage_accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Choose storage key
    index = 1 if use_secondary_key else 0
    return keys.keys[index].value  # pylint: disable=no-member


# Common code for updating audit and threat detection policy
def _db_security_policy_update(
        cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        use_secondary_key):

    # Validate storage endpoint arguments
    if storage_endpoint and storage_account:
        raise CLIError('--storage-endpoint and --storage-account cannot both be specified.')

    # Set storage endpoint
    if storage_endpoint:
        instance.storage_endpoint = storage_endpoint
    if storage_account:
        storage_resource_group = _find_storage_account_resource_group(cli_ctx, storage_account)
        instance.storage_endpoint = _get_storage_endpoint(cli_ctx, storage_account, storage_resource_group)

    # Set storage access key
    if storage_account_access_key:
        # Access key is specified
        instance.storage_account_access_key = storage_account_access_key
    elif enabled:
        # Access key is not specified, but state is Enabled.
        # If state is Enabled, then access key property is required in PUT. However access key is
        # readonly (GET returns empty string for access key), so we need to determine the value
        # and then PUT it back. (We don't want the user to be force to specify this, because that
        # would be very annoying when updating non-storage-related properties).
        # This doesn't work if the user used generic update args, i.e. `--set state=Enabled`
        # instead of `--state Enabled`, since the generic update args are applied after this custom
        # function, but at least we tried.
        if not storage_account:
            storage_account = _get_storage_account_name(instance.storage_endpoint)
            storage_resource_group = _find_storage_account_resource_group(cli_ctx, storage_account)

        instance.storage_account_access_key = _get_storage_key(
            cli_ctx,
            storage_account,
            storage_resource_group,
            use_secondary_key)


# Update audit policy. Custom update function to apply parameters to instance.
def db_audit_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        audit_actions_and_groups=None,
        retention_days=None):

    # Apply state
    if state:
        instance.state = BlobAuditingPolicyState[state.lower()]
    enabled = instance.state.value.lower() == BlobAuditingPolicyState.enabled.value.lower()  # pylint: disable=no-member

    # Set storage-related properties
    _db_security_policy_update(
        cmd.cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        instance.is_storage_secondary_key_in_use)

    # Set other properties
    if audit_actions_and_groups:
        instance.audit_actions_and_groups = audit_actions_and_groups

    if retention_days:
        instance.retention_days = retention_days

    return instance


# Update threat detection policy. Custom update function to apply parameters to instance.
def db_threat_detection_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        retention_days=None,
        email_addresses=None,
        disabled_alerts=None,
        email_account_admins=None):

    # Apply state
    if state:
        instance.state = SecurityAlertPolicyState[state.lower()]
    enabled = instance.state.value.lower() == SecurityAlertPolicyState.enabled.value.lower()  # pylint: disable=no-member

    # Set storage-related properties
    _db_security_policy_update(
        cmd.cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        False)

    # Set other properties
    if retention_days:
        instance.retention_days = retention_days

    if email_addresses:
        instance.email_addresses = ";".join(email_addresses)

    if disabled_alerts:
        instance.disabled_alerts = ";".join(disabled_alerts)

    if email_account_admins:
        instance.email_account_admins = email_account_admins

    return instance


###############################################
#                sql dw                       #
###############################################


# Creates a datawarehouse. Wrapper function which uses the server location so that the user doesn't
# need to specify location.
def dw_create(
        cmd,
        client,
        database_name,
        server_name,
        resource_group_name,
        no_wait=False,
        **kwargs):

    # Set edition
    kwargs['edition'] = DatabaseEdition.data_warehouse.value

    # Create
    return _db_dw_create(
        cmd.cli_ctx,
        client,
        DatabaseIdentity(cmd.cli_ctx, database_name, server_name, resource_group_name),
        no_wait,
        kwargs)


# Lists databases in a server or elastic pool.
def dw_list(
        client,
        server_name,
        resource_group_name):

    return client.list_by_server(
        resource_group_name=resource_group_name,
        server_name=server_name,
        # OData filter to include only DW's
        filter="properties/edition eq '{}'".format(DatabaseEdition.data_warehouse.value))


# Update data warehouse. Custom update function to apply parameters to instance.
def dw_update(
        instance,
        max_size_bytes=None,
        requested_service_objective_name=None):

    # Null out requested_service_objective_id, because if requested_service_objective_id is
    # specified then requested_service_objective_name is ignored.
    instance.requested_service_objective_id = None

    # Apply param values to instance
    instance.max_size_bytes = max_size_bytes or instance.max_size_bytes
    instance.requested_service_objective_name = (
        requested_service_objective_name or requested_service_objective_name)

    return instance


###############################################
#                sql elastic-pool             #
###############################################


# Creates an elastic pool. Wrapper function which uses the server location so that the user doesn't
# need to specify location.
def elastic_pool_create(
        cmd,
        client,
        server_name,
        resource_group_name,
        elastic_pool_name,
        **kwargs):

    # Determine server location
    kwargs['location'] = _get_server_location(
        cmd.cli_ctx,
        server_name=server_name,
        resource_group_name=resource_group_name)

    # Create
    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        elastic_pool_name=elastic_pool_name,
        parameters=kwargs)


# Update elastic pool. Custom update function to apply parameters to instance.
def elastic_pool_update(
        instance,
        database_dtu_max=None,
        database_dtu_min=None,
        dtu=None,
        storage_mb=None,
        zone_redundant=None):

    # Apply params to instance
    instance.database_dtu_max = database_dtu_max or instance.database_dtu_max
    instance.database_dtu_min = database_dtu_min or instance.database_dtu_min
    instance.dtu = dtu or instance.dtu
    instance.storage_mb = storage_mb or instance.storage_mb
    instance.zone_redundant = zone_redundant

    return instance


class ElasticPoolCapabilitiesAdditionalDetails(Enum):  # pylint: disable=too-few-public-methods
    max_size = 'max-size'
    db_min_dtu = 'db-min-dtu'
    db_max_dtu = 'db-max-dtu'
    db_max_size = 'db-max-size'


def elastic_pool_list_capabilities(
        client,
        location,
        edition=None,
        dtu=None,
        show_details=None):

    # Fixup parameters
    if not show_details:
        show_details = []
    if dtu:
        dtu = int(dtu)

    # Get capabilities tree from server
    capabilities = client.list_by_location(location)

    # Get subtree related to elastic pools
    editions = next(sv for sv in capabilities.supported_server_versions
                    if sv.name == _DEFAULT_SERVER_VERSION).supported_elastic_pool_editions

    # Filter by edition
    if edition:
        editions = [e for e in editions if e.name.lower() == edition.lower()]

    # Filter by dtu
    if dtu:
        for e in editions:
            e.supported_elastic_pool_dtus = [
                d for d in e.supported_elastic_pool_dtus
                if d.limit == dtu]

    # Remove editions with no service objectives (due to filters)
    editions = [e for e in editions if e.supported_elastic_pool_dtus]

    for e in editions:
        for d in e.supported_elastic_pool_dtus:
            # Optionally hide supported max sizes
            if ElasticPoolCapabilitiesAdditionalDetails.max_size.value not in show_details:
                d.supported_max_sizes = []

            # Optionally hide per database min & max dtus. min dtus are nested inside max dtus,
            # so only hide max dtus if both min and max should be hidden.
            if ElasticPoolCapabilitiesAdditionalDetails.db_min_dtu.value not in show_details:
                if ElasticPoolCapabilitiesAdditionalDetails.db_max_dtu.value not in show_details:
                    d.supported_per_database_max_dtus = []

                for md in d.supported_per_database_max_dtus:
                    md.supported_per_database_min_dtus = []

            # Optionally hide supported per db max sizes
            if ElasticPoolCapabilitiesAdditionalDetails.db_max_size.value not in show_details:
                d.supported_per_database_max_sizes = []

    return editions


###############################################
#                sql server                   #
###############################################

def server_create(
        client,
        resource_group_name,
        server_name,
        assign_identity=False,
        **kwargs):

    if assign_identity:
        kwargs['identity'] = ResourceIdentity(type=IdentityType.system_assigned.value)

    # Create
    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        parameters=kwargs)


# Lists servers in a resource group or subscription
def server_list(
        client,
        resource_group_name=None):

    if resource_group_name:
        # List all servers in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all servers in the subscription
    return client.list()


# Update server. Custom update function to apply parameters to instance.
def server_update(
        instance,
        administrator_login_password=None,
        assign_identity=False):

    # Once assigned, the identity cannot be removed
    if instance.identity is None and assign_identity:
        instance.identity = ResourceIdentity(type=IdentityType.system_assigned.value)

    # Apply params to instance
    instance.administrator_login_password = (
        administrator_login_password or instance.administrator_login_password)

    return instance


#####
#           sql server ad-admin
#####


def server_ad_admin_set(
        cmd,
        client,
        resource_group_name,
        server_name,
        **kwargs):

    profile = Profile(cli_ctx=cmd.cli_ctx)
    sub = profile.get_subscription()
    kwargs['tenant_id'] = sub['tenantId']

    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        properties=kwargs)


# Update server AD admin. Custom update function to apply parameters to instance.
def server_ad_admin_update(
        instance,
        login=None,
        sid=None,
        tenant_id=None):

    # Apply params to instance
    instance.login = login or instance.login
    instance.sid = sid or instance.sid
    instance.tenant_id = tenant_id or instance.tenant_id

    return instance


#####
#           sql server firewall-rule
#####


# Creates a firewall rule with special start/end ip address value
# that represents all azure ips.
def firewall_rule_allow_all_azure_ips(
        client,
        server_name,
        resource_group_name):

    # Name of the rule that will be created
    rule_name = 'AllowAllAzureIPs'

    # Special start/end IP that represents allowing all azure ips
    azure_ip_addr = '0.0.0.0'

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name=rule_name,
        start_ip_address=azure_ip_addr,
        end_ip_address=azure_ip_addr)


# Update firewall rule. Custom update function is required,
# see https://github.com/Azure/azure-cli/issues/2264
def firewall_rule_update(
        client,
        firewall_rule_name,
        server_name,
        resource_group_name,
        start_ip_address=None,
        end_ip_address=None):

    # Get existing instance
    instance = client.get(
        firewall_rule_name=firewall_rule_name,
        server_name=server_name,
        resource_group_name=resource_group_name)

    # Send update
    return client.create_or_update(
        firewall_rule_name=firewall_rule_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        start_ip_address=start_ip_address or instance.start_ip_address,
        end_ip_address=end_ip_address or instance.end_ip_address)


#####
#           sql server key
#####


def server_key_create(
        client,
        resource_group_name,
        server_name,
        kid=None):

    key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name,
        parameters=ServerKey(
            server_key_type=ServerKeyType.azure_key_vault.value,
            uri=kid
        )
    )


def server_key_get(
        client,
        resource_group_name,
        server_name,
        kid):

    key_name = _get_server_key_name_from_uri(kid)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def server_key_delete(
        client,
        resource_group_name,
        server_name,
        kid):

    key_name = _get_server_key_name_from_uri(kid)

    return client.delete(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


# The SQL server key API requires that the server key has a specific name
# based on the vault, key and key version.
def _get_server_key_name_from_uri(uri):

    match = re.match(r'^https(.)+\.vault(.)+\/keys\/[^\/]+\/[0-9a-zA-Z]+$', uri)

    if match is None:
        raise CLIError('The provided uri is invalid. Please provide a valid Azure Key Vault key id.  For example: '
                       '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

    vault = uri.split('.')[0].split('/')[-1]
    key = uri.split('/')[-2]
    version = uri.split('/')[-1]
    return '{}_{}_{}'.format(vault, key, version)


#####
#           sql server dns-alias
#####


def server_dns_alias_set(
        cmd,
        client,
        resource_group_name,
        server_name,
        dns_alias_name,
        original_server_name,
        original_subscription_id=None,
        original_resource_group_name=None):

    # Build the old alias id
    old_alias_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/dnsAliases/{}".format(
        quote(original_subscription_id or get_subscription_id(cmd.cli_ctx)),
        quote(original_resource_group_name or resource_group_name),
        quote(original_server_name),
        quote(dns_alias_name))

    return client.acquire(
        resource_group_name=resource_group_name,
        server_name=server_name,
        dns_alias_name=dns_alias_name,
        old_server_dns_alias_id=old_alias_id
    )

#####
#           sql server encryption-protector
#####


def encryption_protector_update(
        client,
        resource_group_name,
        server_name,
        server_key_type,
        kid=None):

    if server_key_type == ServerKeyType.service_managed.value:
        key_name = 'ServiceManaged'
    else:
        if kid is None:
            raise CLIError('A uri must be provided if the server_key_type is AzureKeyVault.')
        else:
            key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters=EncryptionProtector(
            server_key_type=server_key_type,
            server_key_name=key_name
        )
    )
