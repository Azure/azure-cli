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


def _flexible_server_create(cmd, client, resource_group_name, server_name, sku_name,
                   location=None, no_wait=False, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None, infrastructure_encryption=None, minimal_tls_version=None):
    from azure.mgmt.rdbms import mysql

    ### TO DO: This is not complete yet, waiting on deployment
    parameters = mysql.flexibleservers.models.Server(
        sku=mysql.flexibleservers.models.Sku(name=sku_name, tier="GeneralPurpose"),
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
        create_mode="Default",  # can also be create??
        tags=tags)
    if assign_identity:
        parameters.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
    return client.create(resource_group_name, server_name, parameters)

# Need to replace source server name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# arguments and validators
def _flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, no_wait=False):
    provider = 'Microsoft.DBforPostgreSQL'
    if isinstance(client, MySqlServersOperations):
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        provider = 'Microsoft.DBforMariaDB'

    parameters = None
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

    if provider == 'Microsoft.DBforMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            properties=mysql.models.ServerPropertiesForRestore(
                source_server_id=source_server,
                restore_point_in_time=restore_point_in_time),
            location=None)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            properties=postgresql.models.ServerPropertiesForRestore(
                source_server_id=source_server,
                restore_point_in_time=restore_point_in_time),
            location=None)
    elif provider == 'Microsoft.DBforMariaDB':
        from azure.mgmt.rdbms import mariadb
        parameters = mariadb.models.ServerForCreate(
            properties=mariadb.models.ServerPropertiesForRestore(
                source_server_id=source_server,
                restore_point_in_time=restore_point_in_time),
            location=None)

    parameters.properties.source_server_id = source_server
    parameters.properties.restore_point_in_time = restore_point_in_time

    # Here is a workaround that we don't support cross-region restore currently,
    # so the location must be set as the same as source server (not the resource group)
    id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        parameters.location = source_server_object.location
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))

    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)


# Common between sterling and meru
# Custom functions for list servers
def _server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()
