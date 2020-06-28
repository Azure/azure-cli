# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointExecutionOwner(Model):
    """ServiceEndpointExecutionOwner.

    :param _links:
    :type _links: :class:`ReferenceLinks <service-endpoint.v4_1.models.ReferenceLinks>`
    :param id: Gets or sets the Id of service endpoint execution owner.
    :type id: int
    :param name: Gets or sets the name of service endpoint execution owner.
    :type name: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, _links=None, id=None, name=None):
        super(ServiceEndpointExecutionOwner, self).__init__()
        self._links = _links
        self.id = id
        self.name = name
