# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from azure.mgmt.subscriptiondefinition import SubscriptionDefinitionClient
from azure.mgmt.subscriptiondefinition.models import *
from ._client_factory import subscriptiondefinition_client_factory

scope_subscription_prefix = "subscriptions/";
scope_subscription_definition_name = "default";
scope_management_group_prefix = "providers/Microsoft.Management/managementGroups/";

def list_subscriptiondefinitions(management_group_id):
    """List all available invoices of the subscription"""
    sub_defs = subscriptiondefinition_client_factory().subscription_definitions
    sub_defs.config.scope = _build_scope(management_group_id)
    return list(sub_defs.list())


def get_subscriptiondefinition(management_group_id=None, name=None, subscription_id=None):
    """Retrieve subscription definition for the specified subscription."""
    sub_defs = subscriptiondefinition_client_factory().subscription_definitions
    sub_defs.config.scope = _build_scope(management_group_id, subscription_id)
    sub_defs.config.subscription_definition_name = scope_subscription_definition_name if subscription_id else name
    return sub_defs.get()


def create_subscriptiondefinition(management_group_id, name, offer_type, subscription_display_name=None):
    """Create a subscription definition."""
    sub_defs = subscriptiondefinition_client_factory().subscription_definitions
    sub_defs.config.scope = _build_scope(management_group_id)
    sub_defs.config.subscription_definition_name = name

    new_def = SubscriptionDefinitionModel(
        subscription_display_name=subscription_display_name if subscription_display_name else name,
        rating_context=SubscriptionDefinitionPropertiesRatingContext(offer_type))

    return sub_defs.create(new_def)

def _build_scope(management_group_id=None, subscription_id=None):
    if management_group_id and subscription_id:
        raise CLIError("cannot specify both management_group_id and subscription_id")
    if management_group_id:
        return scope_management_group_prefix + management_group_id
    if subscription_id:
        return scope_subscription_prefix + subscription_id
    raise CLIError("either management_group_id or subscription_id needs to be specified")