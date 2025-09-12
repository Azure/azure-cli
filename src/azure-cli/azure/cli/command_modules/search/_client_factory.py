# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_search(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.search import SearchManagementClient
    return get_mgmt_service_client(cli_ctx, SearchManagementClient)


def cf_search_services(cli_ctx, _):
    return cf_search(cli_ctx).services


def cf_search_private_endpoint_connections(cli_ctx, _):
    return cf_search(cli_ctx).private_endpoint_connections


def cf_search_private_link_resources(cli_ctx, _):
    return cf_search(cli_ctx).private_link_resources


def cf_search_shared_private_link_resources(cli_ctx, _):
    return cf_search(cli_ctx).shared_private_link_resources


def cf_search_admin_keys(cli_ctx, _):
    return cf_search(cli_ctx).admin_keys


def cf_search_query_keys(cli_ctx, _):
    return cf_search(cli_ctx).query_keys
