# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamFieldValue(Model):
    """TeamFieldValue.

    :param include_children:
    :type include_children: bool
    :param value:
    :type value: str
    """

    _attribute_map = {
        'include_children': {'key': 'includeChildren', 'type': 'bool'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, include_children=None, value=None):
        super(TeamFieldValue, self).__init__()
        self.include_children = include_children
        self.value = value
