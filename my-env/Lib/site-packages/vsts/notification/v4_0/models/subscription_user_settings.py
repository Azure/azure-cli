# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionUserSettings(Model):
    """SubscriptionUserSettings.

    :param opted_out: Indicates whether the user will receive notifications for the associated group subscription.
    :type opted_out: bool
    """

    _attribute_map = {
        'opted_out': {'key': 'optedOut', 'type': 'bool'}
    }

    def __init__(self, opted_out=None):
        super(SubscriptionUserSettings, self).__init__()
        self.opted_out = opted_out
