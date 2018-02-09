# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def cf_managementgroups(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.managementgroups import ManagementGroupsAPI
    return get_mgmt_service_client(cli_ctx, ManagementGroupsAPI, subscription_bound=False)

def management_groups_client_factory(cli_ctx, _):
    return cf_managementgroups(cli_ctx).management_groups

def management_group_subscriptions_client_factory(cli_ctx, _):
    return cf_managementgroups(cli_ctx).management_group_subscriptions

