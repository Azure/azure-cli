# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WebInstanceSummaryData(Model):
    """WebInstanceSummaryData.

    :param average:
    :type average: float
    :param max:
    :type max: float
    :param min:
    :type min: float
    """

    _attribute_map = {
        'average': {'key': 'average', 'type': 'float'},
        'max': {'key': 'max', 'type': 'float'},
        'min': {'key': 'min', 'type': 'float'}
    }

    def __init__(self, average=None, max=None, min=None):
        super(WebInstanceSummaryData, self).__init__()
        self.average = average
        self.max = max
        self.min = min
