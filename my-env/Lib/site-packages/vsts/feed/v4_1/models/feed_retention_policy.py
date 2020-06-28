# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedRetentionPolicy(Model):
    """FeedRetentionPolicy.

    :param age_limit_in_days:
    :type age_limit_in_days: int
    :param count_limit:
    :type count_limit: int
    """

    _attribute_map = {
        'age_limit_in_days': {'key': 'ageLimitInDays', 'type': 'int'},
        'count_limit': {'key': 'countLimit', 'type': 'int'}
    }

    def __init__(self, age_limit_in_days=None, count_limit=None):
        super(FeedRetentionPolicy, self).__init__()
        self.age_limit_in_days = age_limit_in_days
        self.count_limit = count_limit
