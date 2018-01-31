# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_subscription(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import _get_mgmt_service_client
    from azure.mgmt.subscription import SubscriptionClient
    client, _ = _get_mgmt_service_client(cli_ctx, SubscriptionClient, subscription_bound=False)
    return client


def subscription_definitions_mgmt_client_factory(cli_ctx, kwargs):
    return cf_subscription(cli_ctx, **kwargs).subscription_definitions
