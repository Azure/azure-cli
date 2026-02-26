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
from ._flexible_server_location_capabilities_util import get_postgres_location_capability_info, get_postgres_server_capability_info
from ._util import get_autonomous_tuning_settings_map
from ._db_context import DbContext
from .deploy_commands import create_firewall_rule
from .flexible_server_network import prepare_private_network, prepare_private_dns_zone, prepare_public_network, flexible_server_provision_network_resource
from .validators import pg_arguments_validator, validate_server_name, validate_and_format_restore_point_in_time, \
    validate_postgres_replica, validate_georestore_network, pg_byok_validator, validate_migration_runtime_server, \
    validate_resource_group, check_resource_group, validate_citus_cluster, validate_backup_name, \
    validate_virtual_endpoint_name_availability, validate_database_name, compare_sku_names, is_citus_cluster, pg_restore_validator

logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
POSTGRES_DB_NAME = 'postgres'
DELEGATION_SERVICE_NAME = "Microsoft.DBforPostgreSQL/flexibleServers"
RESOURCE_PROVIDER = 'Microsoft.DBforPostgreSQL'


# Custom functions for server logs
def _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value):
    parameters = postgresql_flexibleservers.models.Configuration(
        value=value,
        source=source
    )

    return resolve_poller(
        client.begin_update(resource_group_name, server_name, configuration_name, parameters), cmd.cli_ctx, 'PostgreSQL Parameter update')


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

