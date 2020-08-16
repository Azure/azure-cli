# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_cdn(cli_ctx, *kwargs):  # pylint: disable=unused-argument
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.cdn import CdnManagementClient
    return get_mgmt_service_client(cli_ctx, CdnManagementClient)


def cf_custom_domain(cli_ctx, _):
    return cf_cdn(cli_ctx).custom_domains


def cf_endpoints(cli_ctx, _):
    return cf_cdn(cli_ctx).endpoints


def cf_profiles(cli_ctx, _):
    return cf_cdn(cli_ctx).profiles


def cf_origins(cli_ctx, _):
    return cf_cdn(cli_ctx).origins


def cf_resource_usage(cli_ctx, _):
    return cf_cdn(cli_ctx).resource_usage


def cf_edge_nodes(cli_ctx, _):
    return cf_cdn(cli_ctx).edge_nodes


def cf_waf_policy(cli_ctx, _):
    return cf_cdn(cli_ctx).policies


def cf_waf_rule_set(cli_ctx, _):
    return cf_cdn(cli_ctx).managed_rule_sets
