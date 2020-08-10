# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CounterGroup(Model):
    """CounterGroup.

    :param group_name:
    :type group_name: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'group_name': {'key': 'groupName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, group_name=None, url=None):
        super(CounterGroup, self).__init__()
        self.group_name = group_name
        self.url = url
