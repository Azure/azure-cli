# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError
from knack.log import get_logger
from .._client_factory import (
    cf_postgres_flexible_tuning_options,
    get_postgresql_flexible_management_client)
from ..utils._flexible_server_location_capabilities_util import (
    get_postgres_location_capability_info,
    get_postgres_server_capability_info)
from ..utils._util import get_autonomous_tuning_settings_map
from ..utils.validators import validate_resource_group
from .parameter_commands import _update_parameters, flexible_parameter_update

logger = get_logger(__name__)


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
