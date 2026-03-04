# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import CLIError, user_confirmation
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from knack.log import get_logger
from .identity_commands import flexible_server_identity_update
from .parameter_commands import _update_parameters
from .._client_factory import cf_postgres_flexible_servers
from ..utils.validators import validate_resource_group, validate_citus_cluster

logger = get_logger(__name__)


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
