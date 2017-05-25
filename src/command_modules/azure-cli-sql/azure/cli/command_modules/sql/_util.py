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


def get_sql_servers_operations(kwargs):
    return get_sql_management_client(kwargs).servers


def get_sql_capabilities_operations(kwargs):
    return get_sql_management_client(kwargs).capabilities


def get_sql_firewall_rules_operations(kwargs):
    return get_sql_management_client(kwargs).firewall_rules


def get_sql_databases_operations(kwargs):
    return get_sql_management_client(kwargs).databases


def get_sql_elastic_pools_operations(kwargs):
    return get_sql_management_client(kwargs).elastic_pools


def get_sql_recommended_elastic_pools_operations(kwargs):
    return get_sql_management_client(kwargs).recommended_elastic_pools
