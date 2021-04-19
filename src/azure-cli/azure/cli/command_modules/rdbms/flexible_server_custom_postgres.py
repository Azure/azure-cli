# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.local_context import ALL
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.mgmt.rdbms import postgresql_flexibleservers
from ._client_factory import cf_postgres_flexible_firewall_rules, get_postgresql_flexible_management_client, cf_postgres_flexible_db
from .flexible_server_custom_common import user_confirmation
from ._flexible_server_util import generate_missing_parameters, resolve_poller, create_firewall_rule, \
    parse_public_access_input, generate_password, parse_maintenance_window, get_postgres_list_skus_info, \
    DEFAULT_LOCATION_PG
from .flexible_server_virtual_network import prepare_private_network
from .validators import pg_arguments_validator


logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
DELEGATION_SERVICE_NAME = "Microsoft.DBforPostgreSQL/flexibleServers"


# region create without args
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def flexible_server_create(cmd, client,
                           resource_group_name=None, server_name=None,
                           location=None, backup_retention=None,
                           sku_name=None, tier=None,
                           storage_mb=None, administrator_login=None,
                           administrator_login_password=None, version=None,
                           tags=None, public_access=None, database_name=None,
                           assign_identity=False, subnet_arm_resource_id=None,
                           high_availability=None, zone=None, vnet_resource_id=None,
                           vnet_address_prefix=None, subnet_address_prefix=None):
    # validator
    if location is None:
        location = DEFAULT_LOCATION_PG
    sku_info = get_postgres_list_skus_info(cmd, location)
    pg_arguments_validator(tier, sku_name, storage_mb, sku_info, version=version)
    storage_mb *= 1024

    db_context = DbContext(
        azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules, cf_db=cf_postgres_flexible_db,
        logging_name='PostgreSQL', command_group='postgres', server_client=client)

    # Raise error when user passes values for both parameters
    if subnet_arm_resource_id is not None and public_access is not None:
        raise CLIError("Incorrect usage : A combination of the parameters --subnet "
                       "and --public_access is invalid. Use either one of them.")

    server_result = firewall_id = subnet_id = None

    # Populate desired parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'postgres')
    server_name = server_name.lower()

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
        delegated_subnet_arguments = postgresql_flexibleservers.models.ServerPropertiesDelegatedSubnetArguments(subnet_arm_resource_id=subnet_id)
    else:
        delegated_subnet_arguments = None

    administrator_login_password = generate_password(administrator_login_password)
    if server_result is None:
        # Create postgresql
        # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
        server_result = _create_server(db_context, cmd, resource_group_name, server_name, location,
                                       backup_retention,
                                       sku_name, tier, storage_mb, administrator_login,
                                       administrator_login_password,
                                       version, tags, subnet_id, assign_identity, delegated_subnet_arguments,
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
    server_id = server_result.id
    loc = server_result.location
    version = server_result.version
    sku = server_result.sku.name
    host = server_result.fully_qualified_domain_name

    logger.warning('Make a note of your password. If you forget, you would have to'
                   'reset your password with "az postgres flexible-server update -n %s -g %s -p <new-password>".',
                   server_name, resource_group_name)

    _update_local_contexts(cmd, server_name, resource_group_name, location, user)

    return _form_response(user, sku, loc, server_id, host, version,
                          administrator_login_password if administrator_login_password is not None else '*****',
                          _create_postgresql_connection_string(host, user, administrator_login_password), firewall_id,
                          subnet_id)


def flexible_server_restore(cmd, client,
                            resource_group_name, server_name,
                            source_server, restore_point_in_time=None, location=None, zone=None, no_wait=False):
    provider = 'Microsoft.DBforPostgreSQL'

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server_id = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=provider,
                type='flexibleServers',
                name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    parameters = postgresql_flexibleservers.models.Server(
        point_in_time_utc=restore_point_in_time,
        source_server_name=source_server,  # this should be the source server name, not id
        create_mode="PointInTimeRestore",
        availability_zone=zone,
        source_resource_group_name=resource_group_name,
        source_subscription_id=get_subscription_id(cmd.cli_ctx),
        location=location)

    # Retrieve location from same location as source server
    id_parts = parse_resource_id(source_server_id)
    try:
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        parameters.location = source_server_object.location
    except Exception as e:
        raise ResourceNotFoundError(e)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


# Update Flexible server command
def flexible_server_update_custom_func(cmd, instance,
                                       sku_name=None,
                                       tier=None,
                                       storage_mb=None,
                                       backup_retention=None,
                                       administrator_login_password=None,
                                       ha_enabled=None,
                                       maintenance_window=None,
                                       assign_identity=False,
                                       tags=None):

    # validator
    location = ''.join(instance.location.lower().split())
    sku_info = get_postgres_list_skus_info(cmd, location)
    pg_arguments_validator(tier, sku_name, storage_mb, sku_info, instance=instance)

    from importlib import import_module

    server_module_path = instance.__module__
    module = import_module(server_module_path)
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name

    if tier:
        instance.sku.tier = tier

    if storage_mb:
        instance.storage_profile.storage_mb = storage_mb * 1024

    if backup_retention:
        instance.storage_profile.backup_retention_days = backup_retention

    if maintenance_window:
        # if disabled is pass in reset to default values
        if maintenance_window.lower() == "disabled":
            day_of_week = start_hour = start_minute = 0
            custom_window = "Disabled"
        else:
            day_of_week, start_hour, start_minute = parse_maintenance_window(maintenance_window)
            custom_window = "Enabled"

        # set values - if maintenance_window when is None when created then create a new object
        if instance.maintenance_window is None:
            instance.maintenance_window = postgresql_flexibleservers.models.MaintenanceWindow(
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

    params = ServerForUpdate(sku=instance.sku,
                             storage_profile=instance.storage_profile,
                             administrator_login_password=administrator_login_password,
                             ha_enabled=ha_enabled,
                             maintenance_window=instance.maintenance_window,
                             tags=tags)

    if assign_identity:
        if server_module_path.find('postgres'):
            if instance.identity is None:
                instance.identity = postgresql_flexibleservers.models.Identity()
            params.identity = instance.identity
    return params


def server_delete_func(cmd, client, resource_group_name=None, server_name=None, yes=None):
    confirm = yes
    result = None
    if not yes:
        confirm = user_confirmation(
            "Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name,
                                                                                              resource_group_name),
            yes=yes)
    if confirm:
        try:
            result = client.begin_delete(resource_group_name, server_name)
            if cmd.cli_ctx.local_context.is_on:
                local_context_file = cmd.cli_ctx.local_context._get_local_context_file()  # pylint: disable=protected-access
                local_context_file.remove_option('postgres flexible-server', 'server_name')
                local_context_file.remove_option('postgres flexible-server', 'administrator_login')
                local_context_file.remove_option('postgres flexible-server', 'database_name')
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
            raise CLIError(ex)
    return result


# Wait command
def flexible_server_postgresql_get(cmd, resource_group_name, server_name):
    client = get_postgresql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
    if source is None and value is None:
        # update the command with system default
        try:
            parameter = client.get(resource_group_name, server_name, configuration_name)
            value = parameter.default_value  # reset value to default

            # this should be 'system-default' but there is currently a bug in PG, so keeping as what it is for now
            # this will reset source to be 'system-default' anyway
            source = parameter.source
        except CloudError as e:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
    elif source is None:
        source = "user-override"

    parameters = postgresql_flexibleservers.models.Configuration(
        configuration_name=configuration_name,
        value=value,
        source=source
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


def flexible_list_skus(cmd, client, location):
    result = client.execute(location)
    logger.warning('For prices please refer to https://aka.ms/postgres-pricing')
    return result


def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name, tier,
                   storage_mb, administrator_login, administrator_login_password, version, tags, public_network_access,
                   assign_identity, delegated_subnet_arguments, ha_enabled, availability_zone):
    logging_name, server_client = db_context.logging_name, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/postgres-pricing for pricing details', server_name, sku_name)

    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.
    parameters = postgresql_flexibleservers.models.Server(
        sku=postgresql_flexibleservers.models.Sku(name=sku_name, tier=tier),
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        public_network_access=public_network_access,
        storage_profile=postgresql_flexibleservers.models.StorageProfile(
            backup_retention_days=backup_retention,
            storage_mb=storage_mb),
        delegated_subnet_arguments=delegated_subnet_arguments,
        ha_enabled=ha_enabled,
        availability_zone=availability_zone,
        location=location,
        create_mode="Default",  # can also be create
        tags=tags)

    if assign_identity:
        parameters.identity = postgresql_flexibleservers.models.Identity()

    return resolve_poller(
        server_client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


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
            'collation': 'en_US.utf8'
        }
        resolve_poller(
            database_client.begin_create(resource_group_name, server_name, database_name, parameters), cmd.cli_ctx,
            '{} Database Create/Update'.format(logging_name))


def database_create_func(client, resource_group_name=None, server_name=None, database_name=None, charset=None, collation=None):

    if charset is None and collation is None:
        charset = 'utf8'
        collation = 'en_US.utf8'
        logger.warning("Creating database with utf8 charset and en_US.utf8 collation")
    elif (not charset and collation) or (charset and not collation):
        raise RequiredArgumentMissingError("charset and collation have to be input together.")

    parameters = {
        'name': database_name,
        'charset': charset,
        'collation': collation
    }

    return client.begin_create(
        resource_group_name,
        server_name,
        database_name,
        parameters)


def flexible_server_connection_string(
        server_name='{server}', database_name='{database}', administrator_login='{login}',
        administrator_login_password='{password}'):
    host = '{}.postgres.database.azure.com'.format(server_name)
    return {
        'connectionStrings': _create_postgresql_connection_strings(host, administrator_login,
                                                                   administrator_login_password, database_name)
    }


def _create_postgresql_connection_strings(host, user, password, database):
    result = {
        'psql_cmd': "postgresql://{user}:{password}@{host}/postgres?sslmode=require",
        'ado.net': "Server={host};Database=postgres;Port=5432;User Id={user};Password={password};",
        'jdbc': "jdbc:postgresql://{host}:5432/postgres?user={user}&password={password}",
        'jdbc Spring': "spring.datasource.url=jdbc:postgresql://{host}:5432/postgres  "
                       "spring.datasource.username={user}  "
                       "spring.datasource.password={password}",
        'node.js': "var client = new pg.Client('postgres://{user}:{password}@{host}:5432/postgres');",
        'php': "host={host} port=5432 dbname=postgres user={user} password={password}",
        'python': "cnx = psycopg2.connect(database='postgres', user='{user}', host='{host}', password='{password}', "
                  "port='5432')",
        'ruby': "cnx = PG::Connection.new(:host => '{host}', :user => '{user}', :dbname => 'postgres', "
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


def _create_postgresql_connection_string(host, user, password):
    connection_kwargs = {
        'user': user,
        'host': host,
        'password': password if password is not None else '{password}'
    }
    return 'postgresql://{user}:{password}@{host}/postgres?sslmode=require'.format(**connection_kwargs)


def _form_response(username, sku, location, server_id, host, version, password, connection_string, firewall_id=None,
                   subnet_id=None):
    '''
    from collections import OrderedDict
    new_entry = OrderedDict()
    new_entry['Id'] = server_id
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
        'id': server_id,
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


# pylint: disable=too-many-instance-attributes, too-few-public-methods, useless-object-inheritance
class DbContext(object):
    def __init__(self, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.logging_name = logging_name
        self.cf_db = cf_db
        self.command_group = command_group
        self.server_client = server_client
