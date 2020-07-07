# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BaseSubscriptionFilter(Model):
    """BaseSubscriptionFilter.

    :param event_type:
    :type event_type: str
    :param type:
    :type type: str
    """

    _attribute_map = {
        'event_type': {'key': 'eventType', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, event_type=None, type=None):
        super(BaseSubscriptionFilter, self).__init__()
        self.event_type = event_type
        self.type = type
