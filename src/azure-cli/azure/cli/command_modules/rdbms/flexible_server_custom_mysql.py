# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.core.local_context import ALL
from azure.mgmt.rdbms.mysql.flexibleservers.operations._servers_operations import ServersOperations as MySqlFlexibleServersOperations
from ._client_factory import get_mysql_flexible_management_client, cf_mysql_flexible_firewall_rules, cf_mysql_flexible_db
from ._flexible_server_util import resolve_poller, generate_missing_parameters, create_firewall_rule, \
    parse_public_access_input, update_kwargs, generate_password, parse_maintenance_window
from .flexible_server_custom_common import user_confirmation, _server_list_custom_func
from .flexible_server_virtual_network import create_vnet, prepareVnet

logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
DELEGATION_SERVICE_NAME = "Microsoft.DBforMySQL/flexibleServers"


# region create without args
def _flexible_server_create(cmd, client, resource_group_name=None, server_name=None, sku_name=None, tier=None,
                                location=None, storage_mb=None, administrator_login=None,
                                administrator_login_password=None, version=None,
                                backup_retention=None, tags=None, public_access=None, database_name=None,
                                subnet_arm_resource_id=None, high_availability=None, zone=None, assign_identity=False,
                                vnet_resource_id=None, vnet_address_prefix=None, subnet_address_prefix=None):
    from azure.mgmt.rdbms import mysql
    try:
        db_context = DbContext(
            azure_sdk=mysql, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db, logging_name='MySQL', command_group='mysql', server_client=client)

        # Raise error when user passes values for both parameters
        if subnet_arm_resource_id is not None and public_access is not None:
            raise CLIError("Incorrect usage : A combination of the parameters --subnet "
                           "and --public_access is invalid. Use either one of them.")

        # When address space parameters are passed, the only valid combination is : --vnet, --subnet, --vnet-address-prefix, --subnet-address-prefix
        if (vnet_address_prefix is not None) or (subnet_address_prefix is not None):
            if ((vnet_address_prefix is not None) and (subnet_address_prefix is None)) or ((vnet_address_prefix is None) and (subnet_address_prefix is not None)) or ((vnet_address_prefix is not None) and (subnet_address_prefix is not None) and ((vnet_resource_id is None) or (subnet_arm_resource_id is None))):
               raise CLIError("Incorrect usage : "
                              "--vnet, --subnet, --vnet-address-prefix, --subnet-address-prefix must be supplied together.")

        server_result = firewall_id = subnet_id = None

        # Populate desired parameters
        location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name, server_name)

        # Handle Vnet scenario
        if (subnet_arm_resource_id is not None) or (vnet_resource_id is not None):
            subnet_id = prepareVnet(cmd, server_name, vnet_resource_id, subnet_arm_resource_id, resource_group_name,
                                    location, DELEGATION_SERVICE_NAME, vnet_address_prefix, subnet_address_prefix)
            delegated_subnet_arguments = mysql.flexibleservers.models.DelegatedSubnetArguments(
                    subnet_arm_resource_id=subnet_id)
        elif public_access is None and subnet_arm_resource_id is None and vnet_resource_id is None:
            subnet_id = create_vnet(cmd, server_name, location, resource_group_name,
                                    DELEGATION_SERVICE_NAME)
            delegated_subnet_arguments = mysql.flexibleservers.models.DelegatedSubnetArguments(
                    subnet_arm_resource_id=subnet_id)
        else:
            delegated_subnet_arguments = None

        # Get list of servers in the current sub
        server_list = _server_list_custom_func(client)

        # Ensure that the server name is not in the rg and in the subscription
        for key in server_list:
            if server_name == key.name and key.id.find(resource_group_name) != -1:
                logger.warning('Found existing MySQL server \'%s\' in group \'%s\'',
                               server_name, resource_group_name)
                server_result = client.get(resource_group_name, server_name)
            elif server_name == key.name:
                raise CLIError("The server name '{}' exists in this subscription.Please re-run command with a "
                               "valid server name.".format(server_name))

        administrator_login_password = generate_password(administrator_login_password)
        if server_result is None:
            # Create mysql server
            # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
            server_result = _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention,
                                           sku_name, tier, storage_mb, administrator_login, administrator_login_password,
                                           version, tags, delegated_subnet_arguments, assign_identity, public_access,
                                           high_availability, zone)

            # Adding firewall rule
            if public_access is not None and str(public_access).lower() != 'none':
                if str(public_access).lower() == 'all':
                    start_ip, end_ip = '0.0.0.0', '255.255.255.255'
                else:
                    start_ip, end_ip = parse_public_access_input(public_access)
                firewall_id = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

            # Create mysql database if it does not exist
            if database_name is None:
                database_name = DEFAULT_DB_NAME
            _create_database(db_context, cmd, resource_group_name, server_name, database_name)

        user = server_result.administrator_login
        id = server_result.id
        loc = server_result.location
        version = server_result.version
        sku = server_result.sku.name
        host = server_result.fully_qualified_domain_name

        logger.warning('Make a note of your password. If you forget, you would have to' \
                       ' reset your password with \'az mysql flexible-server update -n %s -g %s -p <new-password>\'.',
                       server_name, resource_group_name)

        _update_local_contexts(cmd, server_name, resource_group_name, location, user)

        return _form_response(user, sku, loc, id, host, version,
                              administrator_login_password if administrator_login_password is not None else '*****',
                              _create_mysql_connection_string(host, database_name, user, administrator_login_password),
                              database_name, firewall_id, subnet_id)

    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)


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

    # Retrieve location from same location as source server
    id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        parameters.location = source_server_object.location
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))
    return sdk_no_wait(no_wait, client.create, resource_group_name, server_name, parameters)


def _flexible_server_update_custom_func(instance,
                               sku_name=None,
                               tier=None,
                               storage_mb=None,
                               backup_retention=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               subnet_arm_resource_id=None,
                               tags=None,
                               auto_grow=None,
                               assign_identity=False,
                               public_network_access=None,
                               ha_enabled=None,
                               replication_role=None,
                               maintenance_window=None):
    from importlib import import_module
    server_module_path = instance.__module__
    module = import_module(server_module_path) # replacement not needed for update in flex servers
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

    if auto_grow:
        instance.storage_profile.storage_autogrow = auto_grow

    if subnet_arm_resource_id:
        instance.delegated_subnet_arguments.subnet_arm_resource_id = subnet_arm_resource_id

    if maintenance_window:
        day_of_week, start_hour, start_minute = parse_maintenance_window(maintenance_window)
        instance.maintenance_window.day_of_week = day_of_week
        instance.maintenance_window.start_hour = start_hour
        instance.maintenance_window.start_minute = start_minute
        instance.maintenance_window.custom_window = "Enabled"

    # TODO: standby count = ha_enabled add here
    params = ServerForUpdate(sku=instance.sku,
                                storage_profile=instance.storage_profile,
                                administrator_login_password=administrator_login_password,
                                ssl_enforcement=ssl_enforcement,
                                delegated_subnet_arguments=instance.delegated_subnet_arguments,
                                tags=tags,
                                ha_enabled=ha_enabled,
                                replication_role=replication_role,
                                public_network_access=public_network_access,
                                maintenance_window=instance.maintenance_window)

    if assign_identity:
        if server_module_path.find('mysql'):
            from azure.mgmt.rdbms import mysql
            if instance.identity is None:
                instance.identity = mysql.models.flexibleservers.Identity(
                    type=mysql.models.flexibleservers.ResourceIdentityType.system_assigned.value)
            params.identity = instance.identity

    return params

def _flexible_server_update_password(instance, server_name, administrator_login, administrator_login_password):
    return _flexible_server_update_custom_func(instance,
                                               server_name=server_name,
                                               administrator_login=administrator_login,
                                               administrator_login_password=administrator_login_password)

def _server_delete_func(cmd, client, resource_group_name=None, server_name=None, force=None):
    confirm = force
    if not force:
        confirm = user_confirmation("Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name, resource_group_name), yes=force)
    if (confirm):
        try:
            result = client.delete(resource_group_name, server_name)
            if cmd.cli_ctx.local_context.is_on:
                local_context_file = cmd.cli_ctx.local_context._get_local_context_file()
                local_context_file.remove_option('mysql flexible-server', 'server_name')
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
        return result


## Parameter update command
def _flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
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


def _flexible_list_skus(client, location):
    return client.list(location)


def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name, tier,
                   storage_mb, administrator_login, administrator_login_password, version, tags, delegated_subnet_arguments,
                   assign_identity, public_network_access, ha_enabled, availability_zone):

    logging_name, azure_sdk, server_client = db_context.logging_name, db_context.azure_sdk, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/mysql-pricing for pricing details', server_name, sku_name)

    from azure.mgmt.rdbms import mysql

    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.
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
        delegated_subnet_arguments=delegated_subnet_arguments,
        ha_enabled=ha_enabled,
        availability_zone=availability_zone,
        tags=tags)

    if assign_identity:
        parameters.identity = mysql.models.flexibleservers.Identity(
            type=mysql.models.flexibleservers.ResourceIdentityType.system_assigned.value)

    return resolve_poller(
        server_client.create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def flexible_server_connection_string(
            server_name='{server}', database_name='{database}', administrator_login='{login}',
            administrator_login_password='{password}'):
    host = '{}.mysql.database.azure.com'.format(server_name)
    return {
        'connectionStrings': _create_mysql_connection_strings(host, administrator_login, administrator_login_password, database_name)
    }


def _create_mysql_connection_strings(host, user, password, database):
    result = {
        'mysql_cmd': "mysql {database} --host {host} --user {user} --password={password}",
        'ado.net': "Server={host}; Port=3306; Database={database}; Uid={user}; Pwd={password};",
        'jdbc': "jdbc:mysql://{host}:3306/{database}?user={user}&password={password}",
        'jdbc Spring': "spring.datasource.url=jdbc:mysql://{host}:3306/{database}  "
                       "spring.datasource.username={user}  "
                       "spring.datasource.password={password}",
        'node.js': "var conn = mysql.createConnection({{host: '{host}', user: '{user}', "
                   "password: {password}, database: {database}, port: 3306}});",
        'php': "host={host} port=3306 dbname={database} user={user} password={password}",
        'python': "cnx = mysql.connector.connect(user='{user}', password='{password}', host='{host}', "
                  "port=3306, database='{database}')",
        'ruby': "client = Mysql2::Client.new(username: '{user}', password: '{password}', "
                "database: '{database}', host: '{host}', port: 3306)",
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


def _form_response(username, sku, location, id, host, version, password, connection_string, database_name, firewall_id=None, subnet_id=None):
    output = {
        'host': host,
        'username': username,
        'password': password,
        'skuname': sku,
        'location': location,
        'id': id,
        'version': version,
        'databaseName': database_name,
        'connectionString': connection_string
    }
    if firewall_id is not None:
        output['firewallName'] = firewall_id
    if subnet_id is not None:
        output['subnetId'] = subnet_id
    return output


def _update_local_contexts(cmd, server_name, resource_group_name, location, user):
    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'server_name',
                                    server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([ALL], 'location',
                                    location)  # Setting the location in the local context
        cmd.cli_ctx.local_context.set([ALL], 'resource_group_name', resource_group_name)
        cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'administrator_login',
                                      user)  # Setting the server name in the local context


def _create_database(db_context, cmd, resource_group_name, server_name, database_name):
    # check for existing database, create if not
    cf_db, logging_name = db_context.cf_db, db_context.logging_name
    database_client = cf_db(cmd.cli_ctx, None)
    try:
        database_client.get(resource_group_name, server_name, database_name)
    except CloudError:
        logger.warning('Creating %s database \'%s\'...', logging_name, database_name)
        resolve_poller(
            database_client.create_or_update(resource_group_name, server_name, database_name, 'utf8'), cmd.cli_ctx,
            '{} Database Create/Update'.format(logging_name))


def _create_mysql_connection_string(host, database_name, user_name, password):
    connection_kwargs = {
        'host': host,
        'dbname': database_name,
        'username': user_name,
        'password': password if password is not None else '{password}'
    }
    return 'server={host};database={dbname};uid={username};pwd={password}'.format(**connection_kwargs)


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class DbContext:
    def __init__(self, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_db = cf_db
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client