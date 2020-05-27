# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt.rdbms.mysql.operations._servers_operations import ServersOperations as MySqlServersOperations
from azure.mgmt.rdbms.mariadb.operations._servers_operations import ServersOperations as MariaDBServersOperations
from ._client_factory import get_mariadb_management_client, get_mysql_management_client, get_postgresql_management_client

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}


def _server_create(cmd, client, resource_group_name, server_name, sku_name, no_wait=False,
                   location=None, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None):
    provider = 'Microsoft.DBforPostgreSQL'
    if isinstance(client, MySqlServersOperations):
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        provider = 'Microsoft.DBforMariaDB'

    parameters = None
    if provider == 'Microsoft.DBforMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                public_network_access=public_network_access,
                storage_profile=mysql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb,
                    storage_autogrow=auto_grow)),
            location=location,
            tags=tags)
        if assign_identity:
            parameters.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            sku=postgresql.models.Sku(name=sku_name),
            properties=postgresql.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                public_network_access=public_network_access,
                storage_profile=postgresql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb,
                    storage_autogrow=auto_grow)),
            location=location,
            tags=tags)
        if assign_identity:
            parameters.identity = postgresql.models.ResourceIdentity(type=postgresql.models.IdentityType.system_assigned.value)
    elif provider == 'Microsoft.DBforMariaDB':
        from azure.mgmt.rdbms import mariadb
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                public_network_access=public_network_access,
                storage_profile=mariadb.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb,
                    storage_autogrow=auto_grow)),
            location=location,
            tags=tags)

    return client.create(resource_group_name, server_name, parameters)


# Need to replace source server name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# arguments and validators
def _server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, no_wait=False):
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


# need to replace source server name with source server id, so customer server georestore function
# The parameter list should be the same as that in factory to use the ParametersContext
# auguments and validators
def _server_georestore(cmd, client, resource_group_name, server_name, sku_name, location, source_server,
                       backup_retention=None, geo_redundant_backup=None, no_wait=False, **kwargs):
    provider = 'Microsoft.DBforPostgreSQL'
    if isinstance(client, MySqlServersOperations):
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        provider = 'Microsoft.DBforMariaDB'

    parameters = None

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                        resource_group=resource_group_name,
                                        namespace=provider,
                                        type='servers',
                                        name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))

    if provider == 'Microsoft.DBforMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForGeoRestore(
                storage_profile=mysql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup),
                source_server_id=source_server),
            location=location)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            sku=postgresql.models.Sku(name=sku_name),
            properties=postgresql.models.ServerPropertiesForGeoRestore(
                storage_profile=postgresql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup),
                source_server_id=source_server),
            location=location)
    elif provider == 'Microsoft.DBforMariaDB':
        from azure.mgmt.rdbms import mariadb
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForGeoRestore(
                storage_profile=mariadb.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup),
                source_server_id=source_server),
            location=location)

    parameters.properties.source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
        if parameters.sku.name is None:
            parameters.sku.name = source_server_object.sku.name
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))

    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)


# Custom functions for server replica, will add PostgreSQL part after backend ready in future
def _replica_create(cmd, client, resource_group_name, server_name, source_server, no_wait=False, location=None, sku_name=None, **kwargs):
    provider = 'Microsoft.DBforPostgreSQL'
    if isinstance(client, MySqlServersOperations):
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        provider = 'Microsoft.DBforMariaDB'
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

    parameters = None
    if provider == 'Microsoft.DBforMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForReplica(source_server_id=source_server),
            location=location)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerForCreate(
            sku=postgresql.models.Sku(name=sku_name),
            properties=postgresql.models.ServerPropertiesForReplica(source_server_id=source_server),
            location=location)
    elif provider == 'Microsoft.DBforMariaDB':
        from azure.mgmt.rdbms import mariadb
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForReplica(source_server_id=source_server),
            location=location)

    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)


def _replica_stop(client, resource_group_name, server_name):
    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise CLIError('Unable to get server: {}.'.format(str(e)))

    if server_object.replication_role.lower() != "replica":
        raise CLIError('Server {} is not a replica server.'.format(server_name))

    from importlib import import_module
    server_module_path = server_object.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerUpdateParameters = getattr(module, 'ServerUpdateParameters')

    params = ServerUpdateParameters(replication_role='None')

    return client.update(resource_group_name, server_name, params)


def _server_update_custom_func(instance,
                               sku_name=None,
                               storage_mb=None,
                               backup_retention=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               tags=None,
                               auto_grow=None,
                               assign_identity=False,
                               public_network_access=None):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerUpdateParameters = getattr(module, 'ServerUpdateParameters')

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

    params = ServerUpdateParameters(sku=instance.sku,
                                    storage_profile=instance.storage_profile,
                                    administrator_login_password=administrator_login_password,
                                    version=None,
                                    ssl_enforcement=ssl_enforcement,
                                    tags=tags,
                                    public_network_access=public_network_access)

    if assign_identity:
        if server_module_path.find('postgres'):
            from azure.mgmt.rdbms import postgresql
            if instance.identity is None:
                instance.identity = postgresql.models.ResourceIdentity(type=postgresql.models.IdentityType.system_assigned.value)
            params.identity = instance.identity
        elif server_module_path.find('mysql'):
            from azure.mgmt.rdbms import mysql
            if instance.identity is None:
                instance.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
            params.identity = instance.identity

    return params


def _server_mariadb_get(cmd, resource_group_name, server_name):
    client = get_mariadb_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


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


def _custom_vnet_update_get(client, resource_group_name, server_name, virtual_network_rule_name):
    return client.get(resource_group_name, server_name, virtual_network_rule_name)


def _custom_vnet_update_set(client, resource_group_name, server_name, virtual_network_rule_name,
                            virtual_network_subnet_id,
                            ignore_missing_vnet_service_endpoint=None):
    return client.create_or_update(resource_group_name, server_name,
                                   virtual_network_rule_name, virtual_network_subnet_id,
                                   ignore_missing_vnet_service_endpoint)


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


# region private_endpoint
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, server_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):  # pylint: disable=unused-argument
    private_endpoint_connection = client.get(resource_group_name=resource_group_name, server_name=server_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = 'Approved' if is_approved else 'Rejected'
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description

    return client.create_or_update(resource_group_name=resource_group_name,
                                   server_name=server_name,
                                   private_endpoint_connection_name=private_endpoint_connection_name,
                                   private_link_service_connection_state=private_endpoint_connection.private_link_service_connection_state)


def approve_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                        description=None):
    """Approve a private endpoint connection request for a server."""

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=True,
        description=description)


def reject_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                       description=None):
    """Reject a private endpoint connection request for a server."""

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=False,
        description=description)


def server_key_create(client, resource_group_name, server_name, kid):

    """Create Server Key."""

    key_name = _get_server_key_name_from_uri(kid)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name,
        uri=kid
    )


def server_key_get(client, resource_group_name, server_name, kid):

    """Get Server Key."""

    key_name = _get_server_key_name_from_uri(kid)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def server_key_delete(cmd, client, resource_group_name, server_name, kid):

    """Drop Server Key."""
    key_name = _get_server_key_name_from_uri(kid)

    return client.delete(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def _get_server_key_name_from_uri(uri):
    '''
    Gets the key's name to use as a server key.

    The SQL server key API requires that the server key has a specific name
    based on the vault, key and key version.
    '''
    import re

    match = re.match(r'^https(.)+\.vault(.)+\/keys\/[^\/]+\/[0-9a-zA-Z]+$', uri)

    if match is None:
        raise CLIError('The provided uri is invalid. Please provide a valid Azure Key Vault key id.  For example: '
                       '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

    vault = uri.split('.')[0].split('/')[-1]
    key = uri.split('/')[-2]
    version = uri.split('/')[-1]
    return '{}_{}_{}'.format(vault, key, version)


def server_ad_admin_set(client, resource_group_name, server_name, login=None, sid=None):
    '''
    Sets a server's AD admin.
    '''

    if isinstance(client, MySqlServersOperations):
        from azure.mgmt.rdbms import mysql
        parameters = mysql.models.ServerAdministratorResource(
            login=login,
            sid=sid,
            tenant_id=_get_tenant_id())
    else:
        from azure.mgmt.rdbms import postgresql
        parameters = postgresql.models.ServerAdministratorResource(
            login=login,
            sid=sid,
            tenant_id=_get_tenant_id())

    return client.create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        properties=parameters)


def _get_tenant_id():
    '''
    Gets tenantId from current subscription.
    '''
    from azure.cli.core._profile import Profile

    profile = Profile()
    sub = profile.get_subscription()
    return sub['tenantId']
# endregion
