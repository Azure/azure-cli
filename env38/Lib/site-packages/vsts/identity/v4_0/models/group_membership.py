# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GroupMembership(Model):
    """GroupMembership.

    :param active:
    :type active: bool
    :param descriptor:
    :type descriptor: :class:`str <identities.v4_0.models.str>`
    :param id:
    :type id: str
    :param queried_id:
    :type queried_id: str
    """

    _attribute_map = {
        'active': {'key': 'active', 'type': 'bool'},
        'descriptor': {'key': 'descriptor', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'queried_id': {'key': 'queriedId', 'type': 'str'}
    }

    def __init__(self, active=None, descriptor=None, id=None, queried_id=None):
        super(GroupMembership, self).__init__()
        self.active = active
        self.descriptor = descriptor
        self.id = id
        self.queried_id = queried_id
