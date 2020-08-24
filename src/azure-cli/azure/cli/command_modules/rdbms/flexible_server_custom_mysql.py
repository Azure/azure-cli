# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import uuid
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt.rdbms.mysql.operations._servers_operations import ServersOperations as MySqlServersOperations
from azure.mgmt.rdbms.mysql.flexibleservers.operations._servers_operations import ServersOperations as MySqlFlexibleServersOperations
from azure.mgmt.rdbms.mariadb.operations._servers_operations import ServersOperations as MariaDBServersOperations
from ._client_factory import get_mariadb_management_client, get_mysql_flexible_management_client, get_postgresql_flexible_management_client, cf_postgres_firewall_rules, cf_postgres_db, cf_postgres_config

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
logger = get_logger(__name__)


def _flexible_server_create(cmd, client, resource_group_name, server_name, sku_name, tier,
                   location=None, no_wait=False, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None, infrastructure_encryption=None, minimal_tls_version=None):
    from azure.mgmt.rdbms import mysql
    ### TO DO: This is not complete yet, waiting on deployment
    parameters = mysql.flexibleservers.models.Server(
        sku=mysql.flexibleservers.models.Sku(name=sku_name, tier = tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        ssl_enforcement=ssl_enforcement,
        public_network_access=public_network_access,
        infrastructure_encryption=infrastructure_encryption,
        storage_profile=mysql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            # geo_redundant_backup=geo_redundant_backup,
            storage_mb=storage_mb),  ##!!! required I think otherwise data is null error seen in backend exceptions
        # storage_autogrow=auto_grow),
        location=location,
        tags=tags)
    if assign_identity:
        parameters.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
    return client.create(resource_group_name, server_name, parameters)

# Need to replace source server name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# arguments and validators
def _flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, location=None, no_wait=False):
    provider = 'Microsoft.DBforMySQL'

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=provider,
                type='servers',
                name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))
    from azure.mgmt.rdbms import mysql
    parameters = mysql.flexibleservers.models.Server(
        source_server=source_server,
        restore_point_in_time=restore_point_in_time,
        location=location
    )

    # Here is a workaround that we don't support cross-region restore currently,
    # so the location must be set as the same as source server (not the resource group)
    id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        parameters.location = source_server_object.location
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))
    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)

# Update commands
def _flexible_server_update_custom_func(instance,
                               sku_name=None,
                               storage_mb=None,
                               backup_retention=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               tags=None,
                               auto_grow=None,
                               assign_identity=False,
                               public_network_access=None,
                               minimal_tls_version=None):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path) # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name
        instance.sku.capacity = None
        instance.sku.family = None
        instance.sku.tier = None
    else:
        instance.sku = None

    if storage_mb:
        instance.storage_profile.storage_mb = storage_mb

    if backup_retention:
        instance.storage_profile.backup_retention_days = backup_retention

    if auto_grow:
        instance.storage_profile.storage_autogrow = auto_grow

    params = ServerForUpdate(sku=instance.sku,
                                    storage_profile=instance.storage_profile,
                                    administrator_login_password=administrator_login_password,
                                    version=None,
                                    ssl_enforcement=ssl_enforcement,
                                    tags=tags,
                                    public_network_access=public_network_access,
                                    minimal_tls_version=minimal_tls_version)

    if assign_identity:
        if server_module_path.find('mysql'):
            from azure.mgmt.rdbms import mysql
            if instance.identity is None:
                instance.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
            params.identity = instance.identity

    return params

## Replica commands

# Custom functions for server replica, will add PostgreSQL part after backend ready in future
def _flexible_replica_create(cmd, client, resource_group_name, server_name, source_server, no_wait=False, location=None, sku_name=None, tier=None, **kwargs):
    provider = 'Microsoft.DBforMySQL'

    # set source server id
    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                        resource_group=resource_group_name,
                                        namespace=provider,
                                        type='servers',
                                        name=source_server)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(source_server))

    source_server_id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except CloudError as e:
        raise CLIError('Unable to get source server: {}.'.format(str(e)))

    if location is None:
        location = source_server_object.location

    if sku_name is None:
        sku_name = source_server_object.sku.name
    if tier is None:
        tier = source_server_object.sku.tier

    from azure.mgmt.rdbms import mysql
    parameters = mysql.flexibleservers.models.Server(
        sku=mysql.flexibleservers.models.Sku(name=sku_name,tier=tier),
        source_server_id=source_server,
        location=location)

    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)


def _flexible_replica_stop(client, resource_group_name, server_name):
    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise CLIError('Unable to get server: {}.'.format(str(e)))

    if server_object.replication_role.lower() != "replica":
        raise CLIError('Server {} is not a replica server.'.format(server_name))

    from importlib import import_module
    server_module_path = server_object.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    params = ServerForUpdate(replication_role='None')

    return client.update(resource_group_name, server_name, params)



# Common between sterling and meru
# Custom functions for list servers
def _server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()

def _flexible_firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance

def _flexible_server_mysql_get(cmd, resource_group_name, server_name):
    client = get_mysql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)
