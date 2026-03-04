# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from functools import cmp_to_key
from importlib import import_module
from urllib.parse import quote
from knack.log import get_logger
from knack.prompting import prompt
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.local_context import ALL
from azure.cli.core.util import CLIError, sdk_no_wait, user_confirmation
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id, resource_id
from .._client_factory import (
    cf_postgres_check_resource_availability,
    cf_postgres_flexible_admin,
    cf_postgres_flexible_config,
    cf_postgres_flexible_db,
    cf_postgres_flexible_firewall_rules,
    cf_postgres_flexible_private_dns_zone_suffix_operations,
    get_postgresql_flexible_management_client)
from .._db_context import DbContext
from ..utils._flexible_server_location_capabilities_util import (
    get_postgres_location_capability_info,
    get_postgres_server_capability_info)
from ..utils._flexible_server_util import (
    _is_resource_name,
    build_identity_and_data_encryption,
    generate_missing_parameters,
    generate_password,
    get_current_time,
    get_postgres_skus,
    get_postgres_tiers,
    parse_maintenance_window,
    resolve_poller)
from ..utils.validators import (
    check_resource_group,
    compare_sku_names,
    pg_arguments_validator,
    pg_byok_validator,
    pg_restore_validator,
    validate_and_format_restore_point_in_time,
    validate_citus_cluster,
    validate_georestore_network,
    validate_resource_group,
    validate_server_name)
from .firewall_rule_commands import create_firewall_rule
from .microsoft_entra_commands import _create_admin
from .network_commands import (
    flexible_server_provision_network_resource,
    prepare_private_dns_zone)

logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
POSTGRES_DB_NAME = 'postgres'
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
                           storage_gb=None, version=None, microsoft_entra_auth=None,
                           admin_name=None, admin_id=None, admin_type=None,
                           password_auth=None, administrator_login=None, administrator_login_password=None,
                           tags=None, subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                           private_dns_zone_arguments=None, public_access=None,
                           high_availability=None, zonal_resiliency=None, allow_same_zone=False,
                           zone=None, standby_availability_zone=None,
                           geo_redundant_backup=None, byok_identity=None, byok_key=None, backup_byok_identity=None, backup_byok_key=None,
                           auto_grow=None, performance_tier=None,
                           storage_type=None, iops=None, throughput=None, create_cluster=None, cluster_size=None, database_name=None, yes=False):

    if not check_resource_group(resource_group_name):
        resource_group_name = None

    # Generate missing parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'postgres')

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    server_name = server_name.lower()
    high_availability_mode = high_availability

    if (sku_name is None) or (version is None) or \
       (zonal_resiliency is not None and zonal_resiliency.lower() != 'disabled'):
        list_location_capability_info = get_postgres_location_capability_info(cmd, location)

        # set sku_name from capability API
        if sku_name is None:
            tiers = [item.lower() for item in get_postgres_tiers(list_location_capability_info['sku_info'])]
            try:
                sku_info = list_location_capability_info['sku_info']
                skus = list(get_postgres_skus(sku_info, tier.lower()))
                skus = sorted(skus, key=cmp_to_key(compare_sku_names))
                sku_name = skus[0]
            except:
                raise CLIError('Incorrect value for --tier. Allowed values : {}'.format(tiers))
        # default to the latest version
        if version is None:
            supported_server_versions = sorted(list_location_capability_info['supported_server_versions'])
            version = supported_server_versions[-1]
        # set high availability from capability API
        if (zonal_resiliency is not None and zonal_resiliency.lower() != 'disabled'):
            single_az = list_location_capability_info['single_az']
            high_availability_mode = 'SameZone' if single_az and allow_same_zone else 'ZoneRedundant'

    pg_arguments_validator(db_context,
                           server_name=server_name,
                           location=location,
                           tier=tier, sku_name=sku_name,
                           storage_gb=storage_gb,
                           auto_grow=auto_grow,
                           storage_type=storage_type,
                           iops=iops, throughput=throughput,
                           high_availability=high_availability,
                           zonal_resiliency=zonal_resiliency,
                           allow_same_zone=allow_same_zone,
                           standby_availability_zone=standby_availability_zone,
                           zone=zone,
                           subnet=subnet,
                           public_access=public_access,
                           version=version,
                           geo_redundant_backup=geo_redundant_backup,
                           byok_identity=byok_identity,
                           byok_key=byok_key,
                           backup_byok_identity=backup_byok_identity,
                           backup_byok_key=backup_byok_key,
                           performance_tier=performance_tier,
                           create_cluster=create_cluster,
                           password_auth=password_auth, microsoft_entra_auth=microsoft_entra_auth,
                           admin_name=admin_name, admin_id=admin_id, admin_type=admin_type,)

    cluster = None
    if create_cluster == 'ElasticCluster':
        cluster_size = cluster_size if cluster_size else 2
        cluster = postgresql_flexibleservers.models.Cluster(cluster_size=cluster_size, default_database_name=database_name if database_name else POSTGRES_DB_NAME)

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

    storage = postgresql_flexibleservers.models.Storage(storage_size_gb=storage_gb, auto_grow=auto_grow, tier=performance_tier, type=storage_type, iops=iops, throughput=throughput)

    backup = postgresql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
                                                      geo_redundant_backup=geo_redundant_backup)

    sku = postgresql_flexibleservers.models.Sku(name=sku_name, tier=tier)

    high_availability = postgresql_flexibleservers.models.HighAvailability(mode=high_availability_mode,
                                                                           standby_availability_zone=standby_availability_zone)

    is_password_auth_enabled = bool(password_auth is not None and password_auth.lower() == 'enabled')
    is_microsoft_entra_auth_enabled = bool(microsoft_entra_auth is not None and microsoft_entra_auth.lower() == 'enabled')
    if is_password_auth_enabled:
        administrator_login_password = generate_password(administrator_login_password)

    identity, data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                   byok_identity=byok_identity,
                                                                   byok_key=byok_key,
                                                                   backup_byok_identity=backup_byok_identity,
                                                                   backup_byok_key=backup_byok_key)

    auth_config = postgresql_flexibleservers.models.AuthConfig(active_directory_auth='Enabled' if is_microsoft_entra_auth_enabled else 'Disabled',
                                                               password_auth=password_auth)

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
                                   auth_config=auth_config,
                                   cluster=cluster)

    # Add Microsoft Entra Admin
    if is_microsoft_entra_auth_enabled and admin_name is not None or admin_id is not None:
        server_admin_client = cf_postgres_flexible_admin(cmd.cli_ctx, '_')
        logger.warning("Add Microsoft Entra Admin '%s'.", admin_name)
        _create_admin(server_admin_client, resource_group_name, server_name, admin_name, admin_id, admin_type)

    # Adding firewall rule
    if start_ip != -1 and end_ip != -1:
        firewall_id = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

    user = server_result.administrator_login if is_password_auth_enabled else '<user>'
    password = administrator_login_password if is_password_auth_enabled else '<password>'
    server_id = server_result.id
    loc = server_result.location
    version = server_result.version
    sku = server_result.sku.name
    host = server_result.fully_qualified_domain_name
    subnet_id = None if network is None else network.delegated_subnet_resource_id

    if is_password_auth_enabled:
        logger.warning('Make a note of your password. If you forget, you would have to '
                       'reset your password with "az postgres flexible-server update -n %s -g %s -p <new-password>".',
                       server_name, resource_group_name)
    logger.warning('Try using \'az postgres flexible-server connect\' command to test out connection.')

    _update_local_contexts(cmd, server_name, resource_group_name, location, user)

    return _form_response(user, sku, loc, server_id, host, version, password,
                          firewall_id, subnet_id, is_password_auth_enabled, is_microsoft_entra_auth_enabled, admin_name)


def _create_server(db_context, cmd, resource_group_name, server_name, tags, location, sku, administrator_login, administrator_login_password,
                   storage, backup, network, version, high_availability, availability_zone, identity, data_encryption, auth_config, cluster):
    validate_resource_group(resource_group_name)

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
        cluster=cluster,
        create_mode="Create")

    return resolve_poller(
        server_client.begin_create_or_update(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def _update_local_contexts(cmd, server_name, resource_group_name, location, user):
    validate_resource_group(resource_group_name)

    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'server_name',
                                      server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'administrator_login',
                                      user)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set(['postgres flexible-server'], 'database_name',
                                      POSTGRES_DB_NAME)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([ALL], 'location',
                                      location)  # Setting the location in the local context
        cmd.cli_ctx.local_context.set([ALL], 'resource_group_name', resource_group_name)


def _form_response(username, sku, location, server_id, host, version, password, firewall_id=None,
                   subnet_id=None, is_password_auth=True, is_microsoft_entra_auth_enabled=False, microsoft_admin=None):

    connection_kwargs = {
        'user': username if username is not None else '{user}',
        'host': host,
        'password': password if password is not None else '{password}',
        'database': POSTGRES_DB_NAME,
    }
    output = {
        'host': host,
        'username': username if is_password_auth else None,
        'password': password if is_password_auth else None,
        'skuname': sku,
        'location': location,
        'id': server_id,
        'version': version,
        'databaseName': POSTGRES_DB_NAME,
        'connectionString': 'postgresql://{user}:{password}@{host}/{database}?sslmode=require'.format(**connection_kwargs)
    }
    if is_microsoft_entra_auth_enabled:
        user = quote(microsoft_admin) if microsoft_admin else '<admin>'
        connection_kwargs = {
            'user': user,
            'host': host,
            'database': POSTGRES_DB_NAME,
        }
        output['admin'] = microsoft_admin
        output['connectionStringMicrosoftEntra'] = 'postgresql://{user}:<access-token>@{host}/{database}?sslmode=require'.format(**connection_kwargs)
    if firewall_id is not None:
        output['firewallName'] = firewall_id
    if subnet_id is not None:
        output['subnetId'] = subnet_id
    return output


def flexible_server_restore(cmd, client,
                            resource_group_name, server_name,
                            source_server, restore_point_in_time=None, zone=None, no_wait=False,
                            subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                            private_dns_zone_arguments=None, geo_redundant_backup=None,
                            byok_identity=None, byok_key=None, backup_byok_identity=None, backup_byok_key=None, storage_type=None, yes=False):

    server_name = server_name.lower()

    validate_resource_group(resource_group_name)

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
        source_subscription_id = id_parts['subscription']
        postgres_source_client = get_postgresql_flexible_management_client(cmd.cli_ctx, source_subscription_id)
        source_server_object = postgres_source_client.servers.get(id_parts['resource_group'], id_parts['name'])

        location = ''.join(source_server_object.location.lower().split())

        db_context = DbContext(
            cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
            cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
            cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
            logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)
        validate_server_name(db_context, server_name, 'Microsoft.DBforPostgreSQL/flexibleServers')

        pg_byok_validator(byok_identity, byok_key, backup_byok_identity, backup_byok_key, geo_redundant_backup)

        pg_restore_validator(source_server_object.sku.tier, storage_type=storage_type)
        storage = postgresql_flexibleservers.models.Storage(type=storage_type if source_server_object.storage.type != "PremiumV2_LRS" else None)

        parameters = postgresql_flexibleservers.models.Server(
            location=location,
            point_in_time_utc=restore_point_in_time,
            source_server_resource_id=source_server_id,  # this should be the source server name, not id
            create_mode="PointInTimeRestore",
            availability_zone=zone,
            storage=storage
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
                                                                                             byok_key=byok_key,
                                                                                             backup_byok_identity=backup_byok_identity,
                                                                                             backup_byok_key=backup_byok_key)

    except Exception as e:
        raise ResourceNotFoundError(e)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, server_name, parameters)


# pylint: disable=too-many-branches
def flexible_server_update_custom_func(cmd, client, instance,
                                       sku_name=None, tier=None,
                                       storage_gb=None,
                                       backup_retention=None,
                                       administrator_login_password=None,
                                       high_availability=None,
                                       zonal_resiliency=None,
                                       allow_same_zone=False,
                                       standby_availability_zone=None,
                                       maintenance_window=None,
                                       byok_identity=None, byok_key=None,
                                       backup_byok_identity=None, backup_byok_key=None,
                                       microsoft_entra_auth=None, password_auth=None,
                                       private_dns_zone_arguments=None,
                                       public_access=None,
                                       tags=None,
                                       auto_grow=None,
                                       performance_tier=None,
                                       iops=None, throughput=None,
                                       cluster_size=None, yes=False):

    # validator
    location = ''.join(instance.location.lower().split())
    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    pg_arguments_validator(db_context,
                           location=location,
                           tier=tier,
                           sku_name=sku_name,
                           storage_gb=storage_gb,
                           auto_grow=auto_grow,
                           iops=iops,
                           throughput=throughput,
                           high_availability=high_availability,
                           zonal_resiliency=zonal_resiliency,
                           allow_same_zone=allow_same_zone,
                           zone=instance.availability_zone,
                           standby_availability_zone=standby_availability_zone,
                           byok_identity=byok_identity,
                           byok_key=byok_key,
                           backup_byok_identity=backup_byok_identity,
                           backup_byok_key=backup_byok_key,
                           performance_tier=performance_tier,
                           cluster_size=cluster_size, instance=instance)

    server_module_path = instance.__module__
    module = import_module(server_module_path)
    ServerForPatch = getattr(module, 'ServerForPatch')

    server_id_parts = parse_resource_id(instance.id)
    resource_group_name = server_id_parts['resource_group']
    server_name = server_id_parts['name']

    if public_access:
        instance.network.public_network_access = public_access

    if private_dns_zone_arguments:
        private_dns_zone_id = prepare_private_dns_zone(db_context,
                                                       resource_group_name,
                                                       server_name,
                                                       private_dns_zone=private_dns_zone_arguments,
                                                       subnet_id=instance.network.delegated_subnet_resource_id,
                                                       location=location,
                                                       yes=yes)
        instance.network.private_dns_zone_arm_resource_id = private_dns_zone_id

    _confirm_restart_server(instance, sku_name, storage_gb, yes)

    if sku_name:
        instance.sku.name = sku_name

    if tier:
        instance.sku.tier = tier

    if storage_gb:
        instance.storage.storage_size_gb = storage_gb

    if auto_grow:
        instance.storage.auto_grow = auto_grow

    instance.storage.tier = performance_tier if performance_tier else None

    if instance.storage.type == "PremiumV2_LRS":
        instance.storage.tier = None

        if sku_name or storage_gb:
            logger.warning("You are changing the compute and/or storage size of the server. "
                           "The server will be restarted for this operation and you will see a short downtime.")

        if iops:
            instance.storage.iops = iops

        if throughput:
            instance.storage.throughput = throughput
    else:
        instance.storage.type = None
        instance.storage.iops = None
        instance.storage.throughput = None

    if backup_retention:
        instance.backup.backup_retention_days = backup_retention

    if maintenance_window:
        if maintenance_window.lower() == "disabled":
            # if disabled is pass in reset to default values
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
                                                                   byok_key=byok_key,
                                                                   backup_byok_identity=backup_byok_identity,
                                                                   backup_byok_key=backup_byok_key,
                                                                   instance=instance)

    auth_config = instance.auth_config
    administrator_login = instance.administrator_login if instance.administrator_login else None
    if microsoft_entra_auth:
        auth_config.active_directory_auth = microsoft_entra_auth
    if password_auth:
        administrator_login, administrator_login_password = _update_login(server_name, resource_group_name, auth_config,
                                                                          password_auth, administrator_login, administrator_login_password)
        auth_config.password_auth = password_auth

    if cluster_size:
        instance.cluster.cluster_size = cluster_size

    params = ServerForPatch(sku=instance.sku,
                            storage=instance.storage,
                            backup=instance.backup,
                            administrator_login=administrator_login,
                            administrator_login_password=administrator_login_password,
                            availability_zone=instance.availability_zone,
                            maintenance_window=instance.maintenance_window,
                            network=instance.network,
                            identity=identity,
                            data_encryption=data_encryption,
                            auth_config=auth_config,
                            cluster=instance.cluster,
                            tags=tags)

    # High availability can't be updated with existing properties
    high_availability_param = postgresql_flexibleservers.models.HighAvailability()
    if zonal_resiliency is not None:
        if zonal_resiliency.lower() == 'disabled':
            high_availability = 'Disabled'
        else:
            list_capability_info = get_postgres_server_capability_info(cmd, resource_group_name, server_name)
            single_az = list_capability_info['single_az']
            high_availability = 'SameZone' if single_az and allow_same_zone else 'ZoneRedundant'
    if high_availability:
        high_availability_param.mode = high_availability

        if high_availability.lower() != "disabled" and standby_availability_zone:
            high_availability_param.standby_availability_zone = standby_availability_zone

        # PG 11 and 12 will never receive fabric mirroring support. Ignite 2025 Fabric mirroring supported on 17. Skip this check for servers of these versions
        if high_availability.lower() != "disabled" and str(instance.version) not in ["11", "12", "17", "18"]:
            config_client = cf_postgres_flexible_config(cmd.cli_ctx, '_')
            fabric_mirror_status = config_client.get(resource_group_name, server_name, 'azure.fabric_mirror_enabled')
            if (fabric_mirror_status and fabric_mirror_status.value.lower() == 'on'):
                raise CLIError("High availability cannot be enabled while Fabric mirroring is Active. Please disable Fabric mirroring to enable high availability.")

        params.high_availability = high_availability_param

    return params


# Common functions used by other providers
def flexible_server_update_get(client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)

    return client.get(resource_group_name, server_name)


def flexible_server_update_set(client, resource_group_name, server_name, parameters):
    validate_resource_group(resource_group_name)

    return client.begin_update(resource_group_name, server_name, parameters)


def _update_login(server_name, resource_group_name, auth_config, password_auth, administrator_login, administrator_login_password):
    if auth_config.password_auth.lower() == 'disabled' and password_auth.lower() == 'enabled':
        administrator_login = administrator_login if administrator_login else prompt('Please enter administrator username for the server. Once set, it cannot be changed: ')
        if not administrator_login:
            raise CLIError('Administrator username is required for enabling password authentication.')
        if not administrator_login_password:
            administrator_login_password = generate_password(administrator_login_password)
            logger.warning('Make a note of password "%s". You can '
                           'reset your password with "az postgres flexible-server update -n %s -g %s -p <new-password>".',
                           administrator_login_password, server_name, resource_group_name)

    return administrator_login, administrator_login_password


# pylint: disable=chained-comparison
def _confirm_restart_server(instance, sku_name, storage_gb, yes):
    show_confirmation = False

    # check if sku_name is changed
    if sku_name and sku_name != instance.sku.name:
        show_confirmation = True

    # check if requested storage growth is crossing the 4096 threshold
    if storage_gb and storage_gb > 4096 and instance.storage.storage_size_gb <= 4096 and instance.storage.type == "":
        show_confirmation = True

    # check if storage_gb changed for PremiumV2_LRS
    if storage_gb and instance.storage.type == "PremiumV2_LRS" and instance.storage.storage_size_gb != storage_gb:
        show_confirmation = True

    if not yes and show_confirmation:
        user_confirmation("You are trying to change the compute or the size of storage assigned to your server in a way that \
            requires a server restart. During the restart, you'll experience some downtime of the server. Do you want to proceed?", yes=yes)


def flexible_server_delete(cmd, client, resource_group_name, server_name, yes=False):
    validate_resource_group(resource_group_name)
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
    validate_resource_group(resource_group_name)
    client = get_postgresql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def server_list_custom_func(client, resource_group_name=None, show_cluster=None):
    if not check_resource_group(resource_group_name):
        resource_group_name = None

    servers = client.list_by_subscription()

    if resource_group_name:
        servers = client.list_by_resource_group(resource_group_name)

    if show_cluster:
        servers = [s for s in servers if s.cluster is not None]
    else:
        servers = [s for s in servers if s.cluster is None]

    return servers


def flexible_list_skus(cmd, client, location):
    result = client.list(location)
    logger.warning('For prices please refer to https://aka.ms/postgres-pricing')
    return result


def flexible_server_georestore(cmd, client, resource_group_name, server_name, source_server, location, zone=None,
                               vnet=None, vnet_address_prefix=None, subnet=None, subnet_address_prefix=None,
                               private_dns_zone_arguments=None, geo_redundant_backup=None, no_wait=False, yes=False,
                               byok_identity=None, byok_key=None, backup_byok_identity=None, backup_byok_key=None, restore_point_in_time=None):
    validate_resource_group(resource_group_name)

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

    restore_point_in_time = validate_and_format_restore_point_in_time(restore_point_in_time)

    try:
        id_parts = parse_resource_id(source_server_id)
        validate_citus_cluster(cmd, id_parts['resource_group'], id_parts['name'])
        source_subscription_id = id_parts['subscription']
        postgres_source_client = get_postgresql_flexible_management_client(cmd.cli_ctx, source_subscription_id)
        source_server_object = postgres_source_client.servers.get(id_parts['resource_group'], id_parts['name'])
    except Exception as e:
        raise ResourceNotFoundError(e)

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    validate_server_name(db_context, server_name, 'Microsoft.DBforPostgreSQL/flexibleServers')
    if source_server_object.network.delegated_subnet_resource_id is not None:
        validate_georestore_network(source_server_object, None, vnet, subnet, 'postgres')

    pg_byok_validator(byok_identity, byok_key, backup_byok_identity, backup_byok_key, geo_redundant_backup)

    storage = postgresql_flexibleservers.models.Storage(type=None)

    parameters = postgresql_flexibleservers.models.Server(
        point_in_time_utc=restore_point_in_time,
        location=location,
        source_server_resource_id=source_server_id,
        create_mode="GeoRestore",
        availability_zone=zone,
        storage=storage
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

    parameters.identity, parameters.data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                                         byok_identity=byok_identity,
                                                                                         byok_key=byok_key,
                                                                                         backup_byok_identity=backup_byok_identity,
                                                                                         backup_byok_key=backup_byok_key)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, server_name, parameters)


def flexible_server_revivedropped(cmd, client, resource_group_name, server_name, source_server, location, zone=None,
                                  vnet=None, vnet_address_prefix=None, subnet=None, subnet_address_prefix=None,
                                  private_dns_zone_arguments=None, geo_redundant_backup=None, no_wait=False, yes=False,
                                  byok_identity=None, byok_key=None, backup_byok_identity=None, backup_byok_key=None):
    validate_resource_group(resource_group_name)

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

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)

    validate_server_name(db_context, server_name, 'Microsoft.DBforPostgreSQL/flexibleServers')

    pg_byok_validator(byok_identity, byok_key, backup_byok_identity, backup_byok_key, geo_redundant_backup)

    storage = postgresql_flexibleservers.models.Storage(type=None)

    parameters = postgresql_flexibleservers.models.Server(
        point_in_time_utc=get_current_time(),
        location=location,
        source_server_resource_id=source_server_id,
        create_mode="ReviveDropped",
        availability_zone=zone,
        storage=storage
    )

    if vnet is not None or vnet_address_prefix is not None or subnet is not None or \
       subnet_address_prefix is not None or private_dns_zone_arguments is not None:
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

    parameters.identity, parameters.data_encryption = build_identity_and_data_encryption(db_engine='postgres',
                                                                                         byok_identity=byok_identity,
                                                                                         byok_key=byok_key,
                                                                                         backup_byok_identity=backup_byok_identity,
                                                                                         backup_byok_key=backup_byok_key)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, server_name, parameters)


def flexible_server_connection_string(
        server_name='{server}',
        database_name='{database}',
        administrator_login='{login}',
        administrator_login_password='{password}',
        show_pg_bouncer=False):
    host = '{}.postgres.database.azure.com'.format(server_name)
    port = 5432
    if show_pg_bouncer is True:
        port = 6432

    return {
        'connectionStrings': _create_postgresql_connection_strings(host, administrator_login,
                                                                   administrator_login_password, database_name, port)
    }


def _create_postgresql_connection_strings(host, user, password, database, port):

    result = {
        'psql_cmd': "postgresql://{user}:{password}@{host}/{database}?sslmode=require",
        'ado.net': "Server={host};Database={database};Port={port};User Id={user};Password={password};Ssl Mode=Require;",
        'jdbc': "jdbc:postgresql://{host}:{port}/{database}?user={user}&password={password}&sslmode=require",
        'jdbc Spring': "spring.datasource.url=jdbc:postgresql://{host}:{port}/{database}  "
                       "spring.datasource.username={user}  "
                       "spring.datasource.password={password}",
        'node.js': "var conn= new Client({open_brace}host:'{host}', user:'{user}', password:'{password}', database:'{database}', port:{port}, ssl:{open_brace}ca:fs.readFileSync(\"{ca-cert filename}\"){close_brace}{close_brace});",
        'php': "pg_connect(\"host={host} port={port} dbname={database} user={user} password={password}\");",
        'python': "cnx = psycopg2.connect(user='{user}', password='{password}', host='{host}', "
                  "port={port}, database='{database}')",
        'ruby': "connection = PG::Connection.new(user => \"{user}\", password => \"{password}\", database => \"{database}\", host => \"{host}\", "
                "port => '{port}')",
    }

    connection_kwargs = {
        'host': host,
        'user': user,
        'password': password if password is not None else '{password}',
        'database': database,
        'port': port,
        'open_brace': '{',
        'close_brace': '}',
        'ca-cert filename': '{ca-cert filename}'
    }

    for k, v in result.items():
        result[k] = v.format(**connection_kwargs)
    return result
