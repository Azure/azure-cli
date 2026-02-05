# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from datetime import datetime, timedelta
import os
import json
from importlib import import_module
from functools import cmp_to_key
import re
from urllib.parse import quote
from urllib.request import urlretrieve
from dateutil.tz import tzutc   # pylint: disable=import-error
import uuid
from knack.log import get_logger
from knack.prompting import (
    prompt
)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.local_context import ALL
from azure.cli.core.util import CLIError, sdk_no_wait, user_confirmation
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.mgmt.core.tools import resource_id, is_valid_resource_id, parse_resource_id
from azure.cli.core.azclierror import BadRequestError, FileOperationError, MutuallyExclusiveArgumentError, RequiredArgumentMissingError, ArgumentUsageError, InvalidArgumentValueError, ValidationError
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from ._client_factory import cf_postgres_flexible_firewall_rules, get_postgresql_flexible_management_client, \
    cf_postgres_flexible_db, cf_postgres_check_resource_availability, cf_postgres_flexible_servers, \
    cf_postgres_flexible_private_dns_zone_suffix_operations, \
    cf_postgres_flexible_private_endpoint_connections, \
    cf_postgres_flexible_tuning_options, \
    cf_postgres_flexible_config, cf_postgres_flexible_admin
from ._flexible_server_util import generate_missing_parameters, resolve_poller, \
    generate_password, parse_maintenance_window, get_current_time, build_identity_and_data_encryption, \
    _is_resource_name, get_tenant_id, get_case_insensitive_key_value, get_enum_value_true_false, \
    get_postgres_tiers, get_postgres_skus
from ._flexible_server_location_capabilities_util import get_postgres_location_capability_info
from ._util import get_autonomous_tuning_settings_map
from .flexible_server_custom_common import create_firewall_rule
from .flexible_server_virtual_network import prepare_private_network, prepare_private_dns_zone, prepare_public_network
from .validators import pg_arguments_validator, validate_server_name, validate_and_format_restore_point_in_time, \
    validate_postgres_replica, validate_georestore_network, pg_byok_validator, validate_migration_runtime_server, \
    validate_resource_group, check_resource_group, validate_citus_cluster, validate_backup_name, \
    validate_virtual_endpoint_name_availability, validate_database_name, compare_sku_names, is_citus_cluster, pg_restore_validator

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
    admin = quote(admin_name) if admin_name else '<admin>'
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
                          _create_postgresql_connection_string(host, user, password),
                          firewall_id, subnet_id, is_password_auth_enabled, is_microsoft_entra_auth_enabled, admin_name,
                          _create_microsoft_entra_connection_string(host, POSTGRES_DB_NAME, admin))
# endregion create without args


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
            list_location_capability_info = get_postgres_location_capability_info(cmd, location)
            single_az = list_location_capability_info['single_az']
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


def flexible_server_restart(cmd, client, resource_group_name, server_name, fail_over=None):
    validate_resource_group(resource_group_name)
    instance = client.get(resource_group_name, server_name)
    if fail_over is not None and instance.high_availability.mode not in ("ZoneRedundant", "SameZone"):
        raise ArgumentUsageError("Failing over can only be triggered for zone redundant or same zone servers.")

    if fail_over is not None:
        validate_citus_cluster(cmd, resource_group_name, server_name)
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


def flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
    validate_resource_group(resource_group_name)
    parameter_value = value
    parameter_source = source
    try:
        # validate configuration name
        parameter = client.get(resource_group_name, server_name, configuration_name)

        # update the command with system default
        if parameter_value is None and parameter_source is None:
            parameter_value = parameter.default_value  # reset value to default

            # this should be 'system-default' but there is currently a bug in PG
            # this will reset source to be 'system-default' anyway
            parameter_source = "user-override"
        elif parameter_source is None:
            parameter_source = "user-override"
    except HttpResponseError as e:
        if parameter_value is None and parameter_source is None:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
        raise CLIError(str(e))

    parameters = postgresql_flexibleservers.models.Configuration(
        value=parameter_value,
        source=parameter_source
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


def flexible_list_skus(cmd, client, location):
    result = client.list(location)
    logger.warning('For prices please refer to https://aka.ms/postgres-pricing')
    return result


def flexible_replica_list_by_server(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)
    return client.list_by_server(resource_group_name, server_name)


def flexible_replica_create(cmd, client, resource_group_name, source_server, replica_name=None, name=None, zone=None,
                            location=None, vnet=None, vnet_address_prefix=None, subnet=None,
                            subnet_address_prefix=None, private_dns_zone_arguments=None, no_wait=False,
                            byok_identity=None, byok_key=None,
                            sku_name=None, tier=None,
                            storage_gb=None, performance_tier=None, yes=False, tags=None):
    validate_resource_group(resource_group_name)

    if replica_name is None and name is None:
        raise RequiredArgumentMissingError('the following arguments are required: --name')
    if replica_name is not None and name is not None:
        raise MutuallyExclusiveArgumentError('usage error: --name and --replica-name cannot be used together. Please use --name.')
    replica_name = replica_name.lower() if name is None else name.lower()

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

    if not location:
        location = source_server_object.location
    location = ''.join(location.lower().split())

    list_location_capability_info = get_postgres_location_capability_info(cmd, location)

    if tier is None and source_server_object is not None:
        tier = source_server_object.sku.tier
    if sku_name is None and source_server_object is not None:
        sku_name = source_server_object.sku.name
    if storage_gb is None and source_server_object is not None:
        storage_gb = source_server_object.storage.storage_size_gb
    validate_postgres_replica(cmd, tier, location, source_server_object,
                              sku_name, storage_gb, performance_tier, list_location_capability_info)

    if not zone:
        zone = _get_pg_replica_zone(list_location_capability_info['zones'],
                                    source_server_object.availability_zone,
                                    zone)

    db_context = DbContext(
        cmd=cmd, azure_sdk=postgresql_flexibleservers, cf_firewall=cf_postgres_flexible_firewall_rules,
        cf_db=cf_postgres_flexible_db, cf_availability=cf_postgres_check_resource_availability,
        cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
        logging_name='PostgreSQL', command_group='postgres', server_client=client, location=location)
    validate_server_name(db_context, replica_name, 'Microsoft.DBforPostgreSQL/flexibleServers')

    pg_byok_validator(byok_identity, byok_key)

    parameters = postgresql_flexibleservers.models.Server(
        tags=tags,
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

    parameters.sku = postgresql_flexibleservers.models.Sku(name=sku_name, tier=tier)

    parameters.storage = postgresql_flexibleservers.models.Storage(storage_size_gb=storage_gb, auto_grow=source_server_object.storage.auto_grow, tier=performance_tier)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, replica_name, parameters)


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


def flexible_replica_promote(cmd, client, resource_group_name, replica_name, promote_mode='standalone', promote_option='planned'):
    validate_resource_group(resource_group_name)
    if is_citus_cluster(cmd, resource_group_name, replica_name):
        # some settings validation
        if promote_mode.lower() == 'standalone':
            raise ValidationError("Standalone replica promotion on elastic cluster isn't currently supported. Please use 'switchover' instead.")
        if promote_option.lower() == 'planned':
            raise ValidationError("Planned replica promotion on elastic cluster isn't currently supported. Please use 'forced' instead.")

    try:
        server_object = client.get(resource_group_name, replica_name)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if server_object.replica.role is not None and "replica" not in server_object.replica.role.lower():
        raise CLIError('Server {} is not a replica server.'.format(replica_name))

    if promote_mode == "standalone":
        params = postgresql_flexibleservers.models.ServerForPatch(
            replica=postgresql_flexibleservers.models.Replica(
                role='None',
                promote_mode=promote_mode,
                promote_option=promote_option
            )
        )
    else:
        params = postgresql_flexibleservers.models.ServerForPatch(
            replica=postgresql_flexibleservers.models.Replica(
                role='Primary',
                promote_mode=promote_mode,
                promote_option=promote_option
            )
        )

    return client.begin_update(resource_group_name, replica_name, params)


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


def database_create_func(cmd, client, resource_group_name, server_name, database_name=None, charset=None, collation=None):
    validate_database_name(database_name)
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

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


# Custom functions for identity
def flexible_server_identity_update(cmd, client, resource_group_name, server_name, system_assigned):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)
    identity_type = server.identity.type if (server and server.identity and server.identity.type) else 'None'

    if system_assigned.lower() == 'enabled':
        # user wants to enable system-assigned identity
        if identity_type == 'None':
            # if user-assigned identity is not enabled, then enable system-assigned identity
            identity_type = 'SystemAssigned'
        elif identity_type == 'UserAssigned':
            # if user-assigned identity is enabled, then enable both system-assigned and user-assigned identity
            identity_type = 'SystemAssigned,UserAssigned'
    else:
        # check if fabric is enabled
        config_client = cf_postgres_flexible_config(cmd.cli_ctx, '_')
        fabric_mirror_status = config_client.get(resource_group_name, server_name, 'azure.fabric_mirror_enabled')
        if (fabric_mirror_status and fabric_mirror_status.value.lower() == 'on'):
            raise CLIError("On servers for which Fabric mirroring is enabled, system assigned managed identity cannot be disabled.")
        if server.data_encryption.type == 'AzureKeyVault':
            # if data encryption is enabled, then system-assigned identity cannot be disabled
            raise CLIError("On servers for which data encryption is based on customer managed key, system assigned managed identity cannot be disabled.")
        if identity_type == 'SystemAssigned,UserAssigned':
            # if both system-assigned and user-assigned identity is enabled, then disable system-assigned identity
            identity_type = 'UserAssigned'
        elif identity_type == 'SystemAssigned':
            # if only system-assigned identity is enabled, then disable system-assigned identity
            identity_type = 'None'

    if identity_type == 'UserAssigned' or identity_type == 'SystemAssigned,UserAssigned':
        identities_map = {}
        for identity in server.identity.user_assigned_identities:
            identities_map[identity] = {}
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                user_assigned_identities=identities_map,
                type=identity_type)}
    else:
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                type=identity_type)}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Updating user assigned identity type for server {}'.format(server_name)
    )

    return result.identity


def flexible_server_identity_assign(cmd, client, resource_group_name, server_name, identities):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)
    identity_type = server.identity.type if (server and server.identity and server.identity.type) else 'None'

    if identity_type == 'SystemAssigned':
        # if system-assigned identity is enabled, then enable both system
        identity_type = 'SystemAssigned,UserAssigned'
    elif identity_type == 'None':
        # if system-assigned identity is not enabled, then enable user-assigned identity
        identity_type = 'UserAssigned'

    identities_map = {}
    for identity in identities:
        identities_map[identity] = {}

    parameters = {
        'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
            user_assigned_identities=identities_map,
            type=identity_type)}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Adding identities to server {}'.format(server_name)
    )

    return result.identity


def flexible_server_identity_remove(cmd, client, resource_group_name, server_name, identities):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    instance = client.get(resource_group_name, server_name)

    if instance.data_encryption:
        primary_id = instance.data_encryption.primary_user_assigned_identity_id

        if primary_id and primary_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for data encryption.".format(primary_id))

        geo_backup_id = instance.data_encryption.geo_backup_user_assigned_identity_id

        if geo_backup_id and geo_backup_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for geo backup data encryption.".format(geo_backup_id))

    identities_map = {}
    for identity in identities:
        identities_map[identity] = None

    system_assigned_identity = instance.identity and 'principalId' in instance.identity.additional_properties and instance.identity.additional_properties['principalId'] is not None

    # if there are no user-assigned identities or all user-assigned identities are already removed
    if not (instance.identity and instance.identity.user_assigned_identities) or \
       all(key.lower() in [identity.lower() for identity in identities] for key in instance.identity.user_assigned_identities.keys()):
        if system_assigned_identity:
            # if there is system assigned identity, then set identity type to SystemAssigned
            parameters = {
                'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                    type="SystemAssigned")}
        else:
            # no system assigned identity, set identity type to None
            parameters = {
                'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                    type="None")}
    # if there are user-assigned identities and system assigned identity, then set identity type to SystemAssigned,UserAssigned
    elif system_assigned_identity:
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                user_assigned_identities=identities_map,
                type="SystemAssigned,UserAssigned")}
    # there is no system assigned identity, but there are user-assigned identities, then set identity type to UserAssigned
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


def flexible_server_identity_list(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)
    return server.identity or postgresql_flexibleservers.models.UserAssignedIdentity(type="SystemAssigned")


def flexible_server_identity_show(cmd, client, resource_group_name, server_name, identity):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)

    for key, value in server.identity.user_assigned_identities.items():
        if key.lower() == identity.lower():
            return value

    raise CLIError("Identity '{}' does not exist in server {}.".format(identity, server_name))


# Custom functions for ad-admin
def flexible_server_microsoft_entra_admin_set(cmd, client, resource_group_name, server_name, login, sid, principal_type=None, no_wait=False):
    validate_resource_group(resource_group_name)

    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot create a Microsoft Entra admin on a server with replication role. Use the primary server instead.")

    return _create_admin(client, resource_group_name, server_name, login, sid, principal_type, no_wait)


# Create Microsoft Entra admin
def _create_admin(client, resource_group_name, server_name, principal_name, sid, principal_type=None, no_wait=False):
    parameters = {
        'principal_name': principal_name,
        'tenant_id': get_tenant_id(),
        'principal_type': principal_type
    }

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, server_name, sid, parameters)


def flexible_server_microsoft_entra_admin_delete(cmd, client, resource_group_name, server_name, sid, no_wait=False):
    validate_resource_group(resource_group_name)

    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot delete an Microsoft Entra admin on a server with replication role. Use the primary server instead.")

    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, server_name, sid)


def flexible_server_microsoft_entra_admin_list(client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)

    return client.list_by_server(
        resource_group_name=resource_group_name,
        server_name=server_name)


def flexible_server_microsoft_entra_admin_show(client, resource_group_name, server_name, sid):
    validate_resource_group(resource_group_name)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        object_id=sid)


def flexible_server_provision_network_resource(cmd, resource_group_name, server_name,
                                               location, db_context, private_dns_zone_arguments=None, public_access=None,
                                               vnet=None, subnet=None, vnet_address_prefix=None, subnet_address_prefix=None, yes=False):
    validate_resource_group(resource_group_name)

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
        if public_access is not None and str(public_access).lower() in ['disabled', 'none']:
            network.public_network_access = 'Disabled'
        else:
            network.public_network_access = 'Enabled'

    return network, start_ip, end_ip


def flexible_server_threat_protection_get(
        client,
        resource_group_name,
        server_name):
    '''
    Gets an advanced threat protection setting.
    '''

    validate_resource_group(resource_group_name)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        threat_protection_name="Default")


def flexible_server_threat_protection_update(
        cmd,
        client, resource_group_name, server_name,
        state=None):
    # pylint: disable=unused-argument
    '''
    Updates an advanced threat protection setting. Custom update function to apply parameters to instance.
    '''

    validate_resource_group(resource_group_name)

    try:
        parameters = {
            'properties': {
                'state': state
            }
        }
        return resolve_poller(
            client.begin_create_or_update(
                resource_group_name=resource_group_name,
                server_name=server_name,
                threat_protection_name="Default",
                parameters=parameters),
            cmd.cli_ctx,
            'PostgreSQL Flexible Server Advanced Threat Protection Setting Update')
    except HttpResponseError as ex:
        if "Operation returned an invalid status 'Accepted'" in ex.message:
            # TODO: Once the swagger is updated, this won't be needed.
            pass
        else:
            raise ex


def flexible_server_threat_protection_set(
        cmd,
        client,
        resource_group_name,
        server_name,
        parameters):
    validate_resource_group(resource_group_name)

    return resolve_poller(
        client.begin_create_or_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            threat_protection_name="Default",
            parameters=parameters),
        cmd.cli_ctx,
        'PostgreSQL Flexible Server Advanced Threat Protection Setting Update')


# Custom functions for server logs
def flexible_server_download_log_files(client, resource_group_name, server_name, file_name):
    validate_resource_group(resource_group_name)

    # list all files
    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name.replace("/", "_"))


def flexible_server_list_log_files_with_filter(client, resource_group_name, server_name, filename_contains=None,
                                               file_last_written=None, max_file_size=None):
    validate_resource_group(resource_group_name)

    # list all files
    all_files = client.list_by_server(resource_group_name, server_name)
    files = []

    if file_last_written is None:
        file_last_written = 72
    time_line = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(hours=file_last_written)

    for f in all_files:
        if f.last_modified_time < time_line:
            continue
        if filename_contains is not None and re.search(filename_contains, f.name) is None:
            continue
        if max_file_size is not None and f.size_in_kb > max_file_size:
            continue

        del f.created_time
        files.append(f)

    return files


def migration_create_func(cmd, client, resource_group_name, server_name, properties, migration_mode="offline",
                          migration_name=None, migration_option=None, tags=None, location=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    logging_name = 'PostgreSQL'
    subscription_id = get_subscription_id(cmd.cli_ctx)
    properties_filepath = os.path.join(os.path.abspath(os.getcwd()), properties)
    # Generate missing parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'postgres')

    # Get the properties for migration from the json file at the specific properties file path
    if not os.path.exists(properties_filepath):
        raise FileOperationError("Properties file does not exist in the given location")
    with open(properties_filepath, "r") as f:
        try:
            request_payload = json.load(f)
            migration_parameters = request_payload.get("properties")
        except ValueError as err:
            logger.error(err)
            raise BadRequestError("Invalid json file. Make sure that the json file content is properly formatted.")

    if migration_name is None:
        # Convert a UUID to a string of hex digits in standard form
        migration_name = str(uuid.uuid4())

    if migration_option is None:
        # Use default migration_option as 'ValidateAndMigrate'
        migration_option = "ValidateAndMigrate"

    return _create_migration(cmd, logging_name, client, subscription_id, resource_group_name, server_name, migration_name,
                             migration_mode, migration_option, migration_parameters, tags, location)


def migration_show_func(cmd, client, resource_group_name, server_name, migration_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.get(resource_group_name, server_name, migration_name)


def migration_list_func(cmd, client, resource_group_name, server_name, migration_filter="Active"):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.list_by_target_server(resource_group_name, server_name, migration_list_filter=migration_filter)


def migration_delete_func(cmd, client, resource_group_name, server_name, migration_name):
    validate_resource_group(resource_group_name)

    return client.cancel(resource_group_name, server_name, migration_name)


def migration_update_func(cmd, client, resource_group_name, server_name, migration_name, setup_logical_replication=None, cutover=None, cancel=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    operationSpecified = False
    if setup_logical_replication is True:
        operationSpecified = True
        parameters = postgresql_flexibleservers.models.MigrationResourceForPatch(setup_logical_replication_on_source_db_if_needed=True)

    if cutover is not None:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        migration_resource = migration_show_func(cmd, client, resource_group_name, server_name, migration_name)
        if migration_resource.migration_mode == "Offline":
            raise BadRequestError("Cutover is not possible for migration {} if the migration_mode set to offline. The migration will cutover automatically".format(migration_name))
        parameters = postgresql_flexibleservers.models.MigrationResourceForPatch(trigger_cutover="True", dbs_to_trigger_cutover_migration_on=migration_resource.dbs_to_migrate)

    if cancel is not None:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        migration_resource = migration_show_func(cmd, client, resource_group_name, server_name, migration_name)
        parameters = postgresql_flexibleservers.models.MigrationResourceForPatch(cancel="True", dbs_to_cancel_migration_on=migration_resource.dbs_to_migrate)

    if operationSpecified is False:
        raise RequiredArgumentMissingError("Incorrect Usage: At least one update operation needs to be specified.")

    return client.update(resource_group_name, server_name, migration_name, parameters)


def migration_check_name_availability(cmd, client, resource_group_name, server_name, migration_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    migration_name_availability_parammeters = {"name": "%s" % migration_name, "type": "Microsoft.DBforPostgreSQL/flexibleServers/migrations"}
    return client.check_name_availability(resource_group_name, server_name, migration_name_availability_parammeters)


def virtual_endpoint_create_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name, endpoint_type, members):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)
    validate_virtual_endpoint_name_availability(cmd, virtual_endpoint_name)

    parameters = {
        'name': virtual_endpoint_name,
        'endpoint_type': endpoint_type,
        'members': [members]
    }

    return client.begin_create(
        resource_group_name,
        server_name,
        virtual_endpoint_name,
        parameters)


def virtual_endpoint_show_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.get(
        resource_group_name,
        server_name,
        virtual_endpoint_name)


def virtual_endpoint_list_func(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.list_by_server(
        resource_group_name,
        server_name)


def virtual_endpoint_delete_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name, yes=False):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the virtual endpoint '{0}' in resource group '{1}'".format(virtual_endpoint_name,
                                                                                                        resource_group_name), yes=yes)

    return client.begin_delete(
        resource_group_name,
        server_name,
        virtual_endpoint_name)


def virtual_endpoint_update_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name, endpoint_type, members):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    parameters = {
        'name': virtual_endpoint_name,
        'endpoint_type': endpoint_type,
        'members': [members]
    }

    return client.begin_update(
        resource_group_name,
        server_name,
        virtual_endpoint_name,
        parameters)


def backup_create_func(client, resource_group_name, server_name, backup_name):
    validate_resource_group(resource_group_name)
    validate_backup_name(backup_name)

    return client.begin_create(
        resource_group_name,
        server_name,
        backup_name)


def ltr_precheck_func(client, resource_group_name, server_name, backup_name):
    validate_resource_group(resource_group_name)

    return client.check_prerequisites(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters={"backup_settings": {"backup_name": backup_name}}
    )


def ltr_start_func(client, resource_group_name, server_name, backup_name, sas_url):
    validate_resource_group(resource_group_name)

    parameters = {
        "backup_settings": {
            "backup_name": backup_name
        },
        "target_details": {
            "sas_uri_list": [sas_url]
        }
    }

    return client.begin_start(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters=parameters
    )


def backup_delete_func(client, resource_group_name, server_name, backup_name, yes=False):
    validate_resource_group(resource_group_name)

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the backup '{0}' in server '{1}'".format(backup_name, server_name), yes=yes)

    return client.begin_delete(
        resource_group_name,
        server_name,
        backup_name)


def flexible_server_approve_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                                        description=None):
    """Approve a private endpoint connection request for a server."""
    validate_resource_group(resource_group_name)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=True,
        description=description)


def flexible_server_reject_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                                       description=None):
    """Reject a private endpoint connection request for a server."""
    validate_resource_group(resource_group_name)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=False,
        description=description)


def flexible_server_private_link_resource_get(
        client,
        resource_group_name,
        server_name):
    '''
    Gets a private link resource for a PostgreSQL flexible server.
    '''
    validate_resource_group(resource_group_name)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        group_name="postgresqlServer")


def flexible_server_fabric_mirroring_start(cmd, client, resource_group_name, server_name, database_names, yes=False):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)
    flexible_servers_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')
    server = flexible_servers_client.get(resource_group_name, server_name)

    if server.high_availability.mode != "Disabled" and server.version not in ["17", "18"]:
        # disable fabric mirroring on HA server
        raise CLIError("Fabric mirroring is not supported on servers with high availability enabled.")

    databases = ','.join(database_names)
    user_confirmation("Are you sure you want to prepare and enable your server" +
                      " '{0}' in resource group '{1}' for mirroring of databases '{2}'.".format(server_name, resource_group_name, databases) +
                      " This requires restart.", yes=yes)

    if (server.identity is None or 'SystemAssigned' not in server.identity.type):
        logger.warning('Enabling system assigned managed identity on the server.')
        flexible_server_identity_update(cmd, flexible_servers_client, resource_group_name, server_name, 'Enabled')

    logger.warning('Updating necessary server parameters.')
    source = "user-override"
    configuration_name = "azure.fabric_mirror_enabled"
    value = "on"
    _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
    configuration_name = "azure.mirror_databases"
    value = databases
    return _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)


def flexible_server_fabric_mirroring_stop(cmd, client, resource_group_name, server_name, yes=False):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    flexible_servers_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')
    server = flexible_servers_client.get(resource_group_name, server_name)

    if server.high_availability.mode != "Disabled" and server.version not in ["17", "18"]:
        # disable fabric mirroring on HA server
        raise CLIError("Fabric mirroring is not supported on servers with high availability enabled.")

    user_confirmation("Are you sure you want to disable mirroring for server '{0}' in resource group '{1}'".format(server_name, resource_group_name), yes=yes)

    configuration_name = "azure.fabric_mirror_enabled"
    parameters = postgresql_flexibleservers.models.Configuration(
        value="off",
        source="user-override"
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


def flexible_server_fabric_mirroring_update_databases(cmd, client, resource_group_name, server_name, database_names, yes=False):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    flexible_servers_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')
    server = flexible_servers_client.get(resource_group_name, server_name)

    if server.high_availability.mode != "Disabled" and server.version not in ["17", "18"]:
        # disable fabric mirroring on HA server
        raise CLIError("Fabric mirroring is not supported on servers with high availability enabled.")

    databases = ','.join(database_names)
    user_confirmation("Are you sure for server '{0}' in resource group '{1}' you want to update the databases being mirrored to be '{2}'"
                      .format(server_name, resource_group_name, databases), yes=yes)

    configuration_name = "azure.mirror_databases"
    parameters = postgresql_flexibleservers.models.Configuration(
        value=databases,
        source="user-override"
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


def _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value):
    parameters = postgresql_flexibleservers.models.Configuration(
        value=value,
        source=source
    )

    return resolve_poller(
        client.begin_update(resource_group_name, server_name, configuration_name, parameters), cmd.cli_ctx, 'PostgreSQL Parameter update')


def index_tuning_update(cmd, client, resource_group_name, server_name, index_tuning_enabled):
    validate_resource_group(resource_group_name)
    source = "user-override"

    if index_tuning_enabled == "True":
        subscription = get_subscription_id(cmd.cli_ctx)
        postgres_source_client = get_postgresql_flexible_management_client(cmd.cli_ctx, subscription)
        source_server_object = postgres_source_client.servers.get(resource_group_name, server_name)
        location = ''.join(source_server_object.location.lower().split())
        list_location_capability_info = get_postgres_location_capability_info(cmd, location, is_offer_restriction_check_required=True)
        autonomous_tuning_supported = list_location_capability_info['autonomous_tuning_supported']
        if not autonomous_tuning_supported:
            raise CLIError("Index tuning is not supported for the server.")

        logger.warning("Enabling index tuning for the server.")
        configuration_name = "index_tuning.mode"
        value = "report"
        _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
        configuration_name = "pg_qs.query_capture_mode"
        query_capture_mode_configuration = client.get(resource_group_name, server_name, configuration_name)

        if query_capture_mode_configuration.value.lower() == "none":
            value = "all"
            _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
        logger.warning("Index tuning is enabled for the server.")
    else:
        logger.warning("Disabling index tuning for the server.")
        configuration_name = "index_tuning.mode"
        value = "off"
        _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
        logger.warning("Index tuning is disabled for the server.")


def index_tuning_show(client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    index_tuning_configuration = client.get(resource_group_name, server_name, "index_tuning.mode")
    query_capture_mode_configuration = client.get(resource_group_name, server_name, "pg_qs.query_capture_mode")

    if index_tuning_configuration.value.lower() == "report" and query_capture_mode_configuration.value.lower() != "none":
        logger.warning("Index tuning is enabled for the server.")
    else:
        logger.warning("Index tuning is disabled for the server.")


def index_tuning_settings_list(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    index_tuning_configurations_map_values = get_autonomous_tuning_settings_map().values()
    configurations_list = client.list_by_server(resource_group_name, server_name)

    # Filter the list based on the values in the dictionary
    index_tuning_settings = [setting for setting in configurations_list if setting.name in index_tuning_configurations_map_values]

    return index_tuning_settings


def index_tuning_settings_get(cmd, client, resource_group_name, server_name, setting_name):
    validate_resource_group(resource_group_name)
    index_tuning_configurations_map = get_autonomous_tuning_settings_map()
    index_tuning_configuration_name = index_tuning_configurations_map[setting_name]

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        configuration_name=index_tuning_configuration_name)


def index_tuning_settings_set(client, resource_group_name, server_name, setting_name, value=None):
    source = "user-override" if value else None
    tuning_settings = get_autonomous_tuning_settings_map()
    configuration_name = tuning_settings[setting_name]
    return flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source, value)


def index_tuning_recommendations_list(cmd, resource_group_name, server_name, recommendation_type=None):
    validate_resource_group(resource_group_name)
    tuning_options_client = cf_postgres_flexible_tuning_options(cmd.cli_ctx, None)

    return tuning_options_client.list_recommendations(
        resource_group_name=resource_group_name,
        server_name=server_name,
        tuning_option="index",
        recommendation_type=recommendation_type
    )


def autonomous_tuning_update(cmd, client, resource_group_name, server_name, autonomous_tuning_enabled):
    validate_resource_group(resource_group_name)
    source = "user-override"

    if autonomous_tuning_enabled == "True":
        subscription = get_subscription_id(cmd.cli_ctx)
        postgres_source_client = get_postgresql_flexible_management_client(cmd.cli_ctx, subscription)
        source_server_object = postgres_source_client.servers.get(resource_group_name, server_name)
        location = ''.join(source_server_object.location.lower().split())
        list_location_capability_info = get_postgres_location_capability_info(cmd, location, is_offer_restriction_check_required=True)
        autonomous_tuning_supported = list_location_capability_info['autonomous_tuning_supported']
        if not autonomous_tuning_supported:
            raise CLIError("Autonomous tuning is not supported for the server.")

        logger.warning("Enabling autonomous tuning for the server.")
        configuration_name = "index_tuning.mode"
        value = "report"
        _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
        configuration_name = "pg_qs.query_capture_mode"
        query_capture_mode_configuration = client.get(resource_group_name, server_name, configuration_name)

        if query_capture_mode_configuration.value.lower() == "none":
            value = "all"
            _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
        logger.warning("Autonomous tuning is enabled for the server.")
    else:
        logger.warning("Disabling autonomous tuning for the server.")
        configuration_name = "index_tuning.mode"
        value = "off"
        _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value)
        logger.warning("Autonomous tuning is disabled for the server.")


def autonomous_tuning_show(client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    autonomous_tuning_configuration = client.get(resource_group_name, server_name, "index_tuning.mode")
    query_capture_mode_configuration = client.get(resource_group_name, server_name, "pg_qs.query_capture_mode")

    if autonomous_tuning_configuration.value.lower() == "report" and query_capture_mode_configuration.value.lower() != "none":
        logger.warning("Autonomous tuning is enabled for the server.")
    else:
        logger.warning("Autonomous tuning is disabled for the server.")


def autonomous_tuning_settings_list(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    autonomous_tuning_configurations_map_values = get_autonomous_tuning_settings_map().values()
    configurations_list = client.list_by_server(resource_group_name, server_name)

    # Filter the list based on the values in the dictionary
    autonomous_tuning_settings = [setting for setting in configurations_list if setting.name in autonomous_tuning_configurations_map_values]

    return autonomous_tuning_settings


def autonomous_tuning_settings_get(cmd, client, resource_group_name, server_name, setting_name):
    validate_resource_group(resource_group_name)
    autonomous_tuning_configurations_map = get_autonomous_tuning_settings_map()
    autonomous_tuning_configuration_name = autonomous_tuning_configurations_map[setting_name]

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        configuration_name=autonomous_tuning_configuration_name)


def autonomous_tuning_settings_set(client, resource_group_name, server_name, setting_name, value=None):
    source = "user-override" if value else None
    tuning_settings = get_autonomous_tuning_settings_map()
    configuration_name = tuning_settings[setting_name]
    return flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source, value)


def autonomous_tuning_index_recommendations_list(cmd, resource_group_name, server_name, recommendation_type=None):
    validate_resource_group(resource_group_name)
    tuning_options_client = cf_postgres_flexible_tuning_options(cmd.cli_ctx, None)

    return tuning_options_client.list_recommendations(
        resource_group_name=resource_group_name,
        server_name=server_name,
        tuning_option="index",
        recommendation_type=recommendation_type
    )


def autonomous_tuning_table_recommendations_list(cmd, resource_group_name, server_name, recommendation_type=None):
    validate_resource_group(resource_group_name)
    tuning_options_client = cf_postgres_flexible_tuning_options(cmd.cli_ctx, None)

    return tuning_options_client.list_recommendations(
        resource_group_name=resource_group_name,
        server_name=server_name,
        tuning_option="table",
        recommendation_type=recommendation_type
    )


def _update_private_endpoint_connection_status(cmd, client, resource_group_name, server_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):  # pylint: disable=unused-argument
    validate_resource_group(resource_group_name)

    private_endpoint_connections_client = cf_postgres_flexible_private_endpoint_connections(cmd.cli_ctx, None)
    private_endpoint_connection = private_endpoint_connections_client.get(resource_group_name=resource_group_name,
                                                                          server_name=server_name,
                                                                          private_endpoint_connection_name=private_endpoint_connection_name)
    new_status = 'Approved' if is_approved else 'Rejected'

    private_link_service_connection_state = {
        'status': new_status,
        'description': description
    }

    private_endpoint_connection.private_link_service_connection_state = private_link_service_connection_state

    return client.begin_update(resource_group_name=resource_group_name,
                               server_name=server_name,
                               private_endpoint_connection_name=private_endpoint_connection_name,
                               parameters=private_endpoint_connection)


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


def _create_postgresql_connection_string(host, user, password, database=POSTGRES_DB_NAME):
    connection_kwargs = {
        'user': user if user is not None else '{user}',
        'host': host,
        'password': password if password is not None else '{password}',
        'database': database,
    }
    return 'postgresql://{user}:{password}@{host}/{database}?sslmode=require'.format(**connection_kwargs)


def _create_microsoft_entra_connection_string(host, database=POSTGRES_DB_NAME, admin='<admin>'):
    connection_kwargs = {
        'user': admin,
        'host': host,
        'database': database,
    }
    return 'postgresql://{user}:<access-token>@{host}/{database}?sslmode=require'.format(**connection_kwargs)


def _form_response(username, sku, location, server_id, host, version, password, connection_string, firewall_id=None,
                   subnet_id=None, is_password_auth=True, is_microsoft_entra_auth_enabled=False, microsoft_admin=None, connection_string_microsoft_entra=None):

    output = {
        'host': host,
        'username': username if is_password_auth else None,
        'password': password if is_password_auth else None,
        'skuname': sku,
        'location': location,
        'id': server_id,
        'version': version,
        'databaseName': POSTGRES_DB_NAME,
        'connectionString': connection_string
    }
    if is_microsoft_entra_auth_enabled:
        output['admin'] = microsoft_admin
        output['connectionStringMicrosoftEntra'] = connection_string_microsoft_entra
    if firewall_id is not None:
        output['firewallName'] = firewall_id
    if subnet_id is not None:
        output['subnetId'] = subnet_id
    return output


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


def _get_pg_replica_zone(availabilityZones, sourceServerZone, replicaZone):
    preferredZone = 'none'
    for _index, zone in enumerate(availabilityZones):
        if zone != sourceServerZone and zone != 'none':
            preferredZone = zone

    if not preferredZone:
        preferredZone = 'none'

    selectZone = preferredZone if not replicaZone else replicaZone

    selectZoneSupported = False
    for _index, zone in enumerate(availabilityZones):
        if zone == selectZone:
            selectZoneSupported = True

    pg_replica_zone = None
    if len(availabilityZones) > 1 and selectZone and selectZoneSupported:
        pg_replica_zone = selectZone if selectZone != 'none' else None
    else:
        sourceZoneSupported = False
        for _index, zone in enumerate(availabilityZones):
            if zone == sourceServerZone:
                sourceZoneSupported = True
        if sourceZoneSupported:
            pg_replica_zone = sourceServerZone
        else:
            pg_replica_zone = None

    return pg_replica_zone


def _create_migration(cmd, logging_name, client, subscription_id, resource_group_name, target_db_server_name,
                      migration_name, migration_mode, migration_option, parameters, tags, location):
    validate_resource_group(resource_group_name)

    parameter_keys = list(parameters.keys())
    migrationInstanceResourceId = get_case_insensitive_key_value("MigrationRuntimeResourceId", parameter_keys, parameters)
    if migrationInstanceResourceId is not None:
        validate_migration_runtime_server(cmd, migrationInstanceResourceId, resource_group_name, target_db_server_name)

    logger.warning('Creating %s Migration for server \'%s\' in group \'%s\' and subscription \'%s\'...', logging_name, target_db_server_name, resource_group_name, subscription_id)
    secret_parameter_dictionary = get_case_insensitive_key_value("SecretParameters", parameter_keys, parameters)
    secret_parameter_keys = list(secret_parameter_dictionary.keys())
    admin_credentials_dictionary = get_case_insensitive_key_value("AdminCredentials", secret_parameter_keys, secret_parameter_dictionary)
    admin_credentials_keys = list(admin_credentials_dictionary.keys())
    source_type = get_case_insensitive_key_value("SourceType", parameter_keys, parameters)
    ssl_mode = get_case_insensitive_key_value("SslMode", parameter_keys, parameters)

    admin_credentials = postgresql_flexibleservers.models.AdminCredentials(
        source_server_password=get_case_insensitive_key_value("SourceServerPassword", admin_credentials_keys, admin_credentials_dictionary),
        target_server_password=get_case_insensitive_key_value("TargetServerPassword", admin_credentials_keys, admin_credentials_dictionary))
    secret_parameters = postgresql_flexibleservers.models.MigrationSecretParameters(
        admin_credentials=admin_credentials,
        source_server_username=get_case_insensitive_key_value("SourceServerUsername", secret_parameter_keys, secret_parameter_dictionary),
        target_server_username=get_case_insensitive_key_value("TargetServerUsername", secret_parameter_keys, secret_parameter_dictionary))
    migration_parameters = postgresql_flexibleservers.models.Migration(
        tags=tags,
        location=location,
        migration_mode=migration_mode,
        source_db_server_resource_id=get_case_insensitive_key_value("SourceDbServerResourceId", parameter_keys, parameters),
        secret_parameters=secret_parameters,
        source_db_server_fully_qualified_domain_name=get_case_insensitive_key_value("SourceDbServerFullyQualifiedDomainName", parameter_keys, parameters),
        target_db_server_fully_qualified_domain_name=get_case_insensitive_key_value("TargetDbServerFullyQualifiedDomainName", parameter_keys, parameters),
        dbs_to_migrate=get_case_insensitive_key_value("DbsToMigrate", parameter_keys, parameters),
        setup_logical_replication_on_source_db_if_needed=get_enum_value_true_false(get_case_insensitive_key_value("SetupLogicalReplicationOnSourceDbIfNeeded", parameter_keys, parameters), "SetupLogicalReplicationOnSourceDbIfNeeded"),
        overwrite_dbs_in_target=get_enum_value_true_false(get_case_insensitive_key_value("OverwriteDbsInTarget", parameter_keys, parameters), "OverwriteDbsInTarget"),
        source_type=source_type,
        migration_option=migration_option,
        ssl_mode=ssl_mode,
        migration_instance_resource_id=migrationInstanceResourceId)

    return client.create(resource_group_name, server_name=target_db_server_name, migration_name=migration_name, parameters=migration_parameters)


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


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class DbContext:
    def __init__(self, cmd=None, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 cf_availability=None, cf_private_dns_zone_suffix=None,
                 command_group=None, server_client=None, location=None):
        self.cmd = cmd
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_availability = cf_availability
        self.cf_private_dns_zone_suffix = cf_private_dns_zone_suffix
        self.logging_name = logging_name
        self.cf_db = cf_db
        self.command_group = command_group
        self.server_client = server_client
        self.location = location
