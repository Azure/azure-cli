# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _cf_policy_insights(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.policyinsights import PolicyInsightsClient

    return get_mgmt_service_client(cli_ctx, PolicyInsightsClient, subscription_bound=False)


def policy_events_operations(cli_ctx, _):
    return _cf_policy_insights(cli_ctx).policy_events


def policy_states_operations(cli_ctx, _):
    return _cf_policy_insights(cli_ctx).policy_states
