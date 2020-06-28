# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionEvent(Model):
    """ExtensionEvent.

    :param id: Id which identifies each data point uniquely
    :type id: long
    :param properties:
    :type properties: :class:`object <gallery.v4_1.models.object>`
    :param statistic_date: Timestamp of when the event occurred
    :type statistic_date: datetime
    :param version: Version of the extension
    :type version: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'long'},
        'properties': {'key': 'properties', 'type': 'object'},
        'statistic_date': {'key': 'statisticDate', 'type': 'iso-8601'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, id=None, properties=None, statistic_date=None, version=None):
        super(ExtensionEvent, self).__init__()
        self.id = id
        self.properties = properties
        self.statistic_date = statistic_date
        self.version = version
