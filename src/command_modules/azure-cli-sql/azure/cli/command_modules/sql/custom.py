# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import (
    get_sql_servers_operation,
    get_sql_database_operations,
    get_sql_elasticpools_operations
)

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
#           sql server firewall
#####

# Creates a firewall rule with special start/end ip address value
# that represents all azure ips.
def firewall_allow_all_azure_ips(
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
