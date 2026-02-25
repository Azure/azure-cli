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
from .parameter_commands import flexible_parameter_update, _update_parameters
from .validators import pg_arguments_validator, validate_server_name, validate_and_format_restore_point_in_time, \
    validate_postgres_replica, validate_georestore_network, pg_byok_validator, validate_migration_runtime_server, \
    validate_resource_group, check_resource_group, validate_citus_cluster, validate_backup_name, \
    validate_virtual_endpoint_name_availability, validate_database_name, compare_sku_names, is_citus_cluster, pg_restore_validator

logger = get_logger(__name__)
DEFAULT_DB_NAME = 'flexibleserverdb'
POSTGRES_DB_NAME = 'postgres'
DELEGATION_SERVICE_NAME = "Microsoft.DBforPostgreSQL/flexibleServers"
RESOURCE_PROVIDER = 'Microsoft.DBforPostgreSQL'

def index_tuning_update(cmd, client, resource_group_name, server_name, index_tuning_enabled):
    validate_resource_group(resource_group_name)
    source = "user-override"

    if index_tuning_enabled == "True":
        list_capability_info = get_postgres_server_capability_info(cmd, resource_group_name, server_name, is_offer_restriction_check_required=True)
        autonomous_tuning_supported = list_capability_info['autonomous_tuning_supported']
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


