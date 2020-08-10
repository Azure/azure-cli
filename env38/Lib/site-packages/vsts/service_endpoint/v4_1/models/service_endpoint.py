# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpoint(Model):
    """ServiceEndpoint.

    :param administrators_group: Gets or sets the identity reference for the administrators group of the service endpoint.
    :type administrators_group: :class:`IdentityRef <service-endpoint.v4_1.models.IdentityRef>`
    :param authorization: Gets or sets the authorization data for talking to the endpoint.
    :type authorization: :class:`EndpointAuthorization <service-endpoint.v4_1.models.EndpointAuthorization>`
    :param created_by: Gets or sets the identity reference for the user who created the Service endpoint.
    :type created_by: :class:`IdentityRef <service-endpoint.v4_1.models.IdentityRef>`
    :param data:
    :type data: dict
    :param description: Gets or sets the description of endpoint.
    :type description: str
    :param group_scope_id:
    :type group_scope_id: str
    :param id: Gets or sets the identifier of this endpoint.
    :type id: str
    :param is_ready: EndPoint state indictor
    :type is_ready: bool
    :param name: Gets or sets the friendly name of the endpoint.
    :type name: str
    :param operation_status: Error message during creation/deletion of endpoint
    :type operation_status: :class:`object <service-endpoint.v4_1.models.object>`
    :param readers_group: Gets or sets the identity reference for the readers group of the service endpoint.
    :type readers_group: :class:`IdentityRef <service-endpoint.v4_1.models.IdentityRef>`
    :param type: Gets or sets the type of the endpoint.
    :type type: str
    :param url: Gets or sets the url of the endpoint.
    :type url: str
    """

    _attribute_map = {
        'administrators_group': {'key': 'administratorsGroup', 'type': 'IdentityRef'},
        'authorization': {'key': 'authorization', 'type': 'EndpointAuthorization'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'data': {'key': 'data', 'type': '{str}'},
        'description': {'key': 'description', 'type': 'str'},
        'group_scope_id': {'key': 'groupScopeId', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_ready': {'key': 'isReady', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'operation_status': {'key': 'operationStatus', 'type': 'object'},
        'readers_group': {'key': 'readersGroup', 'type': 'IdentityRef'},
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, administrators_group=None, authorization=None, created_by=None, data=None, description=None, group_scope_id=None, id=None, is_ready=None, name=None, operation_status=None, readers_group=None, type=None, url=None):
        super(ServiceEndpoint, self).__init__()
        self.administrators_group = administrators_group
        self.authorization = authorization
        self.created_by = created_by
        self.data = data
        self.description = description
        self.group_scope_id = group_scope_id
        self.id = id
        self.is_ready = is_ready
        self.name = name
        self.operation_status = operation_status
        self.readers_group = readers_group
        self.type = type
        self.url = url
