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
from .flexible_server_custom_common import user_confirmation, _server_list_custom_func
from ._flexible_server_util import generate_missing_parameters, resolve_poller, create_vnet, create_firewall_rule, \
    parse_public_access_input, update_kwargs, generate_password, parse_maintenance_window

logger = get_logger(__name__)


# region create without args
def _flexible_server_create(cmd, client,
                            resource_group_name=None, server_name=None,
                            location=None, backup_retention=None,
                            sku_name=None, tier=None,
                            storage_mb=None, administrator_login=None,
                            administrator_login_password=None, version=None,
                            tags=None, public_access=None,
                            assign_identity=False, subnet_arm_resource_id=None,
                            high_availability=None, zone=None):
    from azure.mgmt.rdbms import postgresql
    try:
        db_context = DbContext(
            azure_sdk=postgresql, cf_firewall=cf_postgres_flexible_firewall_rules, logging_name='PostgreSQL', command_group='postgres', server_client=client)

        # Raise error when user passes values for both parameters
        if subnet_arm_resource_id is not None and public_access is not None:
            raise CLIError("Incorrect usage : A combination of the parameters --subnet "
                           "and --public_access is invalid. Use either one of them.")

        server_result = firewall_id = subnet_id = None

        # Populate desired parameters
        location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name, server_name)

        # Get list of servers in the current sub
        server_list = _server_list_custom_func(client)

        # Ensure that the server name is not in the rg and in the subscription
        for key in server_list:
            if server_name == key.name and key.id.find(resource_group_name) != -1:
                logger.warning('Found existing PostgreSQL Server \'%s\' in group \'%s\'',
                               server_name, resource_group_name)
                server_result = client.get(resource_group_name, server_name)
            elif server_name == key.name:
                raise CLIError("The server name '{}' exists in this subscription.Please re-run command with a "
                                   "valid server name.".format(server_name))

        administrator_login_password = generate_password(administrator_login_password)
        if server_result is None:
            # If subnet is provided, use that subnet to create the server, else create subnet if public access is not enabled.
            if subnet_arm_resource_id is not None:
                subnet_id = subnet_arm_resource_id  # set the subnet id to be the one passed in
                delegated_subnet_arguments = postgresql.flexibleservers.models.ServerPropertiesDelegatedSubnetArguments(
            subnet_arm_resource_id=subnet_id)
            elif public_access is None and subnet_arm_resource_id is None:
                subnet_id = create_vnet(cmd, server_name, location, resource_group_name,
                                        "Microsoft.DBforPostgreSQL/flexibleServers")
                delegated_subnet_arguments = postgresql.flexibleservers.models.ServerPropertiesDelegatedSubnetArguments(
            subnet_arm_resource_id=subnet_id)
            else:
                delegated_subnet_arguments = None
            # Create postgresql
            # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
            server_result = _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention,
                                           sku_name, tier, storage_mb, administrator_login, administrator_login_password,
                                           version, tags, subnet_id, assign_identity,delegated_subnet_arguments,
                                           high_availability, zone)

            # Adding firewall rule
            if public_access is not None and str(public_access).lower() != 'none':
                if str(public_access).lower() == 'all':
                    start_ip, end_ip = '0.0.0.0', '255.255.255.255'
                else:
                    start_ip, end_ip = parse_public_access_input(public_access)
                firewall_id = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

        user = server_result.administrator_login
        id = server_result.id
        loc = server_result.location
        version = server_result.version
        sku = server_result.sku.name
        host = server_result.fully_qualified_domain_name

        logger.warning('Make a note of your password. If you forget, you would have to' \
                       ' reset your password with \'az postgres flexible-server update -n %s -g %s -p <new-password>\'.',
                       server_name, resource_group_name)

        _update_local_contexts(cmd, server_name, resource_group_name, location, user)

        return _form_response(user, sku, loc, id, host, version, administrator_login_password if administrator_login_password is not None else '*****',
                              _create_postgresql_connection_string(host, administrator_login_password), firewall_id, subnet_id)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)


def _flexible_server_restore(cmd, client,
                             resource_group_name, server_name,
                             source_server, restore_point_in_time,
                             location=None, no_wait=False):
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


# Update Flexible server command
def _flexible_server_update_custom_func(instance,
                                sku_name=None,
                                tier=None,
                                storage_mb=None,
                                backup_retention=None,
                                administrator_login_password=None,
                                ha_enabled=None,
                                maintenance_window=None,
                                assign_identity=False,
                                tags=None):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path)
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name
        instance.sku.tier = tier
    else:
        instance.sku = None

    if storage_mb:
        instance.storage_profile.storage_mb = storage_mb

    if backup_retention:
        instance.storage_profile.backup_retention_days = backup_retention

    if maintenance_window:
        day_of_week, start_hour, start_minute = parse_maintenance_window(maintenance_window)
        instance.maintenance_window.day_of_week = day_of_week
        instance.maintenance_window.start_hour = start_hour
        instance.maintenance_window.start_minute = start_minute
        instance.maintenance_window.custom_window = "Enabled"

    params = ServerForUpdate(sku=instance.sku,
                             storage_profile=instance.storage_profile,
                             administrator_login_password=administrator_login_password,
                             ha_enabled=ha_enabled,
                             maintenance_window=instance.maintenance_window,
                             tags=tags)

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
                local_context_file.remove_option('postgres flexible-server', 'administrator_login')
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
        return result

# Wait command
def _flexible_server_postgresql_get(cmd, resource_group_name, server_name):
    client = get_postgresql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
    if source is None and value is None:
        # update the command with system default
        try:
            parameter = client.get(resource_group_name, server_name, configuration_name)
            value = parameter.default_value # reset value to default

            # this should be 'system-default' but there is currently a bug in PG, so keeping as what it is for now
            # this will reset source to be 'system-default' anyway
            source = parameter.source
        except CloudError as e:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
    elif source is None:
        source = "user-override"

    return client.update(resource_group_name, server_name, configuration_name, value, source)


def _flexible_list_skus(client, location):
    return client.execute(location)


def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name, tier,
                   storage_mb, administrator_login, administrator_login_password, version, tags, public_network_access,
                   assign_identity, delegated_subnet_arguments, ha_enabled, availability_zone):
    logging_name, azure_sdk, server_client = db_context.logging_name, db_context.azure_sdk, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/postgres-pricing for pricing details', server_name, sku_name)

    from azure.mgmt.rdbms import postgresql

    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.
    parameters = postgresql.flexibleservers.models.Server(
        sku=postgresql.flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=postgresql.flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            storage_mb=storage_mb),
        delegated_subnet_arguments=delegated_subnet_arguments,
        ha_enabled=ha_enabled,
        availability_zone=availability_zone,
        location=location,
        create_mode="Default",  # can also be create
        tags=tags)

    if assign_identity:
        parameters.identity = postgresql.models.ResourceIdentity(
            type=postgresql.models.IdentityType.system_assigned.value)

    return resolve_poller(
        server_client.create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def flexible_server_connection_string(
        server_name='{server}', database_name='{database}', administrator_login='{login}',
        administrator_login_password='{password}'):
    host = '{}.postgres.database.azure.com'.format(server_name)
    return {
        'connectionStrings': _create_postgresql_connection_strings(host, administrator_login, administrator_login_password, database_name)
    }


def _create_postgresql_connection_strings(host, user, password, database):
    result = {
        'psql_cmd': "psql --host={host} --port=5432 --username={user} --dbname={database}",
        'ado.net': "Server={host};Database={database};Port=5432;User Id={user};Password={password};",
        'jdbc': "jdbc:postgresql://{host}:5432/{database}?user={user}&password={password}",
        'jdbc Spring': "spring.datasource.url=jdbc:postgresql://{host}:5432/{database}  "
                       "spring.datasource.username={user}  "
                       "spring.datasource.password={password}",
        'node.js': "var client = new pg.Client('postgres://{user}:{password}@{host}:5432/{database}');",
        'php': "host={host} port=5432 dbname={database} user={user} password={password}",
        'python': "cnx = psycopg2.connect(database='{database}', user='{user}', host='{host}', password='{password}', "
                  "port='5432')",
        'ruby': "cnx = PG::Connection.new(:host => '{host}', :user => '{user}', :dbname => '{database}', "
                ":port => '5432', :password => '{password}')",
    }

    connection_kwargs = {
        'host': host,
        'user': user,
        'password': password if password is not None else '{password}',
        'database': database
    }

    for k, v in result.items():
        result[k] = v.format(**connection_kwargs)
    return result


def _create_postgresql_connection_string(host, password):
    connection_kwargs = {
        'host': host,
        'password': password if password is not None else '{password}'
    }
    return 'postgres://postgres:{password}@{host}/postgres?sslmode=require'.format(**connection_kwargs)


def _form_response(username, sku, location, id, host, version, password, connection_string, firewall_id=None, subnet_id=None):
    '''
    from collections import OrderedDict
    new_entry = OrderedDict()
    new_entry['Id'] = id
    if subnet_id is not None:
        new_entry['SubnetId'] = subnet_id
    new_entry['Location'] = location
    new_entry['SkuName'] = sku
    new_entry['Version'] = version
    new_entry['Host'] = host
    new_entry['UserName'] = username
    new_entry['Password'] = password
    new_entry['ConnectionString'] = connection_string
    if firewall_id is not None:
        new_entry['FirewallName'] = firewall_id
    '''
    output = {
        'host': host,
        'username': username,
        'password': password,
        'skuname': sku,
        'location': location,
        'id': id,
        'version': version,
        'connectionString': connection_string
    }
    if firewall_id is not None:
        output['firewallName'] = firewall_id
    if subnet_id is not None:
        output['subnetId'] = subnet_id
    return output


def _update_local_contexts(cmd, server_name, resource_group_name, location, user):
    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'server_name',
                                    server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'administrator_login',
                                    user)  # Setting the server name in the local context
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
