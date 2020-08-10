# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RetentionPolicy(Model):
    """RetentionPolicy.

    :param days_to_keep:
    :type days_to_keep: int
    """

    _attribute_map = {
        'days_to_keep': {'key': 'daysToKeep', 'type': 'int'}
    }

    def __init__(self, days_to_keep=None):
        super(RetentionPolicy, self).__init__()
        self.days_to_keep = days_to_keep
