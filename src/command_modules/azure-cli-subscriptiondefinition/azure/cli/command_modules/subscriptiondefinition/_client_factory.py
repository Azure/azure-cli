# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

scope_subscription_prefix = "subscriptions/";
scope_management_group_prefix = "providers/Microsoft.Management/managementGroups/";

def subscriptiondefinition_client_factory(management_group_id=None, subscription_id=None, **_):
    from azure.cli.core.commands.client_factory import _get_mgmt_service_client
    from azure.mgmt.subscriptiondefinition import SubscriptionDefinitionClient
    scope = _build_scope(management_group_id, subscription_id)
    client, default_subscription_id = _get_mgmt_service_client(SubscriptionDefinitionClient, subscription_bound=False, scope=scope)
    return client

def _build_scope(management_group_id=None, subscription_id=None):
    if management_group_id and subscription_id:
        raise CLIError("cannot specify both management_group_id and subscription_id")
    if management_group_id:
        return scope_management_group_prefix + management_group_id
    if subscription_id:
        return scope_subscription_prefix + subscription_id
    raise CLIError("either management_group_id or subscription_id needs to be specified")
