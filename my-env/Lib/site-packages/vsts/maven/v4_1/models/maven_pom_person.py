# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomPerson(Model):
    """MavenPomPerson.

    :param email:
    :type email: str
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param organization:
    :type organization: str
    :param organization_url:
    :type organization_url: str
    :param roles:
    :type roles: list of str
    :param timezone:
    :type timezone: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'email': {'key': 'email', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'organization': {'key': 'organization', 'type': 'str'},
        'organization_url': {'key': 'organizationUrl', 'type': 'str'},
        'roles': {'key': 'roles', 'type': '[str]'},
        'timezone': {'key': 'timezone', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, email=None, id=None, name=None, organization=None, organization_url=None, roles=None, timezone=None, url=None):
        super(MavenPomPerson, self).__init__()
        self.email = email
        self.id = id
        self.name = name
        self.organization = organization
        self.organization_url = organization_url
        self.roles = roles
        self.timezone = timezone
        self.url = url
