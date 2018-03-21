# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from azure.mgmt.locationbasedservices.models import (
    LocationBasedServicesAccountCreateParameters,
    Sku)

ACCOUNT_LOCATION = 'global'

logger = get_logger(__name__)


# pylint: disable=line-too-long
def create_account(client, resource_group_name, account_name, sku_name='S0', tags=None):
    sku = Sku(sku_name)
    lbs_account_create_params = LocationBasedServicesAccountCreateParameters(ACCOUNT_LOCATION, sku, tags)
    return client.create_or_update(resource_group_name, account_name, lbs_account_create_params)


def list_accounts(client, resource_group_name=None):
    # Retrieve accounts via subscription
    if resource_group_name is None:
        return client.list_by_subscription()
    # Retrieve accounts via resource group
    return client.list_by_resource_group(resource_group_name)


def generic_update_account(instance, sku_name=None, tags=None):
    # Pre-populate with old instance
    lbs_account_create_params = LocationBasedServicesAccountCreateParameters(ACCOUNT_LOCATION, instance.sku,
                                                                             instance.tags)
    # Update fields with new parameter values
    if sku_name:
        lbs_account_create_params.sku.name = sku_name
    if tags:
        lbs_account_create_params.tags = tags
    return lbs_account_create_params
