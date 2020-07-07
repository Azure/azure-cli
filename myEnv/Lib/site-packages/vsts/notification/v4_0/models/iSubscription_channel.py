# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ISubscriptionChannel(Model):
    """ISubscriptionChannel.

    :param type:
    :type type: str
    """

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, type=None):
        super(ISubscriptionChannel, self).__init__()
        self.type = type
