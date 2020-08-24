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
from ._client_factory import get_postgresql_flexible_management_client

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
logger = get_logger(__name__)


def _flexible_server_create(cmd, client, resource_group_name, server_name, sku_name, tier,
                   location=None, no_wait=False, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None, infrastructure_encryption=None, minimal_tls_version=None):
    from azure.mgmt.rdbms import postgresql

    parameters = postgresql.flexibleservers.models.Server(
        sku=postgresql.flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        ssl_enforcement=ssl_enforcement,
        public_network_access=public_network_access,
        infrastructure_encryption=infrastructure_encryption,
        storage_profile=postgresql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            # geo_redundant_backup=geo_redundant_backup,
            storage_mb=storage_mb),  ##!!! required I think otherwise data is null error seen in backend exceptions
        # storage_autogrow=auto_grow),
        location=location,
        create_mode="Default",  # can also be create
        tags=tags)

    if assign_identity:
        parameters.identity = postgresql.models.ResourceIdentity(type=postgresql.models.IdentityType.system_assigned.value)
    return client.create(resource_group_name, server_name, parameters)

# Need to replace source server name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# arguments and validators
def _flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, location=None, no_wait=False):
    provider = 'Microsoft.DBforPostgreSQL'
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

    from azure.mgmt.rdbms import postgresql
    parameters = postgresql.flexibleservers.models.Server(
        point_in_time_utc=restore_point_in_time,
        source_server_name=source_server,
        location=location)

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
def _flexible_server_update_get(client, resource_group_name, server_name):
    return client.get(resource_group_name, server_name)

def _flexible_server_update_set(client, resource_group_name, server_name, parameters):
    return client.update(resource_group_name, server_name, parameters)

def _flexible_server_update_custom_func(instance,
                               version=None,
                               sku_name=None,
                               v_cores=None,
                               server_edition=None,
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
    module = import_module(server_module_path) # .replace('server', 'server_update_parameters')) not needed for flexservers
    ServerPropertiesForUpdate = getattr(module, 'ServerPropertiesForUpdate')

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

    if server_edition:
        instance.server_edition = server_edition
    else:
        server_edition = "GeneralPurpose" # default if not provided

    params = ServerPropertiesForUpdate(storage_profile=instance.storage_profile,
                                    administrator_login_password=administrator_login_password,
                                    server_edition = server_edition,
                                    v_cores = v_cores)

    if assign_identity:
        if server_module_path.find('postgres'):
            from azure.mgmt.rdbms import postgresql
            if instance.identity is None:
                instance.identity = postgresql.models.ResourceIdentity(type=postgresql.models.IdentityType.system_assigned.value)
            params.identity = instance.identity
    return params

# Wait command
def _flexible_server_postgresql_get(cmd, resource_group_name, server_name):
    client = get_postgresql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)

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
