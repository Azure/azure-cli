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
from .flexible_server_custom_common import create_firewall_rule
from .flexible_server_network import prepare_private_network, prepare_private_dns_zone, prepare_public_network, flexible_server_provision_network_resource
from .validators import pg_arguments_validator, validate_server_name, validate_and_format_restore_point_in_time, \
    validate_postgres_replica, validate_georestore_network, pg_byok_validator, validate_migration_runtime_server, \
    validate_resource_group, check_resource_group, validate_citus_cluster, validate_backup_name, \
    validate_virtual_endpoint_name_availability, validate_database_name, compare_sku_names, is_citus_cluster, pg_restore_validator


def flexible_server_microsoft_entra_admin_set(cmd, client, resource_group_name, server_name, login, sid, principal_type=None, no_wait=False):
    validate_resource_group(resource_group_name)

    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot create a Microsoft Entra admin on a server with replication role. Use the primary server instead.")

    return _create_admin(client, resource_group_name, server_name, login, sid, principal_type, no_wait)


def _create_admin(client, resource_group_name, server_name, principal_name, sid, principal_type=None, no_wait=False):
    parameters = {
        'properties': {
            'principalName': principal_name,
            'tenantId': get_tenant_id(),
            'principalType': principal_type
        }
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
