# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CodeChangeTrendItem(Model):
    """CodeChangeTrendItem.

    :param time:
    :type time: datetime
    :param value:
    :type value: int
    """

    _attribute_map = {
        'time': {'key': 'time', 'type': 'iso-8601'},
        'value': {'key': 'value', 'type': 'int'}
    }

    def __init__(self, time=None, value=None):
        super(CodeChangeTrendItem, self).__init__()
        self.time = time
        self.value = value
