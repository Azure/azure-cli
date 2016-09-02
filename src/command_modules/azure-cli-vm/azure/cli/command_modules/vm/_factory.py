#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import (
    get_mgmt_service_client,
    get_subscription_service_client)

from azure.mgmt.compute import ComputeManagementClient

def _compute_client_factory(**_):
    return get_mgmt_service_client(ComputeManagementClient)

def _subscription_client_factory(**_):
    from azure.mgmt.resource.subscriptions import SubscriptionClient
    return get_subscription_service_client(SubscriptionClient)
