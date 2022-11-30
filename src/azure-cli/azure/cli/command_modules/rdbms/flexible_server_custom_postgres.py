# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from importlib import import_module
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.local_context import ALL
from azure.cli.core.util import CLIError, sdk_no_wait, user_confirmation
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.core.azclierror import RequiredArgumentMissingError, ArgumentUsageError, InvalidArgumentValueError
from azure.mgmt.rdbms import postgresql_flexibleservers
from ._client_factory import cf_postgres_flexible_firewall_rules, get_postgresql_flexible_management_client, \
    cf_postgres_flexible_db, cf_postgres_check_resource_availability, cf_postgres_flexible_servers, \
    cf_postgres_check_resource_availability_with_location, cf_postgres_flexible_private_dns_zone_suffix_operations
from ._flexible_server_util import generate_missing_parameters, resolve_poller,\
    generate_password, parse_maintenance_window, get_current_time, build_identity_and_data_encryption, \
    _is_resource_name, get_tenant_id
from .flexible_server_custom_common import create_firewall_rule
from .flexible_server_virtual_network import prepare_private_network, prepare_private_dns_zone, prepare_public_network
from .validators import pg_arguments_validator, validate_server_name, validate_and_format_restore_point_in_time, \
    validate_postgres_replica, validate_georestore_network, pg_byok_validator

logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
DELEGATION_SERVICE_NAME = "Microsoft.DBforPostgreSQL/flexibleServers"
RESOURCE_PROVIDER = 'Microsoft.DBforPostgreSQL'


# region create without args
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=raise-missing-from, unbalanced-tuple-unpacking
def flexible_server_create(cmd, client,
                           resource_group_name=None, server_name=None,
                           location=None, backup_retention=None,
                           sku_name=None, tier=None,
                           storage_gb=None, administrator_login=None,
                           administrator_login_password=None, version=None,
                           tags=None, database_name=None,
                           subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                           private_dns_zone_arguments=None, public_access=None,
                           high_availability=None, zone=None, standby_availability_zone=None,
                           geo_redundant_backup=None, byok_identity=None, byok_key=None,
                           active_directory_auth=None, password_auth=None, yes=False):

    # Generate missing parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'postgres')

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability_with_location,
        cf_availability_without_location=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    server_name = server_name.lower()

    pg_arguments_validator(db_context,
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
                           version=version,
                           geo_redundant_backup=geo_redundant_backup,
                           byok_identity=byok_identity,
                           byok_key=byok_key)

    server_result = firewall_id = None

    network, start_ip, end_ip = flexible_server_provision_network_resource(cmd=cmd,
                                                                           resource_group_name=resource_group_name,
                                                                           server_name=server_name,
                                                                           location=location,
                                                                           db_context=db_context,
                                                                           private_dns_zone_arguments=private_dns_zone_arguments,
                                                                           public_access=public_access,
                                                                           vnet=vnet,
                                                                           subnet=subnet,
                                                                           vnet_address_prefix=vnet_address_prefix,
                                                                           subnet_address_prefix=subnet_address_prefix,
                                                                           yes=yes)

    storage = postgresql_flexibleservers.models.Storage(storage_size_gb=storage_gb)

    backup = postgresql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
                                                      geo_redundant_backup=geo_redundant_backup)

    sku = postgresql_flexibleservers.models.Sku(name=sku_name, tier=tier)

    high_availability = postgresql_flexibleservers.models.HighAvailability(mode=high_availability,
                                                                           standby_availability_zone=standby_availability_zone)

    administrator_login_password = generate_password(administrator_login_password)

    identity, data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                   byok_identity=byok_identity,
                                                                   byok_key=byok_key)

    auth_config = postgresql_flexibleservers.models.AuthConfig(active_directory_auth_enabled=(active_directory_auth == 'Enabled'),
                                                               password_auth_enabled=(password_auth == 'Enabled'))

    # Create postgresql
    # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
    server_result = _create_server(db_context, cmd, resource_group_name, server_name,
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
                                   availability_zone=zone,
                                   identity=identity,
                                   data_encryption=data_encryption,
                                   auth_config=auth_config)

    # Adding firewall rule
    if start_ip != -1 and end_ip != -1:
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
    subnet_id = network.delegated_subnet_resource_id

    logger.warning('Make a note of your password. If you forget, you would have to '
                   'reset your password with "az postgres flexible-server update -n %s -g %s -p <new-password>".',
                   server_name, resource_group_name)
    logger.warning('Try using \'az postgres flexible-server connect\' command to test out connection.')

    _update_local_contexts(cmd, server_name, resource_group_name, database_name, location, user)

    return _form_response(user, sku, loc, server_id, host, version,
                          administrator_login_password if administrator_login_password is not None else '*****',
                          _create_postgresql_connection_string(host, user, administrator_login_password), database_name, firewall_id,
                          subnet_id)


def flexible_server_restore(cmd, client,
                            resource_group_name, server_name,
                            source_server, restore_point_in_time=None, zone=None, no_wait=False,
                            subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                            private_dns_zone_arguments=None, geo_redundant_backup=None, byok_identity=None,
                            byok_key=None, yes=False):

    server_name = server_name.lower()

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server_id = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=RESOURCE_PROVIDER,
                type='flexibleServers',
                name=source_server)
        else:
            raise ValueError('The provided source server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    restore_point_in_time = validate_and_format_restore_point_in_time(restore_point_in_time)

    try:
        id_parts = parse_resource_id(source_server_id)
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])

        location = ''.join(source_server_object.location.lower().split())

        db_context = DbContext(
            cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
            cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability_with_location,
            cf_availability_without_location=cf_postgres_check_resource_availability,
            cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
            logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)
        validate_server_name(db_context, server_name, 'Microsoft.DBforPostgreSQL/flexibleServers')

        pg_byok_validator(byok_identity, byok_key)

        parameters = postgresql_flexibleservers.models.Server(
            location=location,
            point_in_time_utc=restore_point_in_time,
            source_server_resource_id=source_server_id,  # this should be the source server name, not id
            create_mode="PointInTimeRestore",
            availability_zone=zone
        )

        if source_server_object.network.public_network_access == 'Disabled' and any((vnet, subnet)):
            parameters.network, _, _ = flexible_server_provision_network_resource(cmd=cmd,
                                                                                  resource_group_name=resource_group_name,
                                                                                  server_name=server_name,
                                                                                  location=location,
                                                                                  db_context=db_context,
                                                                                  private_dns_zone_arguments=private_dns_zone_arguments,
                                                                                  public_access='Disabled',
                                                                                  vnet=vnet,
                                                                                  subnet=subnet,
                                                                                  vnet_address_prefix=vnet_address_prefix,
                                                                                  subnet_address_prefix=subnet_address_prefix,
                                                                                  yes=yes)
        else:
            parameters.network = source_server_object.network

        parameters.backup = postgresql_flexibleservers.models.Backup(geo_redundant_backup=geo_redundant_backup)

        parameters.identity, parameters.data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                                             byok_identity=byok_identity,
                                                                                             byok_key=byok_key)

    except Exception as e:
        raise ResourceNotFoundError(e)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


def flexible_server_update_custom_func(cmd, client, instance,
                                       sku_name=None,
                                       tier=None,
                                       storage_gb=None,
                                       backup_retention=None,
                                       administrator_login_password=None,
                                       high_availability=None,
                                       standby_availability_zone=None,
                                       maintenance_window=None,
                                       byok_identity=None, byok_key=None,
                                       active_directory_auth=None, password_auth=None,
                                       tags=None):

    # validator
    location = ''.join(instance.location.lower().split())
    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability_with_location,
        cf_availability_without_location=cf_postgres_check_resource_availability,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    pg_arguments_validator(db_context,
                           location=location,
                           tier=tier,
                           sku_name=sku_name,
                           storage_gb=storage_gb,
                           high_availability=high_availability,
                           zone=instance.availability_zone,
                           standby_availability_zone=standby_availability_zone,
                           byok_identity=byok_identity,
                           byok_key=byok_key,
                           instance=instance)

    server_module_path = instance.__module__
    module = import_module(server_module_path)
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name

    if tier:
        instance.sku.tier = tier

    if storage_gb:
        instance.storage.storage_size_gb = storage_gb

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
        instance.maintenance_window.day_of_week = day_of_week
        instance.maintenance_window.start_hour = start_hour
        instance.maintenance_window.start_minute = start_minute
        instance.maintenance_window.custom_window = custom_window

    identity, data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                   byok_identity=byok_identity,
                                                                   byok_key=byok_key)

    auth_config = instance.auth_config
    if active_directory_auth:
        auth_config.active_directory_auth_enabled = active_directory_auth == 'Enabled'
    if password_auth:
        auth_config.password_auth_enabled = password_auth == 'Enabled'

    params = ServerForUpdate(sku=instance.sku,
                             storage=instance.storage,
                             backup=instance.backup,
                             administrator_login_password=administrator_login_password,
                             maintenance_window=instance.maintenance_window,
                             identity=identity,
                             data_encryption=data_encryption,
                             auth_config=auth_config,
                             tags=tags)

    # High availability can't be updated with existing properties
    high_availability_param = postgresql_flexibleservers.models.HighAvailability()
    if high_availability:
        if high_availability.lower() != "disabled":
            high_availability_param.mode = high_availability
            if standby_availability_zone:
                high_availability_param.standby_availability_zone = standby_availability_zone
        else:
            high_availability_param.mode = high_availability

        params.high_availability = high_availability_param

    return params


def flexible_server_restart(cmd, client, resource_group_name, server_name, fail_over=None):
    instance = client.get(resource_group_name, server_name)
    if fail_over is not None and instance.high_availability.mode != "ZoneRedundant":
        raise ArgumentUsageError("Failing over can only be triggered for zone redundant servers.")

    if fail_over is not None:
        if fail_over.lower() not in ['planned', 'forced']:
            raise InvalidArgumentValueError("Allowed failover parameters are 'Planned' and 'Forced'.")
        if fail_over.lower() == 'planned':
            fail_over = 'plannedFailover'
        elif fail_over.lower() == 'forced':
            fail_over = 'forcedFailover'
        parameters = postgresql_flexibleservers.models.RestartParameter(restart_with_failover=True,
                                                                        failover_mode=fail_over)
    else:
        parameters = postgresql_flexibleservers.models.RestartParameter(restart_with_failover=False)

    return resolve_poller(
        client.begin_restart(resource_group_name, server_name, parameters), cmd.cli_ctx, 'PostgreSQL Server Restart')


def flexible_server_delete(cmd, client, resource_group_name, server_name, yes=False):
    result = None
    if not yes:
        user_confirmation(
            "Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name,
                                                                                              resource_group_name), yes=yes)
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


def flexible_replica_create(cmd, client, resource_group_name, source_server, replica_name, zone=None,
                            location=None, vnet=None, vnet_address_prefix=None, subnet=None,
                            subnet_address_prefix=None, private_dns_zone_arguments=None, no_wait=False,
                            byok_identity=None, byok_key=None, yes=False):
    replica_name = replica_name.lower()

    if not is_valid_resource_id(source_server):
        if _is_resource_name(source_server):
            source_server_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                           resource_group=resource_group_name,
                                           namespace='Microsoft.DBforPostgreSQL',
                                           type='flexibleServers',
                                           name=source_server)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server_id)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except Exception as e:
        raise ResourceNotFoundError(e)

    validate_postgres_replica(cmd, source_server_object)

    if not location:
        location = source_server_object.location
    if not zone:
        zone = source_server_object.availability_zone

    location = ''.join(location.lower().split())

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability_with_location,
        cf_availability_without_location=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)
    validate_server_name(db_context, replica_name, 'Microsoft.DBforPostgreSQL/flexibleServers')

    pg_byok_validator(byok_identity, byok_key)

    parameters = postgresql_flexibleservers.models.Server(
        source_server_resource_id=source_server_id,
        location=location,
        availability_zone=zone,
        create_mode="Replica")

    if source_server_object.network.public_network_access == 'Disabled' and any((vnet, subnet)):
        parameters.network, _, _ = flexible_server_provision_network_resource(cmd=cmd,
                                                                              resource_group_name=resource_group_name,
                                                                              server_name=replica_name,
                                                                              location=location,
                                                                              db_context=db_context,
                                                                              private_dns_zone_arguments=private_dns_zone_arguments,
                                                                              public_access='Disabled',
                                                                              vnet=vnet,
                                                                              subnet=subnet,
                                                                              vnet_address_prefix=vnet_address_prefix,
                                                                              subnet_address_prefix=subnet_address_prefix,
                                                                              yes=yes)
    else:
        parameters.network = source_server_object.network

    parameters.identity, parameters.data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                                         byok_identity=byok_identity,
                                                                                         byok_key=byok_key)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, replica_name, parameters)


def flexible_server_georestore(cmd, client, resource_group_name, server_name, source_server, location, zone=None,
                               vnet=None, vnet_address_prefix=None, subnet=None, subnet_address_prefix=None,
                               private_dns_zone_arguments=None, geo_redundant_backup=None, no_wait=False, yes=False):
    server_name = server_name.lower()

    if not is_valid_resource_id(source_server):
        if _is_resource_name(source_server):
            source_server_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                           resource_group=resource_group_name,
                                           namespace='Microsoft.DBforPostgreSQL',
                                           type='flexibleServers',
                                           name=source_server)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server_id)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except Exception as e:
        raise ResourceNotFoundError(e)

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability_with_location,
        cf_availability_without_location=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    validate_server_name(db_context, server_name, 'Microsoft.DBforPostgreSQL/flexibleServers')
    validate_georestore_network(source_server_object, None, vnet, subnet, 'postgres')

    parameters = postgresql_flexibleservers.models.Server(
        point_in_time_utc=get_current_time(),
        location=location,
        source_server_resource_id=source_server_id,
        create_mode="GeoRestore",
        availability_zone=zone
    )

    if source_server_object.network.public_network_access == 'Disabled':
        parameters.network, _, _ = flexible_server_provision_network_resource(cmd=cmd,
                                                                              resource_group_name=resource_group_name,
                                                                              server_name=server_name,
                                                                              location=location,
                                                                              db_context=db_context,
                                                                              private_dns_zone_arguments=private_dns_zone_arguments,
                                                                              public_access='Disabled',
                                                                              vnet=vnet,
                                                                              subnet=subnet,
                                                                              vnet_address_prefix=vnet_address_prefix,
                                                                              subnet_address_prefix=subnet_address_prefix,
                                                                              yes=yes)

    parameters.backup = postgresql_flexibleservers.models.Backup(geo_redundant_backup=geo_redundant_backup)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


def flexible_replica_stop(client, resource_group_name, server_name):
    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if server_object.replication_role is not None and "replica" not in server_object.replication_role.lower():
        raise CLIError('Server {} is not a replica server.'.format(server_name))

    params = postgresql_flexibleservers.models.ServerForUpdate(
        replication_role='None')

    return client.begin_update(resource_group_name, server_name, params)


def _create_server(db_context, cmd, resource_group_name, server_name, tags, location, sku, administrator_login, administrator_login_password,
                   storage, backup, network, version, high_availability, availability_zone, identity, data_encryption, auth_config):
    logging_name, server_client = db_context.logging_name, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/postgres-pricing for pricing details', server_name, sku.name)

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
        availability_zone=availability_zone,
        identity=identity,
        data_encryption=data_encryption,
        auth_config=auth_config,
        create_mode="Create")

    return resolve_poller(
        server_client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def _create_database(db_context, cmd, resource_group_name, server_name, database_name):
    # check for existing database, create if not
    cf_db, logging_name = db_context.cf_db, db_context.logging_name
    database_client = cf_db(cmd.cli_ctx, None)

    logger.warning('Creating %s database \'%s\'...', logging_name, database_name)
    parameters = {
        'name': database_name,
        'charset': 'utf8',
        'collation': 'en_US.utf8'
    }
    resolve_poller(
        database_client.begin_create(resource_group_name, server_name, database_name, parameters), cmd.cli_ctx,
        '{} Database Create/Update'.format(logging_name))


def database_create_func(client, resource_group_name, server_name, database_name=None, charset=None, collation=None):

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


# Custom functions for identity
def flexible_server_identity_assign(cmd, client, resource_group_name, server_name, identities):
    identities_map = {}
    for identity in identities:
        identities_map[identity] = {}

    parameters = {
        'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
            user_assigned_identities=identities_map,
            type="UserAssigned")}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Adding identities to server {}'.format(server_name)
    )

    return result.identity


def flexible_server_identity_remove(cmd, client, resource_group_name, server_name, identities):
    instance = client.get(resource_group_name, server_name)

    if instance.data_encryption:
        primary_id = instance.data_encryption.primary_user_assigned_identity_id

        if primary_id and primary_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for data encryption.".format(primary_id))

    identities_map = {}
    for identity in identities:
        identities_map[identity] = None

    if not (instance.identity and instance.identity.user_assigned_identities) or \
       all(key.lower() in [identity.lower() for identity in identities] for key in instance.identity.user_assigned_identities.keys()):
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                type="None")}
    else:
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                user_assigned_identities=identities_map,
                type="UserAssigned")}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Removing identities from server {}'.format(server_name)
    )

    return result.identity or postgresql_flexibleservers.models.UserAssignedIdentity(type="SystemAssigned")


def flexible_server_identity_list(client, resource_group_name, server_name):
    server = client.get(resource_group_name, server_name)
    return server.identity or postgresql_flexibleservers.models.UserAssignedIdentity(type="SystemAssigned")


def flexible_server_identity_show(client, resource_group_name, server_name, identity):
    server = client.get(resource_group_name, server_name)

    for key, value in server.identity.user_assigned_identities.items():
        if key.lower() == identity.lower():
            return value

    raise CLIError("Identity '{}' does not exist in server {}.".format(identity, server_name))


# Custom functions for ad-admin
def flexible_server_ad_admin_set(cmd, client, resource_group_name, server_name, login, sid, principal_type=None, no_wait=False):
    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot create an AD admin on a server with replication role. Use the primary server instead.")

    parameters = {
        'principal_name': login,
        'tenant_id': get_tenant_id(),
        'principal_type': principal_type
    }

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, sid, parameters)


def flexible_server_ad_admin_delete(cmd, client, resource_group_name, server_name, sid, no_wait=False):
    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot delete an AD admin on a server with replication role. Use the primary server instead.")

    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, server_name, sid)


def flexible_server_ad_admin_list(client, resource_group_name, server_name):
    return client.list_by_server(
        resource_group_name=resource_group_name,
        server_name=server_name)


def flexible_server_ad_admin_show(client, resource_group_name, server_name, sid):
    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        object_id=sid)


def flexible_server_provision_network_resource(cmd, resource_group_name, server_name,
                                               location, db_context, private_dns_zone_arguments=None, public_access=None,
                                               vnet=None, subnet=None, vnet_address_prefix=None, subnet_address_prefix=None, yes=False):
    start_ip = -1
    end_ip = -1
    network = postgresql_flexibleservers.models.Network()

    if subnet is not None or vnet is not None:
        subnet_id = prepare_private_network(cmd,
                                            resource_group_name,
                                            server_name,
                                            vnet=vnet,
                                            subnet=subnet,
                                            location=location,
                                            delegation_service_name=DELEGATION_SERVICE_NAME,
                                            vnet_address_pref=vnet_address_prefix,
                                            subnet_address_pref=subnet_address_prefix,
                                            yes=yes)
        private_dns_zone_id = prepare_private_dns_zone(db_context,
                                                       'PostgreSQL',
                                                       resource_group_name,
                                                       server_name,
                                                       private_dns_zone=private_dns_zone_arguments,
                                                       subnet_id=subnet_id,
                                                       location=location,
                                                       yes=yes)
        network.delegated_subnet_resource_id = subnet_id
        network.private_dns_zone_arm_resource_id = private_dns_zone_id
    elif subnet is None and vnet is None and private_dns_zone_arguments is not None:
        raise RequiredArgumentMissingError("Private DNS zone can only be used with private access setting. Use vnet or/and subnet parameters.")
    else:
        start_ip, end_ip = prepare_public_network(public_access, yes=yes)

    return network, start_ip, end_ip


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


def _form_response(username, sku, location, server_id, host, version, password, connection_string, database_name, firewall_id=None,
                   subnet_id=None):

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


def _update_local_contexts(cmd, server_name, resource_group_name, database_name, location, user):
    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'server_name',
                                      server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'administrator_login',
                                      user)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'database_name',
                                      database_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([ALL], 'location',
                                      location)  # Setting the location in the local context
        cmd.cli_ctx.local_context.set([ALL], 'resource_group_name', resource_group_name)


# pylint: disable=too-many-instance-attributes, too-few-public-methods, useless-object-inheritance
class DbContext(object):
    def __init__(self, cmd=None, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 cf_availability=None, cf_availability_without_location=None, cf_private_dns_zone_suffix=None,
                 command_group=None, server_client=None, location=None):
        self.cmd = cmd
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_availability = cf_availability
        self.cf_availability_without_location = cf_availability_without_location
        self.cf_private_dns_zone_suffix = cf_private_dns_zone_suffix
        self.logging_name = logging_name
        self.cf_db = cf_db
        self.command_group = command_group
        self.server_client = server_client
        self.location = location
