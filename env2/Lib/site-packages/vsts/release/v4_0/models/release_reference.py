# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseReference(Model):
    """ReleaseReference.

    :param _links: Gets links to access the release.
    :type _links: :class:`ReferenceLinks <release.v4_0.models.ReferenceLinks>`
    :param artifacts: Gets list of artifacts.
    :type artifacts: list of :class:`Artifact <release.v4_0.models.Artifact>`
    :param created_by: Gets the identity who created.
    :type created_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param created_on: Gets date on which it got created.
    :type created_on: datetime
    :param description: Gets description.
    :type description: str
    :param id: Gets the unique identifier of this field.
    :type id: int
    :param modified_by: Gets the identity who modified.
    :type modified_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param name: Gets name of release.
    :type name: str
    :param reason: Gets reason for release.
    :type reason: object
    :param release_definition: Gets release definition shallow reference.
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_0.models.ReleaseDefinitionShallowReference>`
    :param url:
    :type url: str
    :param web_access_uri:
    :type web_access_uri: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'artifacts': {'key': 'artifacts', 'type': '[Artifact]'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'name': {'key': 'name', 'type': 'str'},
        'reason': {'key': 'reason', 'type': 'object'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'url': {'key': 'url', 'type': 'str'},
        'web_access_uri': {'key': 'webAccessUri', 'type': 'str'}
    }

    def __init__(self, _links=None, artifacts=None, created_by=None, created_on=None, description=None, id=None, modified_by=None, name=None, reason=None, release_definition=None, url=None, web_access_uri=None):
        super(ReleaseReference, self).__init__()
        self._links = _links
        self.artifacts = artifacts
        self.created_by = created_by
        self.created_on = created_on
        self.description = description
        self.id = id
        self.modified_by = modified_by
        self.name = name
        self.reason = reason
        self.release_definition = release_definition
        self.url = url
        self.web_access_uri = web_access_uri
