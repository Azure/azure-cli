# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_subscription_definitions(_):
    from azure.cli.core.commands.client_factory import _get_mgmt_service_client
    from azure.mgmt.subscription import SubscriptionClient
    client, _ = _get_mgmt_service_client(SubscriptionClient, subscription_bound=False)
    return client.subscription_definitions
