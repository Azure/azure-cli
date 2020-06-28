# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .web_api_connected_service_ref import WebApiConnectedServiceRef


class WebApiConnectedService(WebApiConnectedServiceRef):
    """WebApiConnectedService.

    :param url:
    :type url: str
    :param authenticated_by: The user who did the OAuth authentication to created this service
    :type authenticated_by: :class:`IdentityRef <core.v4_0.models.IdentityRef>`
    :param description: Extra description on the service.
    :type description: str
    :param friendly_name: Friendly Name of service connection
    :type friendly_name: str
    :param id: Id/Name of the connection service. For Ex: Subscription Id for Azure Connection
    :type id: str
    :param kind: The kind of service.
    :type kind: str
    :param project: The project associated with this service
    :type project: :class:`TeamProjectReference <core.v4_0.models.TeamProjectReference>`
    :param service_uri: Optional uri to connect directly to the service such as https://windows.azure.com
    :type service_uri: str
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        'authenticated_by': {'key': 'authenticatedBy', 'type': 'IdentityRef'},
        'description': {'key': 'description', 'type': 'str'},
        'friendly_name': {'key': 'friendlyName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'kind': {'key': 'kind', 'type': 'str'},
        'project': {'key': 'project', 'type': 'TeamProjectReference'},
        'service_uri': {'key': 'serviceUri', 'type': 'str'}
    }

    def __init__(self, url=None, authenticated_by=None, description=None, friendly_name=None, id=None, kind=None, project=None, service_uri=None):
        super(WebApiConnectedService, self).__init__(url=url)
        self.authenticated_by = authenticated_by
        self.description = description
        self.friendly_name = friendly_name
        self.id = id
        self.kind = kind
        self.project = project
        self.service_uri = service_uri
