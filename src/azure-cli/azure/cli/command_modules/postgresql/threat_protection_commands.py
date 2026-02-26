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
from ._github import create_firewall_rule
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


