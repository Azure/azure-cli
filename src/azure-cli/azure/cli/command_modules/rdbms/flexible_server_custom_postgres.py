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
from azure.cli.core.local_context import ALL
from azure.cli.core.util import CLIError, sdk_no_wait
from ._client_factory import cf_postgres_flexible_firewall_rules, get_postgresql_flexible_management_client
from .flexible_server_custom_common import user_confirmation
from ._flexible_server_util import generate_missing_parameters, resolve_poller, create_vnet, create_firewall_rule, parse_public_access_input, update_kwargs, generate_password

logger = get_logger(__name__)


# region create without args
def _flexible_server_create(cmd, client, resource_group_name=None, server_name=None, location=None, backup_retention=None,
                                   sku_name=None, tier=None, storage_mb=None, administrator_login=None,
                                   administrator_login_password=None, version=None, tags=None, public_access=None,
                                   assign_identity=False):
    from azure.mgmt.rdbms import postgresql
    db_context = DbContext(
        azure_sdk=postgresql, cf_firewall=cf_postgres_flexible_firewall_rules, logging_name='PostgreSQL', command_group='postgres', server_client=client)

    firewall_id = subnet_id = None
    try:
        location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name, server_name)
        # The server name already exists in the resource group
        server_result = client.get(resource_group_name, server_name)
        logger.warning('Found existing PostgreSQL Server \'%s\' in group \'%s\'',
                       server_name, resource_group_name)

        # update server if needed
        server_result = _update_server(
            db_context, cmd, client, server_result, resource_group_name, server_name, backup_retention,
            storage_mb, administrator_login_password)
    except CloudError:
        administrator_login_password = generate_password(administrator_login_password)
        if public_access is None:
            subnet_id = create_vnet(cmd, server_name, location, resource_group_name, "Microsoft.DBforPostgreSQL/flexibleServers")

        # Create postgresql
        server_result = _create_server(
            db_context, cmd, resource_group_name, server_name, location, backup_retention,
            sku_name, tier, storage_mb, administrator_login, administrator_login_password, version,
            tags, public_access, assign_identity)

        if public_access is not None:
            if public_access == 'on':
                start_ip, end_ip = '0.0.0.0', '255.255.255.255'
            else:
                start_ip, end_ip = parse_public_access_input(public_access)
            firewall_id = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

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
        user, sku, loc, id, host, version,
        administrator_login_password if administrator_login_password is not None else '*****',
        _create_postgresql_connection_string(host, administrator_login_password), firewall_id, subnet_id
    )


def _flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, location=None, no_wait=False):
    provider = 'Microsoft.DBforPostgreSQL'
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

    from azure.mgmt.rdbms import postgresql
    parameters = postgresql.flexibleservers.models.Server(
        point_in_time_utc=restore_point_in_time,
        source_server_name=source_server,
        create_mode="PointInTimeRestore",
        location=location)

    # Retrieve location from same location as source server
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
                               standby_count=None,
                               assign_identity=False):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path)
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

    ## TODO: add ha_enabled, maintence window
    params = ServerForUpdate(sku=instance.sku,
                             storage_profile=instance.storage_profile,
                             administrator_login_password=administrator_login_password,
                             standby_count=standby_count)

    if assign_identity:
        if server_module_path.find('postgres'):
            from azure.mgmt.rdbms import postgresql
            if instance.identity is None:
                instance.identity = postgresql.models.ResourceIdentity(
                    type=postgresql.models.IdentityType.system_assigned.value)
                instance.identity = postgresql.models.flexibleservers.Identity(
                    type=postgresql.models.flexibleservers.ResourceIdentityType.system_assigned.value)
            params.identity = instance.identity
    return params

def _server_delete_func(cmd, client, resource_group_name=None, server_name=None, force=None):
    confirm = force
    if not force:
        confirm = user_confirmation("Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name, resource_group_name), yes=force)
    if (confirm):
        try:
            result = client.delete(resource_group_name, server_name)
            if cmd.cli_ctx.local_context.is_on:
                local_context_file = cmd.cli_ctx.local_context._get_local_context_file()
                local_context_file.remove_option('postgres flexible-server', 'server_name')
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
        return result


# Wait command
def _flexible_server_postgresql_get(cmd, resource_group_name, server_name):
    client = get_postgresql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _flexible_parameter_update(client, ids, server_name, configuration_name, resource_group_name, source=None, value=None):
    if source is None and value is None:
        # update the command with system default
        try:
            parameter = client.get(resource_group_name, server_name, configuration_name)
            value = parameter.default_value # reset value to default
            source = "system-default"
        except CloudError as e:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
    elif source is None:
        source = "user-override"

    return client.update(resource_group_name, server_name, configuration_name, value, source)


def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name, tier,
                   storage_mb, administrator_login, administrator_login_password, version,
                   tags, public_network_access, assign_identity):
    logging_name, azure_sdk, server_client = db_context.logging_name, db_context.azure_sdk, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/postgres-pricing for pricing details', server_name, sku_name)

    from azure.mgmt.rdbms import postgresql

    parameters = postgresql.flexibleservers.models.Server(
        sku=postgresql.flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=postgresql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            storage_mb=storage_mb),  ##[TODO : required I think otherwise data is null error seen in backend exceptions
        delegated_subnet_arguments=postgresql.flexibleservers.models.ServerPropertiesDelegatedSubnetArguments(
            subnet_arm_resource_id=None
        ),
        location=location,
        create_mode="Default",  # can also be create
        tags=tags)

    if assign_identity:
        parameters.identity = postgresql.models.ResourceIdentity(
            type=postgresql.models.IdentityType.system_assigned.value)

    return resolve_poller(
        server_client.create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def _update_server(db_context, cmd, client, server_result, resource_group_name, server_name, backup_retention,
                   storage_mb, administrator_login_password):
    # storage profile params
    storage_profile_kwargs = {}
    db_sdk, logging_name = db_context.azure_sdk, db_context.logging_name
    if backup_retention is not None and backup_retention != server_result.storage_profile.backup_retention_days:
        update_kwargs(storage_profile_kwargs, 'backup_retention_days', backup_retention)
    if storage_mb != server_result.storage_profile.storage_mb:
        update_kwargs(storage_profile_kwargs, 'storage_mb', storage_mb)

    # update params
    server_update_kwargs = {
        'storage_profile': db_sdk.models.StorageProfile(**storage_profile_kwargs)
    } if storage_profile_kwargs else {}
    update_kwargs(server_update_kwargs, 'administrator_login_password', administrator_login_password)

    if server_update_kwargs:
        logger.warning('Updating existing %s Server \'%s\' with given arguments', logging_name, server_name)
        params = db_sdk.models.ServerUpdateParameters(**server_update_kwargs)
        return resolve_poller(client.update(
            resource_group_name, server_name, params), cmd.cli_ctx, '{} Server Update'.format(logging_name))
    return server_result


def _create_postgresql_connection_string(host, password):
    connection_kwargs = {
        'host': host,
        'password': password if password is not None else '{password}'
    }
    return 'postgres://postgres:{password}@{host}/postgres?sslmode=require'.format(**connection_kwargs)


def _form_response(username, sku, location, id, host, version, password, connection_string, firewall_id=None, subnet_id=None):
    output = {
        'host': host,
        'username': username,
        'password': password,
        'skuname': sku,
        'location': location,
        'id': id,
        'version': version,
        'connection string': connection_string
    }
    if firewall_id is not None:
        output['firewall id'] = firewall_id
    if subnet_id is not None:
        output['subnet id'] = subnet_id
    return output


def _update_local_contexts(cmd, server_name, resource_group_name, location):
    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'server_name',
                                    server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([ALL], 'location',
                                    location)  # Setting the location in the local context
        cmd.cli_ctx.local_context.set([ALL], 'resource_group_name', resource_group_name)


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class DbContext:
    def __init__(self, azure_sdk=None, logging_name=None, cf_firewall=None,
                 command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client
