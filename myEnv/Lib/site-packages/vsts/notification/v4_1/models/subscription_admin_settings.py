# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionAdminSettings(Model):
    """SubscriptionAdminSettings.

    :param block_user_opt_out: If true, members of the group subscribed to the associated subscription cannot opt (choose not to get notified)
    :type block_user_opt_out: bool
    """

    _attribute_map = {
        'block_user_opt_out': {'key': 'blockUserOptOut', 'type': 'bool'}
    }

    def __init__(self, block_user_opt_out=None):
        super(SubscriptionAdminSettings, self).__init__()
        self.block_user_opt_out = block_user_opt_out
