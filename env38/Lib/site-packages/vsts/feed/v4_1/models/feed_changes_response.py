# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedChangesResponse(Model):
    """FeedChangesResponse.

    :param _links:
    :type _links: :class:`ReferenceLinks <packaging.v4_1.models.ReferenceLinks>`
    :param count:
    :type count: int
    :param feed_changes:
    :type feed_changes: list of :class:`FeedChange <packaging.v4_1.models.FeedChange>`
    :param next_feed_continuation_token:
    :type next_feed_continuation_token: long
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'count': {'key': 'count', 'type': 'int'},
        'feed_changes': {'key': 'feedChanges', 'type': '[FeedChange]'},
        'next_feed_continuation_token': {'key': 'nextFeedContinuationToken', 'type': 'long'}
    }

    def __init__(self, _links=None, count=None, feed_changes=None, next_feed_continuation_token=None):
        super(FeedChangesResponse, self).__init__()
        self._links = _links
        self.count = count
        self.feed_changes = feed_changes
        self.next_feed_continuation_token = next_feed_continuation_token
