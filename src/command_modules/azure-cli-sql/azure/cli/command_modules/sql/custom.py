# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import (
    get_sql_servers_operation,
    get_sql_elasticpools_operations
)

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core._util import CLIError
from azure.mgmt.sql.models.sql_management_client_enums import (
    CreateMode,
    DatabaseEditions,
    ReplicationRole,
    ServiceObjectiveName,
)

###############################################
#                Common funcs                 #
###############################################


# Determines server location
def get_server_location(server_name, resource_group_name):
    server_client = get_sql_servers_operation(None)
    # pylint: disable=no-member
    return server_client.get_by_resource_group(
        server_name=server_name,
        resource_group_name=resource_group_name).location


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
    if edition and edition.lower() == DatabaseEditions.data_warehouse.value.lower():
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
    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from six.moves.urllib.parse import quote  # pylint: disable=import-error
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
def db_copy(  # pylint: disable=too-many-arguments
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
def db_create_replica(  # pylint: disable=too-many-arguments
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
def db_restore(  # pylint: disable=too-many-arguments
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

    if len(links) == 0:
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


def db_delete_replica_link(  # pylint: disable=too-many-arguments
        client,
        database_name,
        server_name,
        resource_group_name,
        # Partner dbs must have the same name as one another
        partner_server_name,
        partner_resource_group_name=None):

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


# Lists databases in a server or elastic pool.
def db_list(
        client,
        server_name,
        resource_group_name,
        elastic_pool_name=None):

    if elastic_pool_name:
        # List all databases in the elastic pool
        pool_client = get_sql_elasticpools_operations(None)
        return pool_client.list_databases(
            server_name=server_name,
            resource_group_name=resource_group_name,
            elastic_pool_name=elastic_pool_name,
            filter=filter)
    else:
        # List all databases in the server
        return client.list_by_server(
            resource_group_name=resource_group_name,
            server_name=server_name)


# Update database. Custom update function to apply parameters to instance.
def db_update(
        instance,
        elastic_pool_name=None,
        max_size_bytes=None,
        requested_service_objective_name=None):

    # Verify edition
    if instance.edition.lower() == DatabaseEditions.data_warehouse.value.lower():
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
    kwargs['edition'] = DatabaseEditions.data_warehouse.value

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
        filter="properties/edition eq '{}'".format(DatabaseEditions.data_warehouse.value))


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

    return client.create_or_update_firewall_rule(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name=rule_name,
        start_ip_address=azure_ip_addr,
        end_ip_address=azure_ip_addr)


# Update firewall rule. Custom update function is required,
# see https://github.com/Azure/azure-cli/issues/2264
def firewall_rule_update(  # pylint: disable=too-many-arguments
        client,
        firewall_rule_name,
        server_name,
        resource_group_name,
        start_ip_address=None,
        end_ip_address=None):

    # Get existing instance
    instance = client.get_firewall_rule(
        firewall_rule_name=firewall_rule_name,
        server_name=server_name,
        resource_group_name=resource_group_name)

    # Send update
    return client.create_or_update_firewall_rule(
        firewall_rule_name=firewall_rule_name,
        server_name=server_name,
        resource_group_name=resource_group_name,
        start_ip_address=start_ip_address or instance.start_ip_address,
        end_ip_address=end_ip_address or instance.end_ip_address)
