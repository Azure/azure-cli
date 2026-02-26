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

def _update_parameters(cmd, client, server_name, configuration_name, resource_group_name, source, value):
    parameters = postgresql_flexibleservers.models.Configuration(
        value=value,
        source=source
    )

    return resolve_poller(
        client.begin_update(resource_group_name, server_name, configuration_name, parameters), cmd.cli_ctx, 'PostgreSQL Parameter update')
