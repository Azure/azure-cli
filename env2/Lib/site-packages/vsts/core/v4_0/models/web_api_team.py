# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .web_api_team_ref import WebApiTeamRef


class WebApiTeam(WebApiTeamRef):
    """WebApiTeam.

    :param id: Team (Identity) Guid. A Team Foundation ID.
    :type id: str
    :param name: Team name
    :type name: str
    :param url: Team REST API Url
    :type url: str
    :param description: Team description
    :type description: str
    :param identity_url: Identity REST API Url to this team
    :type identity_url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'identity_url': {'key': 'identityUrl', 'type': 'str'}
    }

    def __init__(self, id=None, name=None, url=None, description=None, identity_url=None):
        super(WebApiTeam, self).__init__(id=id, name=name, url=url)
        self.description = description
        self.identity_url = identity_url
