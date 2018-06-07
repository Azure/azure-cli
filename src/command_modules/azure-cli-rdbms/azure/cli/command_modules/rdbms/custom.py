# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.rdbms.mysql.operations.servers_operations import ServersOperations
from ._client_factory import get_mysql_management_client, get_postgresql_management_client

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}


def _server_create(cmd, client, resource_group_name, server_name, sku_name, no_wait=False,
                   location=None, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None):
    provider = 'Microsoft.DBForMySQL' if isinstance(client, ServersOperations) else 'Microsoft.DBforPostgreSQL'
    parameters = None
    if provider == 'Microsoft.DBForMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                storage_profile=mysql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb)),
            location=location,
            tags=tags)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            sku=postgresql.models.Sku(name=sku_name),
            properties=postgresql.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                storage_profile=postgresql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb)),
            location=location,
            tags=tags)

    return client.create(resource_group_name, server_name, parameters)


# Need to replace source server name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# arguments and validators
def _server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, no_wait=False):
    provider = 'Microsoft.DBForMySQL' if isinstance(client, ServersOperations) else 'Microsoft.DBforPostgreSQL'
    parameters = None
    if provider == 'Microsoft.DBForMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            properties=mysql.models.ServerPropertiesForRestore())
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            properties=postgresql.models.ServerPropertiesForRestore())

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


# need to replace source server name with source server id, so customer server georestore function
# The parameter list should be the same as that in factory to use the ParametersContext
# auguments and validators
def _server_georestore(cmd, client, resource_group_name, server_name, sku_name, location, source_server,
                       backup_retention=None, geo_redundant_backup=None, no_wait=False, **kwargs):
    provider = 'Microsoft.DBForMySQL' if isinstance(client, ServersOperations) else 'Microsoft.DBforPostgreSQL'
    parameters = None
    if provider == 'Microsoft.DBForMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForGeoRestore(
                storage_profile=mysql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup
                )),
            location=location)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            sku=postgresql.models.Sku(name=sku_name),
            properties=postgresql.models.ServerPropertiesForGeoRestore(
                storage_profile=postgresql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup
                )),
            location=location)

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                        resource_group=resource_group_name,
                                        namespace=provider,
                                        type='servers',
                                        name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))

    parameters.properties.source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
        if parameters.sku.name is None:
            parameters.sku.name = source_server_object.sku.name
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))

    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)


def _server_update_custom_func(instance,
                               capacity=None,
                               storage_mb=None,
                               backup_retention_days=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               tags=None):
    from azure.mgmt.rdbms.mysql.models import StorageProfile  # pylint: disable=unused-variable
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerUpdateParameters = getattr(module, 'ServerUpdateParameters')

    if capacity is not None:
        instance.sku.name = _get_sku_name(instance.sku.tier, instance.sku.family, capacity)
        instance.sku.capacity = capacity
    else:
        instance.sku = None

    if storage_mb is not None:
        instance.storage_profile.storage_mb = storage_mb

    if backup_retention_days is not None:
        instance.storage_profile.backup_retention_days = backup_retention_days

    params = ServerUpdateParameters(sku=instance.sku,
                                    storage_profile=instance.storage_profile,
                                    administrator_login_password=administrator_login_password,
                                    version=None,
                                    ssl_enforcement=ssl_enforcement,
                                    tags=tags)

    return params


def _server_mysql_get(cmd, resource_group_name, server_name):
    client = get_mysql_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _server_postgresql_get(cmd, resource_group_name, server_name):
    client = get_postgresql_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _server_update_get(client, resource_group_name, server_name):
    return client.get(resource_group_name, server_name)


def _server_update_set(client, resource_group_name, server_name, parameters):
    return client.update(resource_group_name, server_name, parameters)


def _get_sku_name(tier, family, capacity):
    return '{}_{}_{}'.format(SKU_TIER_MAP[tier], family, str(capacity))


def _firewall_rule_custom_getter(client, resource_group_name, server_name, firewall_rule_name):
    return client.get(resource_group_name, server_name, firewall_rule_name)


def _firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    return client.create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters.start_ip_address,
        parameters.end_ip_address)


def _firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


# Custom functions for server logs
def _download_log_files(
        client,
        resource_group_name,
        server_name,
        file_name):
    from six.moves.urllib.request import urlretrieve  # pylint: disable=import-error

    # list all files
    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name)


def _list_log_files_with_filter(client, resource_group_name, server_name, filename_contains=None,
                                file_last_written=None, max_file_size=None):
    import re
    from datetime import datetime, timedelta
    from dateutil.tz import tzutc   # pylint: disable=import-error

    # list all files
    all_files = client.list_by_server(resource_group_name, server_name)
    files = []

    if file_last_written is None:
        file_last_written = 72
    time_line = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(hours=file_last_written)

    for f in all_files:
        if f.last_modified_time < time_line:
            continue
        if filename_contains is not None and re.search(filename_contains, f.name) is None:
            continue
        if max_file_size is not None and f.size_in_kb > max_file_size:
            continue

        del f.created_time
        files.append(f)

    return files


# Custom functions for list servers
def _server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()
