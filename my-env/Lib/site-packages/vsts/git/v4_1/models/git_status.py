# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitStatus(Model):
    """GitStatus.

    :param _links: Reference links.
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param context: Context of the status.
    :type context: :class:`GitStatusContext <git.v4_1.models.GitStatusContext>`
    :param created_by: Identity that created the status.
    :type created_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param creation_date: Creation date and time of the status.
    :type creation_date: datetime
    :param description: Status description. Typically describes current state of the status.
    :type description: str
    :param id: Status identifier.
    :type id: int
    :param state: State of the status.
    :type state: object
    :param target_url: URL with status details.
    :type target_url: str
    :param updated_date: Last update date and time of the status.
    :type updated_date: datetime
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'context': {'key': 'context', 'type': 'GitStatusContext'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'creation_date': {'key': 'creationDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'state': {'key': 'state', 'type': 'object'},
        'target_url': {'key': 'targetUrl', 'type': 'str'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'}
    }

    def __init__(self, _links=None, context=None, created_by=None, creation_date=None, description=None, id=None, state=None, target_url=None, updated_date=None):
        super(GitStatus, self).__init__()
        self._links = _links
        self.context = context
        self.created_by = created_by
        self.creation_date = creation_date
        self.description = description
        self.id = id
        self.state = state
        self.target_url = target_url
        self.updated_date = updated_date
