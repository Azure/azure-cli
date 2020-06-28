# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionDailyStat(Model):
    """ExtensionDailyStat.

    :param counts: Stores the event counts
    :type counts: :class:`EventCounts <gallery.v4_1.models.EventCounts>`
    :param extended_stats: Generic key/value pair to store extended statistics. Used for sending paid extension stats like Upgrade, Downgrade, Cancel trend etc.
    :type extended_stats: dict
    :param statistic_date: Timestamp of this data point
    :type statistic_date: datetime
    :param version: Version of the extension
    :type version: str
    """

    _attribute_map = {
        'counts': {'key': 'counts', 'type': 'EventCounts'},
        'extended_stats': {'key': 'extendedStats', 'type': '{object}'},
        'statistic_date': {'key': 'statisticDate', 'type': 'iso-8601'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, counts=None, extended_stats=None, statistic_date=None, version=None):
        super(ExtensionDailyStat, self).__init__()
        self.counts = counts
        self.extended_stats = extended_stats
        self.statistic_date = statistic_date
        self.version = version
