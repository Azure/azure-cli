# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiPageViewStats(Model):
    """WikiPageViewStats.

    :param count: Wiki page view count.
    :type count: int
    :param last_viewed_time: Wiki page last viewed time.
    :type last_viewed_time: datetime
    :param path: Wiki page path.
    :type path: str
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'last_viewed_time': {'key': 'lastViewedTime', 'type': 'iso-8601'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, count=None, last_viewed_time=None, path=None):
        super(WikiPageViewStats, self).__init__()
        self.count = count
        self.last_viewed_time = last_viewed_time
        self.path = path
