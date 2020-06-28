# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GroupOption(Model):
    """GroupOption.

    :param access_level: Access Level
    :type access_level: :class:`AccessLevel <member-entitlement-management.v4_1.models.AccessLevel>`
    :param group: Group
    :type group: :class:`Group <member-entitlement-management.v4_1.models.Group>`
    """

    _attribute_map = {
        'access_level': {'key': 'accessLevel', 'type': 'AccessLevel'},
        'group': {'key': 'group', 'type': 'Group'}
    }

    def __init__(self, access_level=None, group=None):
        super(GroupOption, self).__init__()
        self.access_level = access_level
        self.group = group
