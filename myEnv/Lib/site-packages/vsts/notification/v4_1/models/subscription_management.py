# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionManagement(Model):
    """SubscriptionManagement.

    :param service_instance_type:
    :type service_instance_type: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'service_instance_type': {'key': 'serviceInstanceType', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, service_instance_type=None, url=None):
        super(SubscriptionManagement, self).__init__()
        self.service_instance_type = service_instance_type
        self.url = url
