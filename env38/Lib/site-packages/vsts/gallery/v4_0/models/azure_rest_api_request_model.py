# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AzureRestApiRequestModel(Model):
    """AzureRestApiRequestModel.

    :param asset_details: Gets or sets the Asset details
    :type asset_details: :class:`AssetDetails <gallery.v4_0.models.AssetDetails>`
    :param asset_id: Gets or sets the asset id
    :type asset_id: str
    :param asset_version: Gets or sets the asset version
    :type asset_version: long
    :param customer_support_email: Gets or sets the customer support email
    :type customer_support_email: str
    :param integration_contact_email: Gets or sets the integration contact email
    :type integration_contact_email: str
    :param operation: Gets or sets the asset version
    :type operation: str
    :param plan_id: Gets or sets the plan identifier if any.
    :type plan_id: str
    :param publisher_id: Gets or sets the publisher id
    :type publisher_id: str
    :param type: Gets or sets the resource type
    :type type: str
    """

    _attribute_map = {
        'asset_details': {'key': 'assetDetails', 'type': 'AssetDetails'},
        'asset_id': {'key': 'assetId', 'type': 'str'},
        'asset_version': {'key': 'assetVersion', 'type': 'long'},
        'customer_support_email': {'key': 'customerSupportEmail', 'type': 'str'},
        'integration_contact_email': {'key': 'integrationContactEmail', 'type': 'str'},
        'operation': {'key': 'operation', 'type': 'str'},
        'plan_id': {'key': 'planId', 'type': 'str'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, asset_details=None, asset_id=None, asset_version=None, customer_support_email=None, integration_contact_email=None, operation=None, plan_id=None, publisher_id=None, type=None):
        super(AzureRestApiRequestModel, self).__init__()
        self.asset_details = asset_details
        self.asset_id = asset_id
        self.asset_version = asset_version
        self.customer_support_email = customer_support_email
        self.integration_contact_email = integration_contact_email
        self.operation = operation
        self.plan_id = plan_id
        self.publisher_id = publisher_id
        self.type = type
