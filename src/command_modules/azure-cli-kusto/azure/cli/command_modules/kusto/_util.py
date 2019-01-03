# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_kusto_management_client(cli_ctx):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.kusto import KustoManagementClient
    from msrest.authentication import Authentication
    from os import getenv

    # Allow overriding Kusto resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    kusto_rm_override = getenv('_AZURE_CLI_KUSTO_RM_URI')
    if kusto_rm_override:
        return KustoManagementClient(
            subscription_id=getenv('_AZURE_CLI_KUSTO_SUB_ID'),
            base_url=kusto_rm_override,
            credentials=Authentication())  # No authentication

    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, KustoManagementClient)


def get_kusto_cluster_operations(cli_ctx, _):
    return get_kusto_management_client(cli_ctx).operations.database


def get_kusto_database_operations(cli_ctx, _):
    return get_kusto_management_client(cli_ctx).operations.clusters
