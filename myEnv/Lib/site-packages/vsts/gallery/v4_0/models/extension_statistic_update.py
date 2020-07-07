# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionStatisticUpdate(Model):
    """ExtensionStatisticUpdate.

    :param extension_name:
    :type extension_name: str
    :param operation:
    :type operation: object
    :param publisher_name:
    :type publisher_name: str
    :param statistic:
    :type statistic: :class:`ExtensionStatistic <gallery.v4_0.models.ExtensionStatistic>`
    """

    _attribute_map = {
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'operation': {'key': 'operation', 'type': 'object'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'statistic': {'key': 'statistic', 'type': 'ExtensionStatistic'}
    }

    def __init__(self, extension_name=None, operation=None, publisher_name=None, statistic=None):
        super(ExtensionStatisticUpdate, self).__init__()
        self.extension_name = extension_name
        self.operation = operation
        self.publisher_name = publisher_name
        self.statistic = statistic
