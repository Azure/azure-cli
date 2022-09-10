# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.command_modules.apim._util import get_if_match
from azure.mgmt.apimanagement.models import ProductContract


def list_product(client, resource_group_name, service_name):
    """Lists a collection of products in the specified service instance. """
    return client.list_by_service(resource_group_name, service_name)


def get_product(client, resource_group_name, service_name, product_id):
    """Gets the details of the product specified by its identifier. """
    return client.get(resource_group_name, service_name, product_id)


def delete_product(client, resource_group_name, service_name, product_id, delete_subscriptions=True, if_match=None):
    """Delete product. """
    return client.delete(resource_group_name, service_name, product_id, delete_subscriptions=delete_subscriptions, if_match=get_if_match(if_match))


def create_product(client, resource_group_name, service_name, product_id, display_name=None, description=None, terms=None,
                   subscription_required=None, approval_required=None, subscriptions_limit=None, state=None):
    """Creates a product. """
    # Request Header If-Match
    if_match = '*'

    resource = ProductContract(
        display_name=display_name if not None else product_id
    )
    if description is not None:
        resource.description = description

    if terms is not None:
        resource.terms = terms

    if subscription_required is not None:
        resource.subscription_required = subscription_required

    if approval_required is not None:
        resource.approval_required = approval_required

    if subscriptions_limit is not None:
        resource.subscriptions_limit = subscriptions_limit

    if state is not None:
        resource.state = state

    return client.create_or_update(resource_group_name, service_name, product_id, resource, if_match)


def update_product(instance, display_name=None, description=None, terms=None, subscription_required=None, approval_required=None,
                   subscriptions_limit=None, state=None):
    """Update existing product details. """
    # Request Header If-Match (must be handled with custom function, not built in pass-through since it's a separate param of the SDK client)
#    if_match = '*'

    if display_name is not None:
        instance.display_name = display_name

    if description is not None:
        instance.description = description

    if terms is not None:
        instance.terms = terms

    if subscription_required is not None:
        instance.subscription_required = subscription_required

    if approval_required is not None:
        instance.approval_required = approval_required

    if subscriptions_limit is not None:
        instance.subscriptions_limit = subscriptions_limit

    if state is not None:
        instance.state = state

    return instance
