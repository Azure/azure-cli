# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_sql_management_client(_):
    from azure.mgmt.sql import SqlManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(SqlManagementClient)


def get_sql_servers_operations(kwargs):
    return get_sql_management_client(kwargs).servers


def get_sql_firewall_rules_operations(kwargs):
    return get_sql_management_client(kwargs).firewall_rules


def get_sql_databases_operations(kwargs):
    return get_sql_management_client(kwargs).databases


def get_sql_elastic_pools_operations(kwargs):
    return get_sql_management_client(kwargs).elastic_pools


def get_sql_recommended_elastic_pools_operations(kwargs):
    return get_sql_management_client(kwargs).recommended_elastic_pools
