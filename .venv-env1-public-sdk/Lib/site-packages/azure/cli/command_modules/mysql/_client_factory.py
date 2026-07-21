# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.auth.identity import get_environment_credential, AZURE_CLIENT_ID

# pylint: disable=import-outside-toplevel

RM_URI_OVERRIDE = 'AZURE_CLI_RDBMS_RM_URI'
SUB_ID_OVERRIDE = 'AZURE_CLI_RDBMS_SUB_ID'


def get_mysql_flexible_management_client(cli_ctx, **_):
    from os import getenv
    from azure.mgmt.mysqlflexibleservers import MySQLManagementClient

    # Allow overriding resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    rm_uri_override = getenv(RM_URI_OVERRIDE)
    if rm_uri_override:
        client_id = getenv(AZURE_CLIENT_ID)
        if client_id:
            credentials = get_environment_credential()
        else:
            from msrest.authentication import Authentication  # pylint: disable=import-error
            credentials = Authentication()

        return MySQLManagementClient(
            subscription_id=getenv(SUB_ID_OVERRIDE),
            base_url=rm_uri_override,
            credential=credentials)
    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, MySQLManagementClient)


def get_mysql_flexible_management_client_by_sub(cli_ctx, subscription_id, **_):
    from os import getenv
    from azure.mgmt.mysqlflexibleservers import MySQLManagementClient

    # Allow overriding resource manager URI using environment variable
    rm_uri_override = getenv(RM_URI_OVERRIDE)
    if rm_uri_override:
        client_id = getenv(AZURE_CLIENT_ID)
        if client_id:
            credentials = get_environment_credential()
        else:
            from msrest.authentication import Authentication  # pylint: disable=import-error
            credentials = Authentication()

        return MySQLManagementClient(
            subscription_id=subscription_id,
            base_url=rm_uri_override,
            credential=credentials)
    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, MySQLManagementClient, subscription_id=subscription_id)


def get_mysql_management_client(cli_ctx, **_):
    from os import getenv
    from azure.mgmt.rdbms.mysql import MySQLManagementClient

    # Allow overriding resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    rm_uri_override = getenv(RM_URI_OVERRIDE)
    if rm_uri_override:
        client_id = getenv(AZURE_CLIENT_ID)
        if client_id:
            credentials = get_environment_credential()
        else:
            from msrest.authentication import Authentication  # pylint: disable=import-error
            credentials = Authentication()

        return MySQLManagementClient(
            subscription_id=getenv(SUB_ID_OVERRIDE),
            base_url=rm_uri_override,
            credential=credentials)
    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, MySQLManagementClient)


# Meru operations for flexible servers
def cf_mysql_flexible_servers(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).servers


def cf_mysql_flexible_firewall_rules(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).firewall_rules


def cf_mysql_flexible_config(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).configurations


def cf_mysql_flexible_db(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).databases


def cf_mysql_flexible_replica(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).replicas


def cf_mysql_flexible_location_capabilities(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).location_based_capabilities


def cf_mysql_flexible_log(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).log_files


def cf_mysql_flexible_backup(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).long_running_backup


def cf_mysql_flexible_backups(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).long_running_backups


def cf_mysql_flexible_export(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).backup_and_export


def cf_mysql_flexible_adadmin(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).azure_ad_administrators


def cf_mysql_advanced_threat_protection(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).advanced_threat_protection_settings


def cf_mysql_flexible_maintenances(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).maintenances


def cf_mysql_check_resource_availability(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).check_name_availability


def cf_mysql_check_resource_availability_without_location(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).check_name_availability_without_location


def cf_mysql_flexible_private_dns_zone_suffix_operations(cli_ctx, _):
    return get_mysql_flexible_management_client(cli_ctx).get_private_dns_zone_suffix


def resource_client_factory(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, subscription_id=subscription_id)


def private_dns_client_factory(cli_ctx, subscription_id=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient, subscription_id=subscription_id).private_zones


def private_dns_link_client_factory(cli_ctx, subscription_id=None):
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient,
                                   subscription_id=subscription_id).virtual_network_links


# Operations for single server
def cf_mysql_servers(cli_ctx, _):
    return get_mysql_management_client(cli_ctx).servers


def cf_mysql_firewall_rules(cli_ctx, _):
    return get_mysql_management_client(cli_ctx).firewall_rules
