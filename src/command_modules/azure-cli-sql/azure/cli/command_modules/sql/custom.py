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


# Creates a database. Wrapper function which uses the server location so that the user doesn't
# need to specify location.
def db_create(
        client,
        server_name,
        resource_group_name,
        database_name,
        **kwargs):

    # Determine server location
    kwargs['location'] = get_server_location(
        server_name=server_name,
        resource_group_name=resource_group_name)

    # Create
    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        database_name=database_name,
        parameters=kwargs)


class DatabaseIdentity(object):  # pylint: disable=too-few-public-methods
    def __init__(self, database_name, server_name, resource_group_name):
        self.database_name = database_name
        self.server_name = server_name
        self.resource_group_name = resource_group_name


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
    # url parse package has different names in Python 2 and 3.
    # So we have to import it differently depending on Python version.
    # pylint: disable=no-name-in-module, import-error
    import sys
    if sys.version_info >= (3,):
        from urllib.parse import quote
    else:
        from urllib import quote

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


# Copies a secondary replica. Wrapper function to make create mode more convenient.
def db_create_secondary(  # pylint: disable=too-many-arguments
        client,
        database_name,
        server_name,
        resource_group_name,
        # Replica must have the same database name as the source db
        secondary_server_name,
        secondary_resource_group_name=None,
        **kwargs):

    # Determine optional values
    secondary_resource_group_name = secondary_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = 'OnlineSecondary'

    # Replica must have the same database name as the source db
    return _db_create_special(
        client,
        DatabaseIdentity(database_name, server_name, resource_group_name),
        DatabaseIdentity(database_name, secondary_server_name, secondary_resource_group_name),
        kwargs)


# Creates a database from a database point in time backup.
# Wrapper function to make create mode more convenient.
# def db_restore(
#     client,
#     database_name,
#     server_name,
#     resource_group_name,
#     restore_point_in_time,
#     dest_name,
#     dest_server_name=None,
#     dest_resource_group_name=None,
#     **kwargs):

#     # Determine optional values
#     dest_resource_group_name = dest_resource_group_name or resource_group_name
#     dest_server_name = dest_server_name or server_name

#     # Set create mode: TODO - doesn't yet work because restorePointInTime is not yet in Swagger
#     kwargs['create_mode'] = 'PointInTimeRestore'
#     #kwargs['restore_point_in_time'] = restore_point_in_time

#     return _db_create_special(
#         client,
#         database_name,
#         server_name,
#         resource_group_name,
#         dest_name,
#         dest_server_name,
#         dest_resource_group_name,
#         kwargs)


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
            elastic_pool_name=elastic_pool_name)
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
            requested_service_objective_name != 'ElasticPool'):
        raise CLIError('If elastic pool is specified, service objective must be'
                       ' unspecified or equal \'ElasticPool\'.')

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
