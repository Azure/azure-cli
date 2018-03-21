# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError

from azure.mgmt.locationbasedservices.models import (
    LocationBasedServicesAccountCreateParameters,
    Sku)

ACCOUNT_LOCATION = 'global'

logger = get_logger(__name__)


# pylint: disable=line-too-long
def create_account(client, resource_group_name, account_name, sku_name='S0', tags=None, agree=None):
    """Create a Location Based Services Account. A Location Based
    Services Account holds the keys which allow access to the Location
    Based Services REST APIs.

    :param resource_group_name: The name of the Azure Resource Group.
    :type resource_group_name: str
    :param account_name: The name of the Location Based Services Account.
    :type account_name: str
    :param sku_name: The name of the SKU, in standard format (such as S0).
    :type sku_name: str
    :param tags: Gets or sets a list of key value pairs that describe the
     resource. These tags can be used in viewing and grouping this resource
     (across resource groups). A maximum of 15 tags can be provided for a
     resource. Each tag must have a key no greater than 128 characters and
     value no greater than 256 characters.
    :type tags: dict[str, str]
    :param agree: If true, user agrees to the Preview Terms. Ignore prompt
     for confirmation. False otherwise.
    :type agree: bool
    :return: LocationBasedServicesAccount
    :rtype:
     ~azure.mgmt.locationbasedservices.models.LocationBasedServicesAccount
    :raises:
     :class:`ErrorException<azure.mgmt.locationbasedservices.models.ErrorException>`
    """
    # Prompt for the Preview Terms agreement.
    warning_msg = 'By creating a Location Based Services account, you agree to the Microsoft Azure Preview Terms.' + \
                  '\nThe Preview Terms can be found at: ' + \
                  '\nhttps://azure.microsoft.com/en-us/support/legal/preview-supplemental-terms/'
    logger.warning(warning_msg)

    if not agree:  # ... in order to pass ScenarioTest
        response = prompt_y_n('I confirm that I have read and agree to the Microsoft Azure Preview Terms.')
        if not response:
            raise CLIError('You must agree to the Microsoft Azure Preview Terms to create an account.')

    # Proceed if user has agreed to the Preview Terms.
    sku = Sku(sku_name)
    lbs_account_create_params = LocationBasedServicesAccountCreateParameters(ACCOUNT_LOCATION, sku, tags)
    return client.create_or_update(resource_group_name, account_name, lbs_account_create_params)


def list_accounts(client, resource_group_name=None):
    """Get all Location Based Services Accounts in a Resource Group OR in a Subscription.

    :param resource_group_name: The name of the Azure Resource Group.
    :type resource_group_name: str
    :param dict custom_headers: headers that will be added to the request
    :param bool raw: returns the direct response alongside the
     deserialized response
    :param operation_config: :ref:`Operation configuration
     overrides<msrest:optionsforoperations>`.
    :return: An iterator like instance of LocationBasedServicesAccount
    :rtype:
     ~azure.mgmt.locationbasedservices.models.LocationBasedServicesAccountPaged[~azure.mgmt.locationbasedservices.models.LocationBasedServicesAccount]
    :raises:
     :class:`ErrorException<azure.mgmt.locationbasedservices.models.ErrorException>`
    """
    # Retrieve accounts via subscription
    if resource_group_name is None:
        return client.list_by_subscription()
    # Retrieve accounts via resource group
    return client.list_by_resource_group(resource_group_name)


def generic_update_account(instance, sku_name=None, tags=None):
    """Create a LocationBasedServicesCreateParameters from old account instance
    with new sku_name and tags. This function is called from the
    generic_update_command(...) in commands.py .

    :param sku_name: The name of the SKU, in standard format (such as S0).
    :type sku_name: str
    :param tags: Gets or sets a list of key value pairs that describe the
     resource. These tags can be used in viewing and grouping this resource
     (across resource groups). A maximum of 15 tags can be provided for a
     resource. Each tag must have a key no greater than 128 characters and
     value no greater than 256 characters.
    :type tags: dict[str, str]
    :return: LocationBasedServicesAccountCreateParameters
    :rtype:
     ~azure.mgmt.locationbasedservices.models.LocationBasedServicesAccountCreateParameters
    """
    # Pre-populate with old instance
    lbs_account_create_params = LocationBasedServicesAccountCreateParameters(ACCOUNT_LOCATION, instance.sku,
                                                                             instance.tags)
    # Update fields with new parameter values
    if sku_name:
        lbs_account_create_params.sku.name = sku_name
    if tags:
        lbs_account_create_params.tags = tags
    return lbs_account_create_params
