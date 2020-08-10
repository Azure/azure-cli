# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionChannelWithAddress(Model):
    """SubscriptionChannelWithAddress.

    :param address:
    :type address: str
    :param type:
    :type type: str
    :param use_custom_address:
    :type use_custom_address: bool
    """

    _attribute_map = {
        'address': {'key': 'address', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'use_custom_address': {'key': 'useCustomAddress', 'type': 'bool'}
    }

    def __init__(self, address=None, type=None, use_custom_address=None):
        super(SubscriptionChannelWithAddress, self).__init__()
        self.address = address
        self.type = type
        self.use_custom_address = use_custom_address
