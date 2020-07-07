# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionDailyStats(Model):
    """ExtensionDailyStats.

    :param daily_stats: List of extension statistics data points
    :type daily_stats: list of :class:`ExtensionDailyStat <gallery.v4_0.models.ExtensionDailyStat>`
    :param extension_id: Id of the extension, this will never be sent back to the client. For internal use only.
    :type extension_id: str
    :param extension_name: Name of the extension
    :type extension_name: str
    :param publisher_name: Name of the publisher
    :type publisher_name: str
    :param stat_count: Count of stats
    :type stat_count: int
    """

    _attribute_map = {
        'daily_stats': {'key': 'dailyStats', 'type': '[ExtensionDailyStat]'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'stat_count': {'key': 'statCount', 'type': 'int'}
    }

    def __init__(self, daily_stats=None, extension_id=None, extension_name=None, publisher_name=None, stat_count=None):
        super(ExtensionDailyStats, self).__init__()
        self.daily_stats = daily_stats
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.publisher_name = publisher_name
        self.stat_count = stat_count
