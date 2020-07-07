# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphMembershipState(Model):
    """GraphMembershipState.

    :param _links: This field contains zero or more interesting links about the graph membership state. These links may be invoked to obtain additional relationships or more detailed information about this graph membership state.
    :type _links: :class:`ReferenceLinks <graph.v4_1.models.ReferenceLinks>`
    :param active: When true, the membership is active
    :type active: bool
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'active': {'key': 'active', 'type': 'bool'}
    }

    def __init__(self, _links=None, active=None):
        super(GraphMembershipState, self).__init__()
        self._links = _links
        self.active = active
