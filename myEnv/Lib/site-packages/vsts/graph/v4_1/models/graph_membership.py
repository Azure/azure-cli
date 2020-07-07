# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphMembership(Model):
    """GraphMembership.

    :param _links: This field contains zero or more interesting links about the graph membership. These links may be invoked to obtain additional relationships or more detailed information about this graph membership.
    :type _links: :class:`ReferenceLinks <graph.v4_1.models.ReferenceLinks>`
    :param container_descriptor:
    :type container_descriptor: str
    :param member_descriptor:
    :type member_descriptor: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'container_descriptor': {'key': 'containerDescriptor', 'type': 'str'},
        'member_descriptor': {'key': 'memberDescriptor', 'type': 'str'}
    }

    def __init__(self, _links=None, container_descriptor=None, member_descriptor=None):
        super(GraphMembership, self).__init__()
        self._links = _links
        self.container_descriptor = container_descriptor
        self.member_descriptor = member_descriptor
