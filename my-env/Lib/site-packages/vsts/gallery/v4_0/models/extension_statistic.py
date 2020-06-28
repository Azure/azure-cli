# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionStatistic(Model):
    """ExtensionStatistic.

    :param statistic_name:
    :type statistic_name: str
    :param value:
    :type value: float
    """

    _attribute_map = {
        'statistic_name': {'key': 'statisticName', 'type': 'str'},
        'value': {'key': 'value', 'type': 'float'}
    }

    def __init__(self, statistic_name=None, value=None):
        super(ExtensionStatistic, self).__init__()
        self.statistic_name = statistic_name
        self.value = value
