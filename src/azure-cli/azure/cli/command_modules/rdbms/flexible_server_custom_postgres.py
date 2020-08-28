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
from .flexible_server_custom_common import _server_list_custom_func, _flexible_firewall_rule_update_custom_func # needed for common functions in commands.py
from ._util import generate_missing_parameters, resolve_poller, _create_vnet

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
logger = get_logger(__name__)

# region create without args
def _flexible_server_create(cmd, client, resource_group_name=None, server_name=None, location=None, backup_retention=None,
                                   sku_name=None, geo_redundant_backup=None, storage_mb=None, administrator_login=None,
                                   administrator_login_password=None, version=None, ssl_enforcement=None, database_name=None, tags=None, public_network_access=None, infrastructure_encryption=None,
                                   assign_identity=False):
    from azure.mgmt.rdbms import postgresql
    db_context = DbContext(
        azure_sdk=postgresql, logging_name='PostgreSQL', command_group='postgres', server_client=client)

    try:
        location, resource_group_name, server_name, administrator_login_password = generate_missing_parameters(cmd, location, resource_group_name, server_name, administrator_login_password)
        # The server name already exists in the resource group
        server_result = client.get(resource_group_name, server_name)
        logger.warning('Found existing PostgreSQL Server \'%s\' in group \'%s\'',
                       server_name, resource_group_name)
    except CloudError:
        subnet_id = _create_vnet(cmd, server_name, location, resource_group_name, "Microsoft.DBforPostgreSQL/flexibleServers")
        # Create postgresql server
        server_result = _create_server(
            db_context, cmd, resource_group_name, server_name, location, backup_retention,
            sku_name, geo_redundant_backup, storage_mb, administrator_login, administrator_login_password, version,
            ssl_enforcement, tags, public_network_access, infrastructure_encryption, assign_identity)
    """
    user = '{}@{}'.format(administrator_login, server_name)
    host = server_result.fully_qualified_domain_name
    sku = '{}'.format(sku_name)
    rg = '{}'.format(resource_group_name)
    loc = '{}'.format(location)
    """

    rg = '{}'.format(resource_group_name)
    user = server_result.administrator_login
    id = server_result.id
    loc = server_result.location
    host = server_result.fully_qualified_domain_name
    version = server_result.version
    sku = server_result.sku.name

    logger.warning('Make a note of your password. If you forget, you would have to'
                   ' reset your password with CLI command for reset password')

    _update_local_contexts(cmd, server_name, resource_group_name, location)

    return _form_response(
        user, sku, loc, rg, id, host, version,
        administrator_login_password if administrator_login_password is not None else '*****',
        _create_postgresql_connection_string(host, administrator_login_password)
    )


"""
def _flexible_server_create(cmd, client, resource_group_name, server_name, sku_name, tier,
                   location=None, storage_mb=None, administrator_login=None, administrator_login_password=None, version=None,
                   backup_retention=None, tags=None, public_network_access=None, vnet_name=None, vnet_address_prefix=None,
                   subnet_name=None, subnet_address_prefix=None, public_access=None, high_availability=None, zone=None,
                   maintenance_window=None, assign_identity=False):
    from azure.mgmt.rdbms import postgresql

    parameters = postgresql.flexibleservers.models.Server(
        sku=postgresql.flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=postgresql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            # geo_redundant_backup=geo_redundant_backup, # to be enabled after private preview
            storage_mb=storage_mb),  ##!!! required I think otherwise data is null error seen in backend exceptions
        location=location,
        create_mode="Default",
        vnet_inj_args = postgresql.flexibleservers.models.ServerPropertiesVnetInjArgs(
            delegated_vnet_id=None,  # what should this value be?
            delegated_subnet_name=subnet_name,
            delegated_vnet_name=vnet_name,
            delegated_vnet_resource_group=None  # what should this value be?
        ),
        tags=tags)

    if assign_identity:
        parameters.identity = postgresql.models.flexibleservers.Identity(type=postgresql.models.flexibleservers.ResourceIdentityType.system_assigned.value)
    return client.create(resource_group_name, server_name, parameters)
"""
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

# 8/25: may need to update the update function per updates to swagger spec
def _flexible_server_update_custom_func(instance,
                               sku_name=None,
                               v_cores=None,
                               server_edition=None,
                               storage_mb=None,
                               backup_retention=None,
                               administrator_login_password=None,
                               auto_grow=None,
                               assign_identity=False):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path)
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



def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name,
                   geo_redundant_backup, storage_mb, administrator_login, administrator_login_password, version,
                   ssl_enforcement, tags, public_network_access, infrastructure_encryption, assign_identity):
    logging_name, azure_sdk, server_client = db_context.logging_name, db_context.azure_sdk, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Make a note of your password. If you forget, you would have to'
                   ' reset your password with CLI command for reset password')

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/postgres-pricing for pricing details', server_name, sku_name)

    from azure.mgmt.rdbms import postgresql

    # MOLJAIN TO DO: The SKU should not be hardcoded, need a fix with new swagger or need to manually parse sku provided
    parameters = postgresql.flexibleservers.models.Server(
        sku=postgresql.flexibleservers.models.Sku(name=sku_name, tier="GeneralPurpose", capacity=4),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        ssl_enforcement=ssl_enforcement,
        public_network_access=public_network_access,
        infrastructure_encryption=infrastructure_encryption,
        storage_profile=postgresql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            geo_redundant_backup=geo_redundant_backup,
            storage_mb=storage_mb),  ##!!! required I think otherwise data is null error seen in backend exceptions
        # storage_autogrow=auto_grow),
        location=location,
        create_mode="Default",  # can also be create
        tags=tags)

    if assign_identity:
        parameters.identity = postgresql.models.ResourceIdentity(
            type=postgresql.models.IdentityType.system_assigned.value)

    return resolve_poller(
        server_client.create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def _create_postgresql_connection_string(host, password):
    connection_kwargs = {
        'host': host,
        'password': password if password is not None else '{password}'
    }
    return 'postgres://postgres:{password}@{host}/postgres?sslmode=require'.format(**connection_kwargs)


def _form_response(username, sku, location, resource_group_name, id, host, version, password, connection_string):
    return {
        'host': host,
        'username': username,
        'password': password,
        'skuname': sku,
        'location': location,
        'resource group': resource_group_name,
        'id': id,
        'version': version,
        'connection string': connection_string
    }


def _update_local_contexts(cmd, server_name, resource_group_name, location):
    cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'server-name',
                                  server_name)  # Setting the server name in the local context
    cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'location',
                                  location)  # Setting the location in the local context
    cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'resource_group_name', resource_group_name)





# pylint: disable=too-many-instance-attributes,too-few-public-methods
class DbContext:
    def __init__(self, azure_sdk=None, logging_name=None,
                 command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client
