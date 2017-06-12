# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from azure.cli.core.commands.client_factory import (
    get_mgmt_service_client,
    get_subscription_id)
from azure.cli.core.util import CLIError
from azure.mgmt.sql.models.sql_management_client_enums import (
    BlobAuditingPolicyState,
    CreateMode,
    DatabaseEdition,
    ReplicationRole,
    SecurityAlertPolicyState,
    ServiceObjectiveName,
    StorageKeyType
)
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient

# url parse package has different names in Python 2 and 3. 'six' package works cross-version.
from six.moves.urllib.parse import (quote, urlparse)  # pylint: disable=import-error

from ._util import (
    get_sql_servers_operations,
    get_sql_elastic_pools_operations
)

###############################################
#                Common funcs                 #
###############################################


# Determines server location
def get_server_location(server_name, resource_group_name):
    server_client = get_sql_servers_operations(None)
    # pylint: disable=no-member
    return server_client.get(
        server_name=server_name,
        resource_group_name=resource_group_name).location


_DEFAULT_SERVER_VERSION = "12.0"


###############################################
#                sql db                       #
###############################################


# Helper class to bundle up database identity properties
class DatabaseIdentity(object):  # pylint: disable=too-few-public-methods
    def __init__(self, database_name, server_name, resource_group_name):
        self.database_name = database_name
        self.server_name = server_name
        self.resource_group_name = resource_group_name


# Creates a database or datawarehouse. Wrapper function which uses the server location so that
# the user doesn't need to specify location.
def _db_dw_create(
        client,
        db_id,
        kwargs):

    # Determine server location
    kwargs['location'] = get_server_location(
        server_name=db_id.server_name,
        resource_group_name=db_id.resource_group_name)

    # Create
    return client.create_or_update(
        server_name=db_id.server_name,
        resource_group_name=db_id.resource_group_name,
        database_name=db_id.database_name,
        parameters=kwargs)


# Creates a database. Wrapper function which uses the server location so that the user doesn't
# need to specify location.
def db_create(
        client,
        database_name,
        server_name,
        resource_group_name,
        **kwargs):

    # Verify edition
    edition = kwargs.get('edition')  # kwags['edition'] throws KeyError if not in dictionary
    if edition and edition.lower() == DatabaseEdition.data_warehouse.value.lower():
        raise CLIError('Azure SQL Data Warehouse can be created with the command'
                       ' `az sql dw create`.')

    return _db_dw_create(
        client,
        DatabaseIdentity(database_name, server_name, resource_group_name),
        kwargs)


# Common code for special db create modes.
def _db_create_special(
        client,
        source_db,
        dest_db,
        kwargs):

    # Determine server location
    kwargs['location'] = get_server_location(
        server_name=dest_db.server_name,
        resource_group_name=dest_db.resource_group_name)

    # Set create mode properties
    subscription_id = get_subscription_id()
    kwargs['source_database_id'] = (
        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/databases/{}'
        .format(quote(subscription_id),
                quote(source_db.resource_group_name),
                quote(source_db.server_name),
                quote(source_db.database_name)))

    # Create
    return client.create_or_update(
        server_name=dest_db.server_name,
        resource_group_name=dest_db.resource_group_name,
        database_name=dest_db.database_name,
        parameters=kwargs)


# Copies a database. Wrapper function to make create mode more convenient.
def db_copy(
        client,
        database_name,
        server_name,
        resource_group_name,
        dest_name,
        dest_server_name=None,
        dest_resource_group_name=None,
        **kwargs):

    # Determine optional values
    dest_server_name = dest_server_name or server_name
    dest_resource_group_name = dest_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = 'Copy'

    return _db_create_special(
        client,
        DatabaseIdentity(database_name, server_name, resource_group_name),
        DatabaseIdentity(dest_name, dest_server_name, dest_resource_group_name),
        kwargs)


# Copies a replica. Wrapper function to make create mode more convenient.
def db_create_replica(
        client,
        database_name,
        server_name,
        resource_group_name,
        # Replica must have the same database name as the source db
        partner_server_name,
        partner_resource_group_name=None,
        **kwargs):

    # Determine optional values
    partner_resource_group_name = partner_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = CreateMode.online_secondary.value

    # Replica must have the same database name as the source db
    return _db_create_special(
        client,
        DatabaseIdentity(database_name, server_name, resource_group_name),
        DatabaseIdentity(database_name, partner_server_name, partner_resource_group_name),
        kwargs)


# Creates a database from a database point in time backup.
# Wrapper function to make create mode more convenient.
def db_restore(
        client,
        database_name,
        server_name,
        resource_group_name,
        restore_point_in_time,
        dest_name,
        **kwargs):

    # Set create mode properties
    kwargs['create_mode'] = 'PointInTimeRestore'
    kwargs['restore_point_in_time'] = restore_point_in_time

    return _db_create_special(
        client,
        DatabaseIdentity(database_name, server_name, resource_group_name),
        # Cross-server restore is not supported. So dest server/group must be the same as source.
        DatabaseIdentity(dest_name, server_name, resource_group_name),
        kwargs)


# Fails over a database. Wrapper function which uses the server location so that the user doesn't
# need to specify replication link id.
def db_failover(
        client,
        database_name,
        server_name,
        resource_group_name,
        allow_data_loss=False):

    # List replication links
    links = list(client.list_replication_links(
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
        failover_func = client.failover_replication_link_allow_data_loss
    else:
        failover_func = client.failover_replication_link

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
    links = list(client.list_replication_links(
        database_name=database_name,
        server_name=server_name,
        resource_group_name=resource_group_name))

    # The link doesn't tell us the partner resource group name, so we just have to count on
    # partner server name being unique
    link = next((l for l in links if l.partner_server == partner_server_name), None)
    if not link:
        # No link exists, nothing to be done
        return

    return client.delete_replication_link(
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
    if storage_key_type.lower() == StorageKeyType.shared_access_key.value.lower():
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
        pool_client = get_sql_elastic_pools_operations(None)
        return pool_client.list_databases(
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
        requested_service_objective_name=None):

    # Verify edition
    if instance.edition.lower() == DatabaseEdition.data_warehouse.value.lower():
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

    return instance


#####
#           sql server audit-policy & threat-policy
#####


# Finds a storage account's resource group by querying ARM resource cache.
# Why do we have to do this: so we know the resource group in order to later query the storage API
# to determine the account's keys and endpoint. Why isn't this just a command line parameter:
# because if it was a command line parameter then the customer would need to specify storage
# resource group just to update some unrelated property, which is annoying and makes no sense to
# the customer.
def _find_storage_account_resource_group(name):
    storage_type = 'Microsoft.Storage/storageAccounts'
    classic_storage_type = 'Microsoft.ClassicStorage/storageAccounts'

    query = "name eq '{}' and (resourceType eq '{}' or resourceType eq '{}')".format(
        name, storage_type, classic_storage_type)

    client = get_mgmt_service_client(ResourceManagementClient)
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
        storage_account,
        resource_group_name):

    # Get storage account
    client = get_mgmt_service_client(StorageManagementClient)
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
        storage_account,
        resource_group_name,
        use_secondary_key):

    # Get storage keys
    client = get_mgmt_service_client(StorageManagementClient)
    keys = client.storage_accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Choose storage key
    index = 1 if use_secondary_key else 0
    return keys.keys[index].value  # pylint: disable=no-member


# Common code for updating audit and threat detection policy
def _db_security_policy_update(
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
        storage_resource_group = _find_storage_account_resource_group(storage_account)
        instance.storage_endpoint = _get_storage_endpoint(storage_account, storage_resource_group)

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
            storage_resource_group = _find_storage_account_resource_group(storage_account)

        instance.storage_account_access_key = _get_storage_key(
            storage_account,
            storage_resource_group,
            use_secondary_key)


# Update audit policy. Custom update function to apply parameters to instance.
def db_audit_policy_update(
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
    enabled = instance.state.value.lower() == BlobAuditingPolicyState.enabled.value.lower()

    # Set storage-related properties
    _db_security_policy_update(
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
    enabled = instance.state.value.lower() == SecurityAlertPolicyState.enabled.value.lower()

    # Set storage-related properties
    _db_security_policy_update(
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
        client,
        database_name,
        server_name,
        resource_group_name,
        **kwargs):

    # Set edition
    kwargs['edition'] = DatabaseEdition.data_warehouse.value

    # Create
    return _db_dw_create(
        client,
        DatabaseIdentity(database_name, server_name, resource_group_name),
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
        client,
        server_name,
        resource_group_name,
        elastic_pool_name,
        **kwargs):

    # Determine server location
    kwargs['location'] = get_server_location(
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
        storage_mb=None):

    # Apply params to instance
    instance.database_dtu_max = database_dtu_max or instance.database_dtu_max
    instance.database_dtu_min = database_dtu_min or instance.database_dtu_min
    instance.dtu = dtu or instance.dtu
    instance.storage_mb = storage_mb or instance.storage_mb

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


# Update server. Custom update function to apply parameters to instance.
def server_update(
        instance,
        administrator_login_password=None):

    # Apply params to instance
    instance.administrator_login_password = (
        administrator_login_password or instance.administrator_login_password)

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
