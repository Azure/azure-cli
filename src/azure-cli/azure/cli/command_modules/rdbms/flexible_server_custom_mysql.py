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
from azure.cli.core._profile import Profile
from azure.mgmt.rdbms.mysql.operations._servers_operations import ServersOperations as MySqlServersOperations
from azure.mgmt.rdbms.mysql.flexibleservers.operations._servers_operations import ServersOperations as MySqlFlexibleServersOperations
from ._client_factory import get_mysql_flexible_management_client, cf_mysql_flexible_firewall_rules
from .flexible_server_custom_common import _server_list_custom_func, _flexible_firewall_rule_update_custom_func # needed for common functions in commands.py

from ._util import resolve_poller, generate_missing_parameters, create_vnet, create_firewall_rule, parse_public_access_input

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
logger = get_logger(__name__)

"""
def _flexible_server_create(cmd, client, resource_group_name, server_name, sku_name, tier,
                                location=None, storage_mb=None, administrator_login=None,
                                administrator_login_password=None, version=None,
                                backup_retention=None, tags=None, public_network_access=None, vnet_name=None,
                                vnet_address_prefix=None, subnet_name=None, subnet_address_prefix=None, public_access=None,
                                high_availability=None, zone=None, maintenance_window=None, assign_identity=False):
    from azure.mgmt.rdbms import mysql

    parameters = mysql.flexibleservers.models.Server(
        sku=mysql.flexibleservers.models.Sku(name=sku_name, tier = tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=mysql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            # geo_redundant_backup=geo_redundant_backup,
            storage_mb=storage_mb),  ##!!! required I think otherwise data is null error seen in backend exceptions
        # storage_autogrow=auto_grow),
        location=location,
        create_mode="Default",
        vnet_inj_args=mysql.flexibleservers.models.VnetInjArgs(
            delegated_vnet_id=None,  # what should this value be?
            delegated_subnet_name=subnet_name,
            delegated_vnet_name=vnet_name,
            # delegated_vnet_resource_group=None  # not in mysql
        ),
        tags=tags)

    if assign_identity:
        parameters.identity = mysql.models.flexibleservers.Identity(type=mysql.models.flexibleservers.ResourceIdentityType.system_assigned.value)
    return client.create(resource_group_name, server_name, parameters)
"""

# region create without args
def _flexible_server_create(cmd, client, resource_group_name=None, server_name=None, sku_name=None, tier=None,
                                location=None, storage_mb=None, administrator_login=None,
                                administrator_login_password=None, version=None,
                                backup_retention=None, tags=None, public_access=None, vnet_name=None,
                                vnet_address_prefix=None, subnet_name=None, subnet_address_prefix=None, public_network_access=None,
                                high_availability=None, zone=None, maintenance_window=None, assign_identity=False):
    from azure.mgmt.rdbms import mysql
    db_context = DbContext(
        azure_sdk=mysql, cf_firewall=cf_mysql_flexible_firewall_rules, logging_name='MySQL', command_group='mysql', server_client=client)

    try:
        location, resource_group_name, server_name, administrator_login_password = generate_missing_parameters(cmd, location, resource_group_name, server_name, administrator_login_password)
        # The server name already exists in the resource group
        server_result = client.get(resource_group_name, server_name)
        logger.warning('Found existing MySQL Server \'%s\' in group \'%s\'',
                       server_name, resource_group_name)
    except CloudError:
        if public_access is None:
            subnet_id = create_vnet(cmd, server_name, location, resource_group_name, "Microsoft.MySQL/flexibleServers")

        # Create mysql server
        server_result = _create_server(
            db_context, cmd, resource_group_name, server_name, location, backup_retention,
            sku_name, storage_mb, administrator_login, administrator_login_password, version,
            tags, public_network_access, assign_identity, tier, subnet_name, vnet_name)

        if public_access is not None:
            start_ip, end_ip = parse_public_access_input(public_access)
            create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

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

    return _form_response(user, sku, loc, rg, id, host,version,
        administrator_login_password if administrator_login_password is not None else '*****',
        ''
    )


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
                type='flexibleServers',
                name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))

    from azure.mgmt.rdbms import mysql
    parameters = mysql.flexibleservers.models.Server(
        source_server_id=source_server,
        restore_point_in_time=restore_point_in_time,
        location=location,
        create_mode="PointInTimeRestore"
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

# 8/25: may need to update the update function per updates to swagger spec
def _flexible_server_update_custom_func(instance,
                               sku_name=None,
                               storage_mb=None,
                               backup_retention=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               vnet_name=None,
                               subnet_name=None,
                               tags=None,
                               auto_grow=None,
                               assign_identity=False,
                               public_network_access=None,
                               replication_role=None):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path) # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name
        instance.sku.tier = None
    else:
        instance.sku = None

    if storage_mb:
        instance.storage_profile.storage_mb = storage_mb

    if backup_retention:
        instance.storage_profile.backup_retention_days = backup_retention

    if auto_grow:
        instance.storage_profile.storage_autogrow = auto_grow

    if subnet_name:
        instance.vnet_inj_args.delegated_subnet_name = subnet_name

    if vnet_name:
        instance.vnet_inj_args.delegated_vnet_name = vnet_name

    params = ServerForUpdate(sku=instance.sku,
                                    storage_profile=instance.storage_profile,
                                    administrator_login_password=administrator_login_password,
                                    ssl_enforcement=ssl_enforcement,
                                    vnet_inj_args=instance.vnet_inj_args,
                                    tags=tags,
                                    replication_role=replication_role,
                                    public_network_access=public_network_access)

    if assign_identity:
        if server_module_path.find('mysql'):
            from azure.mgmt.rdbms import mysql
            if instance.identity is None:
                instance.identity = mysql.models.flexibleservers.Identity(
                    type=mysql.models.flexibleservers.ResourceIdentityType.system_assigned.value)
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

def _flexible_server_mysql_get(cmd, resource_group_name, server_name):
    client = get_mysql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name,
                   storage_mb, administrator_login, administrator_login_password, version,
                   tags, public_network_access, assign_identity, tier, subnet_name, vnet_name):

    logging_name, azure_sdk, server_client = db_context.logging_name, db_context.azure_sdk, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/mysql-pricing for pricing details', server_name, sku_name)

    from azure.mgmt.rdbms import mysql

    parameters = mysql.flexibleservers.models.Server(
        sku=mysql.flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=mysql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            storage_mb=storage_mb),
        location=location,
        create_mode="Default",
        vnet_inj_args=mysql.flexibleservers.models.VirtualNetworkRule(
            virtual_network_subnet_id=None, #TODO virtual_network_subnet_id,
            ignore_missing_vnet_service_endpoint=None # TODO False default?
        ),
        tags=tags)

    if assign_identity:
        parameters.identity = mysql.models.flexibleservers.Identity(
            type=mysql.models.flexibleservers.ResourceIdentityType.system_assigned.value)
    # return client.create(resource_group_name, server_name, parameters)

    return resolve_poller(
        server_client.create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


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
    cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'server-name',
                                  server_name)  # Setting the server name in the local context
    cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'location',
                                  location)  # Setting the location in the local context
    cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'resource_group_name', resource_group_name)



# pylint: disable=too-many-instance-attributes,too-few-public-methods
class DbContext:
    def __init__(self, azure_sdk=None, logging_name=None, cf_firewall=None,
                 command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client