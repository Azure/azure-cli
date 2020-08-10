# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedChange(Model):
    """FeedChange.

    :param change_type:
    :type change_type: object
    :param feed:
    :type feed: :class:`Feed <packaging.v4_1.models.Feed>`
    :param feed_continuation_token:
    :type feed_continuation_token: long
    :param latest_package_continuation_token:
    :type latest_package_continuation_token: long
    """

    _attribute_map = {
        'change_type': {'key': 'changeType', 'type': 'object'},
        'feed': {'key': 'feed', 'type': 'Feed'},
        'feed_continuation_token': {'key': 'feedContinuationToken', 'type': 'long'},
        'latest_package_continuation_token': {'key': 'latestPackageContinuationToken', 'type': 'long'}
    }

    def __init__(self, change_type=None, feed=None, feed_continuation_token=None, latest_package_continuation_token=None):
        super(FeedChange, self).__init__()
        self.change_type = change_type
        self.feed = feed
        self.feed_continuation_token = feed_continuation_token
        self.latest_package_continuation_token = latest_package_continuation_token
