# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from azure.mgmt.subscriptiondefinition import SubscriptionDefinitionClient
from azure.mgmt.subscriptiondefinition.models import *
from ._client_factory import subscriptiondefinition_client_factory

scope_subscription_definition_name = "default";

def list_subscriptiondefinitions(management_group_id):
    """List all available invoices of the subscription"""
    sub_defs = subscriptiondefinition_client_factory(management_group_id).subscription_definitions
    return list(sub_defs.list())


def get_subscriptiondefinition(management_group_id=None, name=None, subscription_id=None):
    """Retrieve subscription definition for the specified subscription."""
    sub_defs = subscriptiondefinition_client_factory(management_group_id, subscription_id).subscription_definitions
    sub_defs.config.subscription_definition_name = scope_subscription_definition_name if subscription_id else name
    return sub_defs.get()


def create_subscriptiondefinition(management_group_id, name, offer_type, subscription_display_name=None):
    """Create a subscription definition."""
    sub_defs = subscriptiondefinition_client_factory(management_group_id).subscription_definitions
    sub_defs.config.subscription_definition_name = name

    new_def = SubscriptionDefinitionModel(
        subscription_display_name=subscription_display_name if subscription_display_name else name,
        rating_context=SubscriptionDefinitionPropertiesRatingContext(offer_type))

    return sub_defs.create(name, new_def)
