# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from azure.mgmt.subscription.models import SubscriptionDefinition

def create_subscription_definition(client, name, offer_type, subscription_display_name=None):
    """Create a subscription definition."""
    new_def = SubscriptionDefinition(
        subscription_display_name=subscription_display_name if subscription_display_name else name,
        offer_type=offer_type)

    return client.create(name, new_def)
