# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DateRange(Model):
    """DateRange.

    :param end: End of the date range.
    :type end: datetime
    :param start: Start of the date range.
    :type start: datetime
    """

    _attribute_map = {
        'end': {'key': 'end', 'type': 'iso-8601'},
        'start': {'key': 'start', 'type': 'iso-8601'}
    }

    def __init__(self, end=None, start=None):
        super(DateRange, self).__init__()
        self.end = end
        self.start = start
