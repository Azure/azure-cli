# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Group(Model):
    """Group.

    :param display_name: Display Name of the Group
    :type display_name: str
    :param group_type: Group Type
    :type group_type: object
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'group_type': {'key': 'groupType', 'type': 'object'}
    }

    def __init__(self, display_name=None, group_type=None):
        super(Group, self).__init__()
        self.display_name = display_name
        self.group_type = group_type
