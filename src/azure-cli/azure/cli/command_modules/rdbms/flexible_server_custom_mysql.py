# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from importlib import import_module
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.core.azclierror import RequiredArgumentMissingError, ArgumentUsageError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait, user_confirmation
from azure.cli.core.local_context import ALL
from azure.mgmt.rdbms import mysql_flexibleservers
from ._client_factory import get_mysql_flexible_management_client, cf_mysql_flexible_firewall_rules, \
    cf_mysql_flexible_db, cf_mysql_check_resource_availability
from ._flexible_server_util import resolve_poller, generate_missing_parameters, parse_public_access_input, \
    generate_password, parse_maintenance_window, get_mysql_list_skus_info
from .flexible_server_custom_common import create_firewall_rule
from .flexible_server_virtual_network import prepare_private_network
from .validators import mysql_arguments_validator, validate_server_name, validate_auto_grow_update, validate_mysql_ha_enabled

logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
DELEGATION_SERVICE_NAME = "Microsoft.DBforMySQL/flexibleServers"
MINIMUM_IOPS = 300


# region create without args
# pylint: disable=too-many-locals, too-many-statements, raise-missing-from
def flexible_server_create(cmd, client, resource_group_name=None, server_name=None, sku_name=None, tier=None,
                           location=None, storage_mb=None, administrator_login=None,
                           administrator_login_password=None, version=None,
                           backup_retention=None, tags=None, public_access=None, database_name=None,
                           subnet_arm_resource_id=None, high_availability=None, zone=None, assign_identity=False,
                           vnet_resource_id=None, vnet_address_prefix=None, subnet_address_prefix=None, iops=None, auto_grow=None):

    # Populate desired parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'mysql')
    # validator
    sku_info, iops_info, single_az = get_mysql_list_skus_info(cmd, location)
    mysql_arguments_validator(tier, sku_name, storage_mb, backup_retention, sku_info, version=version)

    db_context = DbContext(
        azure_sdk=mysql_flexibleservers, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
        logging_name='MySQL', command_group='mysql', server_client=client)

    if high_availability is not None and high_availability.lower() == 'enabled':
        if tier == 'Burstable':
            raise ArgumentUsageError("High availability is not supported for Burstable tier")
        if single_az:
            raise ArgumentUsageError("This region is single availability zone. High availability is not supported in a single availability zone region.")

    # Raise error when user passes values for both parameters
    if subnet_arm_resource_id is not None and public_access is not None:
        raise CLIError("Incorrect usage : A combination of the parameters --subnet "
                       "and --public_access is invalid. Use either one of them.")

    server_result = firewall_id = subnet_id = None
    server_name = server_name.lower()
    validate_server_name(cf_mysql_check_resource_availability(cmd.cli_ctx, '_'), server_name, 'Microsoft.DBforMySQL/flexibleServers')

    # Handle Vnet scenario
    if public_access is None:
        subnet_id = prepare_private_network(cmd,
                                            resource_group_name,
                                            server_name,
                                            vnet=vnet_resource_id,
                                            subnet=subnet_arm_resource_id,
                                            location=location,
                                            delegation_service_name=DELEGATION_SERVICE_NAME,
                                            vnet_address_pref=vnet_address_prefix,
                                            subnet_address_pref=subnet_address_prefix)
        delegated_subnet_arguments = mysql_flexibleservers.models.DelegatedSubnetArguments(subnet_arm_resource_id=subnet_id)
    else:
        delegated_subnet_arguments = None

    # determine IOPS
    iops = _determine_iops(storage_gb=storage_mb,
                           iops_info=iops_info,
                           iops_input=iops,
                           tier=tier,
                           sku_name=sku_name)

    storage_mb *= 1024  # storage input comes in GiB value
    administrator_login_password = generate_password(administrator_login_password)

    # Create mysql server
    # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
    server_result = _create_server(db_context, cmd, resource_group_name, server_name, location,
                                   backup_retention,
                                   sku_name, tier, storage_mb, administrator_login,
                                   administrator_login_password,
                                   version, tags, delegated_subnet_arguments, assign_identity, public_access,
                                   high_availability, zone, iops, auto_grow)

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
    server_id = server_result.id
    loc = server_result.location
    version = server_result.version
    sku = server_result.sku.name
    host = server_result.fully_qualified_domain_name

    logger.warning('Make a note of your password. If you forget, you would have to reset your password with'
                   '\'az mysql flexible-server update -n %s -g %s -p <new-password>\'.',
                   server_name, resource_group_name)

    _update_local_contexts(cmd, server_name, resource_group_name, location, user)

    return _form_response(user, sku, loc, server_id, host, version,
                          administrator_login_password if administrator_login_password is not None else '*****',
                          _create_mysql_connection_string(host, database_name, user, administrator_login_password),
                          database_name, firewall_id, subnet_id)


def flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, location=None, no_wait=False):
    provider = 'Microsoft.DBforMySQL'
    validate_server_name(cf_mysql_check_resource_availability(cmd.cli_ctx, '_'), server_name, 'Microsoft.DBforMySQL/flexibleServers')

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

    parameters = mysql_flexibleservers.models.Server(
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
    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


# pylint: disable=too-many-branches
def flexible_server_update_custom_func(cmd, instance,
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
                                       replication_role=None,
                                       maintenance_window=None,
                                       ha_enabled=None,
                                       iops=None):
    # validator
    location = ''.join(instance.location.lower().split())
    sku_info, iops_info, _ = get_mysql_list_skus_info(cmd, location)
    mysql_arguments_validator(tier, sku_name, storage_mb, backup_retention, sku_info, instance=instance)

    server_module_path = instance.__module__
    module = import_module(server_module_path)  # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if storage_mb:
        instance.storage_profile.storage_mb = storage_mb * 1024

    if (tier is not None and sku_name is None) or (tier is None and sku_name is not None):
        raise CLIError('Argument Error. If you pass --tier, --sku-name is a mandatory parameter and vice-versa.')

    if tier:
        instance.sku.tier = tier

    if sku_name:
        instance.sku.name = sku_name

    if not iops:
        iops = instance.storage_profile.storage_iops
    instance.storage_profile.storage_iops = _determine_iops(storage_gb=instance.storage_profile.storage_mb // 1024,
                                                            iops_info=iops_info,
                                                            iops_input=iops,
                                                            tier=instance.sku.tier,
                                                            sku_name=instance.sku.name)

    if backup_retention:
        instance.storage_profile.backup_retention_days = backup_retention

    if ha_enabled:
        validate_mysql_ha_enabled(instance)

    if auto_grow:
        validate_auto_grow_update(instance, auto_grow)
        instance.storage_profile.storage_autogrow = auto_grow

    if subnet_arm_resource_id:
        instance.delegated_subnet_arguments.subnet_arm_resource_id = subnet_arm_resource_id

    if maintenance_window:
        logger.warning('If you are updating maintenancw window with other parameter, maintenance window will be updated first. Please update the other parameters later.')
        # if disabled is pass in reset to default values
        if maintenance_window.lower() == "disabled":
            day_of_week = start_hour = start_minute = 0
            custom_window = "Disabled"
        else:
            day_of_week, start_hour, start_minute = parse_maintenance_window(maintenance_window)
            custom_window = "Enabled"

        # set values - if maintenance_window when is None when created then create a new object
        if instance.maintenance_window is None:
            instance.maintenance_window = mysql_flexibleservers.models.MaintenanceWindow(
                day_of_week=day_of_week,
                start_hour=start_hour,
                start_minute=start_minute,
                custom_window=custom_window
            )
        else:
            instance.maintenance_window.day_of_week = day_of_week
            instance.maintenance_window.start_hour = start_hour
            instance.maintenance_window.start_minute = start_minute
            instance.maintenance_window.custom_window = custom_window

        return ServerForUpdate(maintenance_window=instance.maintenance_window)

    params = ServerForUpdate(sku=instance.sku,
                             storage_profile=instance.storage_profile,
                             administrator_login_password=administrator_login_password,
                             ssl_enforcement=ssl_enforcement,
                             delegated_subnet_arguments=instance.delegated_subnet_arguments,
                             tags=tags,
                             ha_enabled=ha_enabled,
                             replication_role=replication_role)

    if assign_identity:
        if server_module_path.find('mysql'):
            if instance.identity is None:
                instance.identity = mysql_flexibleservers.models.Identity()
            params.identity = instance.identity

    return params


def server_delete_func(cmd, client, resource_group_name=None, server_name=None, yes=None):
    result = None  # default return value

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name,
                                                                                              resource_group_name), yes=yes)
    try:
        result = client.begin_delete(resource_group_name, server_name)
        if cmd.cli_ctx.local_context.is_on:
            local_context_file = cmd.cli_ctx.local_context._get_local_context_file()  # pylint: disable=protected-access
            local_context_file.remove_option('mysql flexible-server', 'server_name')
            local_context_file.remove_option('mysql flexible-server', 'administrator_login')
            local_context_file.remove_option('mysql flexible-server', 'database_name')

    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
        raise CLIError(ex)
    return result


# Parameter update command
def flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
    if source is None and value is None:
        # update the command with system default
        try:
            parameter = client.get(resource_group_name, server_name, configuration_name)
            value = parameter.default_value  # reset value to default
            source = "system-default"
        except CloudError as e:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
    elif source is None:
        source = "user-override"

    parameters = mysql_flexibleservers.models.Configuration(
        name=configuration_name,
        value=value,
        source=source
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


# Replica commands
# Custom functions for server replica, will add PostgreSQL part after backend ready in future
def flexible_replica_create(cmd, client, resource_group_name, replica_name, server_name, no_wait=False, location=None, sku_name=None, tier=None, **kwargs):
    provider = 'Microsoft.DBforMySQL'
    validate_server_name(cf_mysql_check_resource_availability(cmd.cli_ctx, '_'), replica_name, 'Microsoft.DBforMySQL/flexibleServers')

    # set source server id
    if not is_valid_resource_id(server_name):
        if len(server_name.split('/')) == 1:
            server_name = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                      resource_group=resource_group_name,
                                      namespace=provider,
                                      type='flexibleServers',
                                      name=server_name)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(server_name))

    source_server_id_parts = parse_resource_id(server_name)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except CloudError as e:
        raise CLIError('Unable to get source server: {}.'.format(str(e)))

    location = source_server_object.location
    sku_name = source_server_object.sku.name
    tier = source_server_object.sku.tier

    parameters = mysql_flexibleservers.models.Server(
        sku=mysql_flexibleservers.models.Sku(name=sku_name, tier=tier),
        source_server_id=server_name,
        location=location,
        create_mode="Replica")
    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, replica_name, parameters)


def flexible_replica_stop(client, resource_group_name, server_name):
    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise CLIError('Unable to get server: {}.'.format(str(e)))

    if server_object.replication_role is not None and server_object.replication_role.lower() != "replica":
        raise CLIError('Server {} is not a replica server.'.format(server_name))

    server_module_path = server_object.__module__
    module = import_module(server_module_path)  # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    params = ServerForUpdate(replication_role='None')

    return client.begin_update(resource_group_name, server_name, params)


def flexible_server_mysql_get(cmd, resource_group_name, server_name):
    client = get_mysql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def flexible_list_skus(cmd, client, location):
    result = client.list(location)
    logger.warning('For prices please refer to https://aka.ms/mysql-pricing')
    return result


def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name, tier,
                   storage_mb, administrator_login, administrator_login_password, version, tags,
                   delegated_subnet_arguments,
                   assign_identity, public_network_access, ha_enabled, availability_zone, iops, auto_grow):
    logging_name, server_client = db_context.logging_name, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/mysql-pricing for pricing details', server_name, sku_name)

    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.
    parameters = mysql_flexibleservers.models.Server(
        sku=mysql_flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=mysql_flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            storage_mb=storage_mb,
            storage_iops=iops,
            storage_autogrow=auto_grow),
        location=location,
        create_mode="Default",
        delegated_subnet_arguments=delegated_subnet_arguments,
        ha_enabled=ha_enabled,
        availability_zone=availability_zone,
        tags=tags)

    if assign_identity:
        parameters.identity = mysql_flexibleservers.models.Identity()

    return resolve_poller(
        server_client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def flexible_server_connection_string(
        server_name='{server}', database_name='{database}', administrator_login='{login}',
        administrator_login_password='{password}'):
    host = '{}.mysql.database.azure.com'.format(server_name)
    if database_name is None:
        database_name = 'mysql'
    return {
        'connectionStrings': _create_mysql_connection_strings(host, administrator_login, administrator_login_password,
                                                              database_name)
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


def _form_response(username, sku, location, server_id, host, version, password, connection_string, database_name,
                   firewall_id=None, subnet_id=None):
    output = {
        'host': host,
        'username': username,
        'password': password,
        'skuname': sku,
        'location': location,
        'id': server_id,
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
    except ResourceNotFoundError:
        logger.warning('Creating %s database \'%s\'...', logging_name, database_name)
        parameters = {
            'name': database_name,
            'charset': 'utf8',
            'collation': 'utf8_general_ci'
        }
        resolve_poller(
            database_client.begin_create_or_update(resource_group_name, server_name, database_name, parameters), cmd.cli_ctx,
            '{} Database Create/Update'.format(logging_name))


def database_create_func(client, resource_group_name=None, server_name=None, database_name=None, charset=None, collation=None):

    if charset is None and collation is None:
        charset = 'utf8'
        collation = 'utf8_general_ci'
        logger.warning("Creating database with utf8 charset and utf8_general_ci collation")
    elif (not charset and collation) or (charset and not collation):
        raise RequiredArgumentMissingError("charset and collation have to be input together.")

    parameters = {
        'name': database_name,
        'charset': charset,
        'collation': collation
    }

    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        database_name,
        parameters)


def _create_mysql_connection_string(host, database_name, user_name, password):
    connection_kwargs = {
        'host': host,
        'dbname': database_name,
        'username': user_name,
        'password': password if password is not None else '{password}'
    }
    return 'mysql {dbname} --host {host} --user {username} --password={password}'.format(**connection_kwargs)


def _determine_iops(storage_gb, iops_info, iops_input, tier, sku_name):
    max_supported_iops = iops_info[tier][sku_name]
    free_iops = get_free_iops(storage_in_mb=storage_gb * 1024,
                              iops_info=iops_info,
                              tier=tier,
                              sku_name=sku_name)

    iops = free_iops
    if iops_input and iops_input > free_iops:
        iops = min(iops_input, max_supported_iops)

    logger.warning("IOPS is %d which is either your input or free(maximum) IOPS supported for your storage size and SKU.", iops)
    return iops


def get_free_iops(storage_in_mb, iops_info, tier, sku_name):
    free_iops = MINIMUM_IOPS + (storage_in_mb // 1024) * 3
    max_supported_iops = iops_info[tier][sku_name]  # free iops cannot exceed maximum supported iops for the sku

    return min(free_iops, max_supported_iops)


# pylint: disable=too-many-instance-attributes, too-few-public-methods, useless-object-inheritance
class DbContext(object):
    def __init__(self, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_db = cf_db
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client
