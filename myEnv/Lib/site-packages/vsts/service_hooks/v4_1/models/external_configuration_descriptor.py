# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExternalConfigurationDescriptor(Model):
    """ExternalConfigurationDescriptor.

    :param create_subscription_url: Url of the site to create this type of subscription.
    :type create_subscription_url: str
    :param edit_subscription_property_name: The name of an input property that contains the URL to edit a subscription.
    :type edit_subscription_property_name: str
    :param hosted_only: True if the external configuration applies only to hosted.
    :type hosted_only: bool
    """

    _attribute_map = {
        'create_subscription_url': {'key': 'createSubscriptionUrl', 'type': 'str'},
        'edit_subscription_property_name': {'key': 'editSubscriptionPropertyName', 'type': 'str'},
        'hosted_only': {'key': 'hostedOnly', 'type': 'bool'}
    }

    def __init__(self, create_subscription_url=None, edit_subscription_property_name=None, hosted_only=None):
        super(ExternalConfigurationDescriptor, self).__init__()
        self.create_subscription_url = create_subscription_url
        self.edit_subscription_property_name = edit_subscription_property_name
        self.hosted_only = hosted_only
