# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OAuthConfiguration(Model):
    """OAuthConfiguration.

    :param client_id: Gets or sets the ClientId
    :type client_id: str
    :param client_secret: Gets or sets the ClientSecret
    :type client_secret: str
    :param created_by: Gets or sets the identity who created the config.
    :type created_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param created_on: Gets or sets the time when config was created.
    :type created_on: datetime
    :param endpoint_type: Gets or sets the type of the endpoint.
    :type endpoint_type: str
    :param id: Gets or sets the unique identifier of this field
    :type id: int
    :param modified_by: Gets or sets the identity who modified the config.
    :type modified_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param modified_on: Gets or sets the time when variable group was modified
    :type modified_on: datetime
    :param name: Gets or sets the name
    :type name: str
    :param url: Gets or sets the Url
    :type url: str
    """

    _attribute_map = {
        'client_id': {'key': 'clientId', 'type': 'str'},
        'client_secret': {'key': 'clientSecret', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'endpoint_type': {'key': 'endpointType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, client_id=None, client_secret=None, created_by=None, created_on=None, endpoint_type=None, id=None, modified_by=None, modified_on=None, name=None, url=None):
        super(OAuthConfiguration, self).__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.created_by = created_by
        self.created_on = created_on
        self.endpoint_type = endpoint_type
        self.id = id
        self.modified_by = modified_by
        self.modified_on = modified_on
        self.name = name
        self.url = url
