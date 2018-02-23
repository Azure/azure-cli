# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.locationbasedservices.models import LocationBasedServicesAccountCreateParameters, Sku


# pylint: disable=line-too-long
def create(client, resource_group_name, account_name, sku_name='S0', tags=None, custom_headers=None,
           raw=False):
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
    :param dict custom_headers: headers that will be added to the request
    :param bool raw: returns the direct response alongside the
     deserialized response
    :return: LocationBasedServicesAccount or ClientRawResponse if raw=true
    :rtype:
     ~azure.mgmt.locationbasedservices.models.LocationBasedServicesAccount
     or ~msrest.pipeline.ClientRawResponse
    :raises:
     :class:`ErrorException<azure.mgmt.locationbasedservices.models.ErrorException>`
    """

    sku = Sku(sku_name)
    lbs_account_create_params = LocationBasedServicesAccountCreateParameters('global', sku, tags)
    return client.create_or_update(resource_group_name, account_name, lbs_account_create_params, custom_headers, raw)


def list_accounts(client, resource_group_name=None, custom_headers=None, raw=False):
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
    if resource_group_name is None:
        return client.list_by_subscription(custom_headers, raw)
    return client.list_by_resource_group(resource_group_name, custom_headers, raw)
