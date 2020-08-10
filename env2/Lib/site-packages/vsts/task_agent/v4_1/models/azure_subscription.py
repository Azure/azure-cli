# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AzureSubscription(Model):
    """AzureSubscription.

    :param display_name:
    :type display_name: str
    :param subscription_id:
    :type subscription_id: str
    :param subscription_tenant_id:
    :type subscription_tenant_id: str
    :param subscription_tenant_name:
    :type subscription_tenant_name: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'subscription_id': {'key': 'subscriptionId', 'type': 'str'},
        'subscription_tenant_id': {'key': 'subscriptionTenantId', 'type': 'str'},
        'subscription_tenant_name': {'key': 'subscriptionTenantName', 'type': 'str'}
    }

    def __init__(self, display_name=None, subscription_id=None, subscription_tenant_id=None, subscription_tenant_name=None):
        super(AzureSubscription, self).__init__()
        self.display_name = display_name
        self.subscription_id = subscription_id
        self.subscription_tenant_id = subscription_tenant_id
        self.subscription_tenant_name = subscription_tenant_name
