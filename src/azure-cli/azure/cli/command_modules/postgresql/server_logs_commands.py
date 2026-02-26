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
    cf_postgres_flexible_config, cf_postgres_flexible_admin, cf_postgres_flexible_replica
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


def flexible_server_log_list(client, resource_group_name, server_name, filename_contains=None,
                             file_last_written=None, max_file_size=None):
    validate_resource_group(resource_group_name)

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


def flexible_server_version_upgrade(cmd, client, resource_group_name, server_name, version, yes=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    if not yes:
        user_confirmation(
            "Upgrading major version in server {} is irreversible. The action you're about to take can't be undone. "
            "Going further will initiate major version upgrade to the selected version on this server."
            .format(server_name), yes=yes)

    instance = client.get(resource_group_name, server_name)

    current_version = int(instance.version.split('.')[0])
    if current_version >= int(version):
        raise CLIError("The version to upgrade to must be greater than the current version.")

    list_server_capability_info = get_postgres_server_capability_info(cmd, resource_group_name, server_name)
    eligible_versions = list_server_capability_info['supported_server_versions'][str(current_version)]

    if version == '13':
        logger.warning("PostgreSQL version 13 will reach end-of-life (EOL) soon. "
                       "Upgrade to PostgreSQL 14 or later as soon as possible to "
                       "maintain security, performance, and supportability.")

    if version not in eligible_versions:
        # version not supported
        error_message = ""
        if len(eligible_versions) > 0:
            error_message = "Server is running version {}. It can only be upgraded to the following versions: {} ".format(str(current_version), eligible_versions)
        else:
            error_message = "Server is running version {}. It cannot be upgraded to any higher version. ".format(str(current_version))

        raise CLIError(error_message)

    replica_operations_client = cf_postgres_flexible_replica(cmd.cli_ctx, '_')
    version_mapped = version

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower() or len(list(replicas)) > 0:
        raise CLIError("Major version upgrade is not yet supported for servers in a read replica setup.")

    parameters = {
        'properties': {
            'version': version_mapped
        }
    }

    return resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Upgrading server {} to major version {}'.format(server_name, version)
    )
