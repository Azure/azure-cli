# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FilterGroup(Model):
    """FilterGroup.

    :param end:
    :type end: int
    :param level:
    :type level: int
    :param start:
    :type start: int
    """

    _attribute_map = {
        'end': {'key': 'end', 'type': 'int'},
        'level': {'key': 'level', 'type': 'int'},
        'start': {'key': 'start', 'type': 'int'}
    }

    def __init__(self, end=None, level=None, start=None):
        super(FilterGroup, self).__init__()
        self.end = end
        self.level = level
        self.start = start
