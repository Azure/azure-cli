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


def cf_afd_profiles(cli_ctx, _):
    return cf_cdn(cli_ctx).afd_profiles


def cf_origins(cli_ctx, _):
    return cf_cdn(cli_ctx).origins


def cf_origin_groups(cli_ctx, _):
    return cf_cdn(cli_ctx).origin_groups


def cf_resource_usage(cli_ctx, _):
    return cf_cdn(cli_ctx).resource_usage


def cf_edge_nodes(cli_ctx, _):
    return cf_cdn(cli_ctx).edge_nodes


def cf_waf_policy(cli_ctx, _):
    return cf_cdn(cli_ctx).policies


def cf_waf_rule_set(cli_ctx, _):
    return cf_cdn(cli_ctx).managed_rule_sets


def cf_afd_endpoints(cli_ctx, _):
    return cf_cdn(cli_ctx).afd_endpoints


def cf_afd_origin_groups(cli_ctx, _):
    return cf_cdn(cli_ctx).afd_origin_groups


def cf_afd_origins(cli_ctx, _):
    return cf_cdn(cli_ctx).afd_origins


def cf_afd_routes(cli_ctx, _):
    return cf_cdn(cli_ctx).routes


def cf_afd_rule_sets(cli_ctx, _):
    return cf_cdn(cli_ctx).rule_sets


def cf_afd_rules(cli_ctx, _):
    return cf_cdn(cli_ctx).rules


def cf_afd_security_policies(cli_ctx, _):
    return cf_cdn(cli_ctx).security_policies


def cf_afd_custom_domain(cli_ctx, _):
    return cf_cdn(cli_ctx).afd_custom_domains


def cf_afd_secrets(cli_ctx, _):
    return cf_cdn(cli_ctx).secrets


def cf_afd_log_analytics(cli_ctx, _):
    return cf_cdn(cli_ctx).log_analytics
