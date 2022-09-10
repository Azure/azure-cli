# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import (get_enum_type, get_three_state_flag)
from azure.mgmt.apimanagement.models import SubscriptionState
from azure.cli.command_modules.apim.operations.subscription.custom import SubscriptionKeyKind

SUBSCRIPTION_TYPES = SubscriptionState
SUBSCRIPTION_KEYS = SubscriptionKeyKind


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim subscription') as c:
        c.argument('sid', arg_group="Subscription", help='Subscription entity Identifier. The entity represents the association between a user and a product in API Management.')
        c.argument('display_name', options_list=['--display-name', '-d'], arg_group='Subscription', help='Subscription name')
        c.argument('owner_id', arg_group='Subscription', help='User (user id path) for whom subscription is being created in form /users/{userId}')
        c.argument('state', get_enum_type(SUBSCRIPTION_TYPES), arg_group='Subscription', help='Initial subscription state. If no value is specified, subscription is created with Submitted state. Possible states are * active – the subscription is active, * suspended – the subscription is blocked, and the subscriber cannot call any APIs of the product, * submitted – the subscription request has been made by the developer, but has not yet been approved or rejected, * rejected – the subscription request has been denied by an administrator, * cancelled – the subscription has been cancelled by the developer or administrator, * expired – the subscription reached its expiration date and was deactivated. Possible values include: \'suspended\', \'active\', \'expired\', \'submitted\', \'rejected\', \'cancelled\'')
        c.argument('allow_tracing', options_list=['--allow-tracing', '-a'], arg_type=get_three_state_flag(), arg_group='Subscription', help='Determines whether tracing can be enabled')
        c.argument('scope', arg_group='Subscription', help='Scope like /products/{productId} or /apis or /apis/{apiId}.')
        c.argument('primary_key', arg_group="Subscription", help='The primary access key for the APIM subscription')
        c.argument('secondary_key', arg_group="Subscription", help='The secondary access key for the APIM subscription')

    for scope in ['apim subscription keys regenerate', 'apim subscription regenerate-key']:
        with commands_loader.argument_context(scope) as c:
            c.argument('key_kind', arg_type=get_enum_type(SUBSCRIPTION_KEYS), help='The type of key to regenerate: primary or secondary')
