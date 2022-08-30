# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import (get_enum_type, get_three_state_flag)
from azure.mgmt.apimanagement.models import ProductState

STATE_TYPES = ProductState


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim product') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the API Management service instance", id_part=None)
        c.argument('product_id', options_list=['--product-id', '-p'], help='Product identifier. Must be unique in the current API Management service instance.')
        c.argument('display_name', help='Product display name. The display name of the product. If left empty, defaults to the product\'s Id.')
        c.argument('description', options_list=['--description', '-d'], help='Product description. May include HTML formatting tags.')
        c.argument('terms', help='Product legal terms of use. Developers trying to subscribe to the product will be presented and required to accept these terms before they can complete the subscription process.')
        c.argument('subscription_required', options_list=['--subscription-required', '-s'], arg_type=get_three_state_flag(), help='Whether a product subscription is required for accessing APIs included in this product. If true, the product is referred to as "protected" and a valid subscription key is required for a request to an API included in the product to succeed. If false, the product is referred to as "open" and requests to an API included in the product can be made without a subscription key. If property is omitted when creating a new product its value is assumed to be true.')
        c.argument('approval_required', arg_type=get_three_state_flag(), help='Whether subscription approval is required. If false, new subscriptions will be approved automatically enabling developers to call the product’s APIs immediately after subscribing. If true, administrators must manually approve the subscription before the developer can any of the product’s APIs. Can be present only if subscriptionRequired property is present and has a value of false.')
        c.argument('subscriptions_limit', type=int, help='Whether the number of subscriptions a user can have to this product at the same time. Set to null or omit to allow unlimited per user subscriptions. Can be present only if --subscription-required is present and has a value of false.')
        c.argument('state', get_enum_type(STATE_TYPES), help='Whether product is published or not. Published products are discoverable by users of developer portal. Non published products are visible only to administrators. Default state of Product is notPublished.')
        c.argument('if_match', help='ETag of the integration runtime entity. Should only be specified for update, for '
                   'which it should match existing entity or can be * for unconditional update.')

    with commands_loader.argument_context('apim product') as c:
        c.argument('delete_subscriptions', arg_type=get_three_state_flag(), help="Whether to delete the product's subscriptions. Default is true.")
