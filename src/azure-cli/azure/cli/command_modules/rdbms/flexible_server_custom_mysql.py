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
def flexible_server_create(cmd, client,
                           resource_group_name=None, server_name=None,
                           location=None, backup_retention=None,
                           sku_name=None, tier=None,
                           storage_gb=None, administrator_login=None,
                           administrator_login_password=None, version=None,
                           tags=None, database_name=None,
                           subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                           private_dns_zone_arguments=None, public_access=None,
                           high_availability=None, zone=None, maintenance_window=None,
                           geo_redundant_backup=None, standby_availability_zone=None,
                           iops=None, auto_grow=None):
    # Generate missing parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'mysql')
    db_context = DbContext(
        cmd=cmd, azure_sdk=mysql_flexibleservers, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
        cf_availability=cf_mysql_check_resource_availability, logging_name='MySQL', command_group='mysql', server_client=client,
        location=location)
                                                                             
    server_name = server_name.lower()

    mysql_arguments_validator(db_context,
                              server_name=server_name,
                              location=location,
                              tier=tier,
                              sku_name=sku_name,
                              storage_gb=storage_gb,
                              high_availability=high_availability,
                              standby_availability_zone=standby_availability_zone,
                              zone=zone,
                              subnet=subnet,
                              public_access=public_access,
                              version=version)

    # server_result = firewall_id = subnet_id = None

    # network = mysql_flexibleservers.models.Network()
    # if subnet is not None or vnet is not None:
    #     subnet_id = prepare_private_network(cmd,
    #                                         resource_group_name,
    #                                         server_name,
    #                                         vnet=vnet,
    #                                         subnet=subnet,
    #                                         location=location,
    #                                         delegation_service_name=DELEGATION_SERVICE_NAME,
    #                                         vnet_address_pref=vnet_address_prefix,
    #                                         subnet_address_pref=subnet_address_prefix)
    #     private_dns_zone_id = prepare_private_dns_zone(cmd,
    #                                                    'PostgreSQL',
    #                                                    resource_group_name,
    #                                                    server_name,
    #                                                    private_dns_zone=private_dns_zone_arguments,
    #                                                    subnet_id=subnet_id,
    #                                                    location=location)
    #     network.delegated_subnet_resource_id = subnet_id
    #     network.private_dns_zone_arm_resource_id = private_dns_zone_id
    # else:
    #     network.public_network_access = ' Enabled'

    # # determine IOPS
    # iops = _determine_iops(storage_gb=storage_mb,
    #                        iops_info=iops_info,
    #                        iops_input=iops,
    #                        tier=tier,
    #                        sku_name=sku_name)

    # storage = mysql_flexibleservers.models.Storage(storage_size_gb=storage_gb,
    #                                                iops=iops,
    #                                                auto_grow=auto_grow)


    # backup = mysql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
    #                                              geo_redundant_backup=geo_redundant_backup)

    # sku = mysql_flexibleservers.models.Sku(name=sku_name, tier=tier)

    # if high_availability.lower() == "enabled":
    #     high_availability = "ZoneRedundant"
    # high_availability = mysql_flexibleservers.models.HighAvailability(mode=high_availability,
    #                                                                   standby_availability_zone=standby_availability_zone)

    # maintenance_window_object = postgresql_flexibleservers.models.MaintenanceWindow()
    # if maintenance_window is not None:
    #     custom_window = 'Enabled'
    #     day_of_week, start_hour, start_minute = parse_maintenance_window(maintenance_window)
    # else:
    #     custom_window = "Disabled"
    #     day_of_week = start_hour = start_minute = 0
    # maintenance_window_object.day_of_week = day_of_week
    # maintenance_window_object.start_hour = start_hour
    # maintenance_window_object.start_minute = start_minute
    # maintenance_window_object.custom_window = custom_window

    # administrator_login_password = generate_password(administrator_login_password)

    # # Create mysql server
    # # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
    # server_result = _create_server(db_context, cmd, resource_group_name, server_name,
    #                                tags=tags,
    #                                location=location,
    #                                sku=sku,
    #                                administrator_login=administrator_login,
    #                                administrator_login_password=administrator_login_password,
    #                                storage=storage,
    #                                backup=backup,
    #                                network=network,
    #                                version=version,
    #                                high_availability=high_availability,
    #                                maintenance_window=maintenance_window_object,
    #                                availability_zone=zone)

    # # Adding firewall rule
    # if public_access is not None and str(public_access).lower() != 'none':
    #     if str(public_access).lower() == 'all':
    #         start_ip, end_ip = '0.0.0.0', '255.255.255.255'
    #     else:
    #         start_ip, end_ip = parse_public_access_input(public_access)
    #     firewall_id = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

    # # Create mysql database if it does not exist
    # if database_name is None:
    #     database_name = DEFAULT_DB_NAME
    # _create_database(db_context, cmd, resource_group_name, server_name, database_name)

    # user = server_result.administrator_login
    # server_id = server_result.id
    # loc = server_result.location
    # version = server_result.version
    # sku = server_result.sku.name
    # host = server_result.fully_qualified_domain_name

    # logger.warning('Make a note of your password. If you forget, you would have to reset your password with'
    #                '\'az mysql flexible-server update -n %s -g %s -p <new-password>\'.',
    #                server_name, resource_group_name)

    # _update_local_contexts(cmd, server_name, resource_group_name, location, user)

    # return _form_response(user, sku, loc, server_id, host, version,
    #                       administrator_login_password if administrator_login_password is not None else '*****',
    #                       _create_mysql_connection_string(host, database_name, user, administrator_login_password),
    #                       database_name, firewall_id, subnet_id)


def flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, location=None, no_wait=False):
    provider = 'Microsoft.DBforMySQL'
    server_name = server_name.lower()
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
    else:
        source_server_id = source_server

    try:
        id_parts = parse_resource_id(source_server_id)
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])

        parameters = mysql_flexibleservers.models.Server(
            location=source_server_object.location,
            point_in_time_utc=restore_point_in_time,
            source_server_resource_id=source_server_id,  # this should be the source server name, not id
            create_mode="PointInTimeRestore",
            availability_zone=zone
        )

        if source_server_object.network.public_network_access == 'Disabled':
            setup_restore_network(cmd=cmd,
                                  resource_group_name=resource_group_name,
                                  server_name=server_name,
                                  location=parameters.location,
                                  parameters=parameters,
                                  source_server_object=source_server_object,
                                  subnet_id=subnet,
                                  private_dns_zone=private_dns_zone_arguments)

    except Exception as e:
        raise ResourceNotFoundError(e)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


def setup_restore_network(cmd, resource_group_name, server_name, location, parameters, source_server_object, subnet_id=None, private_dns_zone=None):
    
    parameters.network = mysql_flexibleservers.models.Network(delegated_subnet_resource_id=source_server_object.network.delegated_subnet_resource_id,
                                                              private_dns_zone_arm_resource_id=source_server_object.network.private_dns_zone_arm_resource_id)

    if subnet_id is not None:
        vnet_sub, vnet_rg, vnet_name, subnet_name = get_id_components(subnet_id)
        resource_client = resource_client_factory(cmd.cli_ctx, vnet_sub)
        nw_client = network_client_factory(cmd.cli_ctx, subscription_id=vnet_sub)
        Delegation = cmd.get_models('Delegation', resource_type=ResourceType.MGMT_NETWORK)
        delegation = Delegation(name=DELEGATION_SERVICE_NAME, service_name=DELEGATION_SERVICE_NAME)
        if check_existence(resource_client, subnet_name, vnet_rg, 'Microsoft.Network', 'subnets', parent_name=vnet_name, parent_type='virtualNetworks'):
            subnet = nw_client.subnets.get(vnet_rg, vnet_name, subnet_name)
            # Add Delegation if not delegated already
            if not subnet.delegations:
                logger.warning('Adding "%s" delegation to the existing subnet %s.', DELEGATION_SERVICE_NAME, subnet_name)
                subnet.delegations = [delegation]
                subnet = nw_client.subnets.begin_create_or_update(vnet_rg, vnet_name, subnet_name, subnet).result()
            else:
                for delgtn in subnet.delegations:
                    if delgtn.service_name != DELEGATION_SERVICE_NAME:
                        raise CLIError("Can not use subnet with existing delegations other than {}".format(DELEGATION_SERVICE_NAME))
            parameters.network.delegated_subnet_resource_id = subnet_id
        else:
            raise ResourceNotFoundError("The subnet does not exist. Please verify the subnet Id.")

    if private_dns_zone is not None or source_server_object.network.private_dns_zone_arm_resource_id is None:
        subnet_id = parameters.network.delegated_subnet_resource_id
        private_dns_zone_id = prepare_private_dns_zone(cmd,
                                                       'MySQL',
                                                       resource_group_name,
                                                       server_name,
                                                       private_dns_zone=private_dns_zone,
                                                       subnet_id=subnet_id,
                                                       location=location)
        parameters.network.private_dns_zone_arm_resource_id = private_dns_zone_id

# pylint: disable=too-many-branches
def flexible_server_update_custom_func(cmd, client, instance,
                                       sku_name=None,
                                       tier=None,
                                       storage_gb=None,
                                       auto_grow=None,
                                       iops=None,
                                       backup_retention=None,
                                       administrator_login_password=None,
                                       high_availability=None,
                                       standby_availability_zone=None,
                                       maintenance_window=None,
                                       tags=None,
                                       replication_role=None):
    # validator
    location = ''.join(instance.location.lower().split())
    db_context = DbContext(
        cmd=cmd, azure_sdk=mysal_flexibleservers, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
        cf_availability=cf_mysql_check_resource_availability, logging_name='MySQL', command_group='mysql', server_client=client,
        location=instance.location)

    mysql_arguments_validator(db_context,
                              location=location,
                              tier=tier,
                              sku_name=sku_name,
                              storage_gb=storage_gb,
                              high_availability=high_availability,
                              zone=instance.availability_zone,
                              standby_availability_zone=standby_availability_zone,
                              instance=instance)

    server_module_path = instance.__module__
    module = import_module(server_module_path)  # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name

    if tier:
        instance.sku.tier = tier

    if backup_retention:
        instance.backup.backup_retention_days = backup_retention

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

    if high_availability:
        if high_availability.lower() == "enabled":
            high_availability = "ZoneRedundant"
            instance.high_availability.mode = high_availability
            if standby_availability_zone:
                instance.high_availability.standby_availability_zone = standby_availability_zone
        else:
            instance.high_availability = postgresql_flexibleservers.models.HighAvailability(mode=high_availability)

    if storage_gb:
        instance.storage.storage_size_gb = storage_gb

    if not iops:
        iops = instance.storage_profile.storage_iops
    instance.storage.iops = _determine_iops(storage_gb=instance.storage_profile.storage_mb // 1024,
                                            iops_info=iops_info,
                                            iops_input=iops,
                                            tier=instance.sku.tier,
                                            sku_name=instance.sku.name)

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
                             storage=instance.storage,
                             backup=instance.backup,
                             administrator_login_password=administrator_login_password,
                             high_availability=instance.high_availability,
                             maintenance_window=instance.maintenance_window,
                             tags=tags)


    # if assign_identity:
    #     if server_module_path.find('mysql'):
    #         if instance.identity is None:
    #             instance.identity = mysql_flexibleservers.models.Identity()
    #         params.identity = instance.identity

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
    replica_name = replica_name.lower()
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
    else:
        source_server_id = source_server

    source_server_id_parts = parse_resource_id(server_name)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except Exception as e:
        raise ResourceNotFoundError(e)

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
        raise ResourceNotFoundError(e)

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


def _create_server(db_context, cmd, resource_group_name, server_name, tags, location, sku, administrator_login, administrator_login_password,
                   storage, backup, network, version, high_availability, maintenance_window, availability_zone, iops, auto_grow):
    logging_name, server_client = db_context.logging_name, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/mysql-pricing for pricing details', server_name, sku_name)

    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.    
    parameters = postgresql_flexibleservers.models.Server(
        tags=tags,
        location=location,
        sku=sku,
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        storage=storage,
        backup=backup,
        network=network,
        version=version,
        high_availability=high_availability,
        maintenance_window=maintenance_window,
        availability_zone=availability_zone,
        create_mode="Create")

    # if assign_identity:
    #     parameters.identity = mysql_flexibleservers.models.Identity()

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
    def __init__(self, cmd=None, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 cf_availability=None, command_group=None, server_client=None, location=None):
        self.cmd = cmd
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_db = cf_db
        self.cf_availability = cf_availability
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client
        self.location = location
