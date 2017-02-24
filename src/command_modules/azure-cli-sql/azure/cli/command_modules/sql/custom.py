# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import (
    get_sql_servers_operation,
    get_sql_database_operations,
    get_sql_elasticpools_operations
)

from azure.cli.core.commands.client_factory import get_subscription_id

###############################################
#                Common funcs                 #
###############################################

# Determines server location
def get_server_location(server_name, resource_group_name):
    server_client = get_sql_servers_operation(None)
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
    kwargs['location'] = get_server_location(server_name=server_name, resource_group_name=resource_group_name)

    # Create
    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        database_name=database_name,
        parameters=kwargs)

# Common code for special db create modes.
def _db_create_special(
    client,
    database_name,
    server_name,
    resource_group_name,
    dest_database_name,
    dest_server_name,
    dest_resource_group_name,
    kwargs):

    # Determine server location
    kwargs['location'] = get_server_location(server_name=server_name, resource_group_name=resource_group_name)

    # Set create mode properties
    from urllib.parse import quote
    subscription_id = get_subscription_id()
    kwargs['source_database_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/databases/{}'.format(
        quote(subscription_id),
        quote(resource_group_name),
        quote(server_name),
        quote(database_name))

    # Create
    return client.create_or_update(
        server_name=dest_server_name,
        resource_group_name=dest_resource_group_name,
        database_name=dest_database_name,
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
        database_name,
        server_name,
        resource_group_name,
        dest_name,
        dest_server_name,
        dest_resource_group_name,
        kwargs)

# Copies a secondary replica. Wrapper function to make create mode more convenient.
def db_create_secondary(
    client,
    database_name,
    server_name,
    resource_group_name,
    secondary_server_name,
    secondary_resource_group_name=None,
    **kwargs):

    # Determine optional values
    secondary_resource_group_name = secondary_resource_group_name or resource_group_name

    # Set create mode
    kwargs['create_mode'] = 'OnlineSecondary'

    return _db_create_special(
        client,
        database_name,
        server_name,
        resource_group_name,
        database_name, # replica must have the same database name as the source db
        secondary_server_name,
        secondary_resource_group_name,
        kwargs)

# Creates a database from a database point in time backup. Wrapper function to make create mode more convenient.
#def db_restore(
#    client,
#    database_name,
#    server_name,
#    resource_group_name,
#    restore_point_in_time,
#    dest_name,
#    dest_server_name=None,
#    dest_resource_group_name=None,
#    **kwargs):

#    # Determine optional values
#    dest_resource_group_name = dest_resource_group_name or resource_group_name
#    dest_server_name = dest_server_name or server_name

#    # Set create mode: TODO - doesn't yet work because restorePointInTime is not yet in Swagger spec
#    kwargs['create_mode'] = 'PointInTimeRestore'
#    #kwargs['restore_point_in_time'] = restore_point_in_time

#    return _db_create_special(
#        client,
#        database_name,
#        server_name,
#        resource_group_name,
#        dest_name,
#        dest_server_name,
#        dest_resource_group_name,
#        kwargs)

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
        return 
    else:
        # List all databases in the server
        return client.list_by_server(
            resource_group_name=resource_group_name,
            server_name=server_name)

# Update database. Custom update function because we need to insert some helper code.
def db_update(
    instance,
    #elastic_pool_name=None, # Unsupported for now until it's tested
    max_size_bytes=None,
    requested_service_objective_name=None):

    # Verify that elastic_pool_name and requested_service_objective_name are consistent # TODO

    # Null out requested_service_objective_id, because if requested_service_objective_id is
    # specified then requested_service_objective_name is ignored.
    instance.requested_service_objective_id = None

    # Validation done - update the instance
    # The base generic update command should be able to do this part, but
    # it seems to not be working, so we just do this manually here.
    #instance.elastic_pool_name = elastic_pool_name or instance.elastic_pool_name # Unsupported for now until it's tested
    instance.max_size_bytes = max_size_bytes or instance.max_size_bytes
    instance.requested_service_objective_name = requested_service_objective_name or instance.requested_service_objective_name

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
    kwargs['location'] = get_server_location(server_name=server_name, resource_group_name=resource_group_name)

    # Create
    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        elastic_pool_name=elastic_pool_name,
        parameters=kwargs)

###############################################
#                sql server                   #
###############################################

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

## There's no way to implement update firewall rule - https://github.com/Azure/azure-cli/issues/2264
## Update firewall rule. Custom update function to apply param values.
#def firewall_rule_update(
#    instance,
#    start_ip_address=None,
#    end_ip_address=None):

#    # Validation done - update the instance
#    # The base generic update command should be able to do this part, but
#    # it seems to not be working, so we just do this manually here.
#    instance.start_ip_address = start_ip_address or instance.start_ip_address
#    instance.end_ip_address = end_ip_address or instance.end_ip_address

#    return instance
