# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.auth.identity import get_environment_credential, AZURE_CLIENT_ID

# pylint: disable=import-outside-toplevel

RM_URI_OVERRIDE = 'AZURE_CLI_POSTGRESQL_FLEXIBLE_RM_URI'
SUB_ID_OVERRIDE = 'AZURE_CLI_POSTGRESQL_FLEXIBLE_SUB_ID'


def get_postgresql_flexible_management_client(cli_ctx, subscription_id=None, **_):
    from os import getenv
    from azure.mgmt.postgresqlflexibleservers import PostgreSQLManagementClient
    # Allow overriding resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    rm_uri_override = getenv(RM_URI_OVERRIDE)
    subscription = subscription_id if subscription_id is not None else getenv(SUB_ID_OVERRIDE)
    if rm_uri_override:
        client_id = getenv(AZURE_CLIENT_ID)
        if client_id:
            credentials = get_environment_credential()
        else:
            from msrest.authentication import Authentication  # pylint: disable=import-error
            credentials = Authentication()

        return PostgreSQLManagementClient(
            subscription_id=subscription,
            base_url=rm_uri_override,
            credential=credentials)
    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, PostgreSQLManagementClient, subscription_id=subscription)


def cf_postgres_flexible_servers(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).servers


def cf_postgres_flexible_firewall_rules(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).firewall_rules


def cf_postgres_flexible_virtual_endpoints(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).virtual_endpoints


def cf_postgres_flexible_config(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).configurations


def cf_postgres_flexible_replica(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).replicas


def cf_postgres_flexible_location_capabilities(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).capabilities_by_location


def cf_postgres_flexible_server_capabilities(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).capabilities_by_server


def cf_postgres_flexible_backups(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).backups_automatic_and_on_demand


def cf_postgres_flexible_ltr_backups(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).backups_long_term_retention


def cf_postgres_flexible_operations(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).operations


def cf_postgres_flexible_admin(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).administrators_microsoft_entra


def cf_postgres_flexible_migrations(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).migrations


def cf_postgres_flexible_server_threat_protection_settings(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).server_threat_protection_settings


def cf_postgres_flexible_advanced_threat_protection_settings(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).advanced_threat_protection_settings


def cf_postgres_flexible_server_log_files(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).captured_logs


def cf_postgres_check_resource_availability(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).name_availability


def cf_postgres_flexible_db(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).databases


def cf_postgres_flexible_private_dns_zone_suffix_operations(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).private_dns_zone_suffix


def cf_postgres_flexible_private_endpoint_connections(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).private_endpoint_connections


def cf_postgres_flexible_private_link_resources(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).private_link_resources


def cf_postgres_flexible_tuning_options(cli_ctx, _):
    return get_postgresql_flexible_management_client(cli_ctx).tuning_options


def resource_client_factory(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, subscription_id=subscription_id)


def private_dns_client_factory(cli_ctx, subscription_id=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient, subscription_id=subscription_id).private_zones


def private_dns_link_client_factory(cli_ctx, subscription_id=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient,
                                   subscription_id=subscription_id).virtual_network_links
