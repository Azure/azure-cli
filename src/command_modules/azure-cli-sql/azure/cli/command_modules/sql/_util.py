# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_sql_management_client(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.sql import SqlManagementClient
    from msrest.authentication import Authentication
    from os import getenv

    # Allow overriding SQL resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    sql_rm_override = getenv('_AZURE_CLI_SQL_RM_URI')
    if sql_rm_override:
        return SqlManagementClient(
            subscription_id=getenv('_AZURE_CLI_SQL_SUB_ID'),
            base_url=sql_rm_override,
            credentials=Authentication())  # No authentication

    # Normal production scenario.
    return get_mgmt_service_client(SqlManagementClient)


def get_sql_capabilities_operations(kwargs):
    return get_sql_management_client(kwargs).capabilities


def get_sql_databases_operations(kwargs):
    return get_sql_management_client(kwargs).databases


def get_sql_database_operations_operations(kwargs):
    return get_sql_management_client(kwargs).database_operations


def get_sql_database_blob_auditing_policies_operations(kwargs):
    return get_sql_management_client(kwargs).database_blob_auditing_policies


def get_sql_database_threat_detection_policies_operations(kwargs):
    return get_sql_management_client(kwargs).database_threat_detection_policies


def get_sql_database_transparent_data_encryption_activities_operations(kwargs):
    return get_sql_management_client(kwargs).transparent_data_encryption_activities


def get_sql_database_transparent_data_encryptions_operations(kwargs):
    return get_sql_management_client(kwargs).transparent_data_encryptions


def get_sql_database_usages_operations(kwargs):
    return get_sql_management_client(kwargs).database_usages


def get_sql_elastic_pools_operations(kwargs):
    return get_sql_management_client(kwargs).elastic_pools


def get_sql_encryption_protectors_operations(kwargs):
    return get_sql_management_client(kwargs).encryption_protectors


def get_sql_firewall_rules_operations(kwargs):
    return get_sql_management_client(kwargs).firewall_rules


def get_sql_recommended_elastic_pools_operations(kwargs):
    return get_sql_management_client(kwargs).recommended_elastic_pools


def get_sql_replication_links_operations(kwargs):
    return get_sql_management_client(kwargs).replication_links


def get_sql_restorable_dropped_databases_operations(kwargs):
    return get_sql_management_client(kwargs).restorable_dropped_databases


def get_sql_server_azure_ad_administrators_operations(kwargs):
    return get_sql_management_client(kwargs).server_azure_ad_administrators


def get_sql_server_keys_operations(kwargs):
    return get_sql_management_client(kwargs).server_keys


def get_sql_servers_operations(kwargs):
    return get_sql_management_client(kwargs).servers


def get_sql_server_usages_operations(kwargs):
    return get_sql_management_client(kwargs).server_usages


def get_sql_virtual_network_rules_operations(kwargs):
    return get_sql_management_client(kwargs).virtual_network_rules
