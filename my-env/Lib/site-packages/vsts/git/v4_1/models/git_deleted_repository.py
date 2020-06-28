# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitDeletedRepository(Model):
    """GitDeletedRepository.

    :param created_date:
    :type created_date: datetime
    :param deleted_by:
    :type deleted_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param deleted_date:
    :type deleted_date: datetime
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param project:
    :type project: :class:`TeamProjectReference <git.v4_1.models.TeamProjectReference>`
    """

    _attribute_map = {
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'deleted_by': {'key': 'deletedBy', 'type': 'IdentityRef'},
        'deleted_date': {'key': 'deletedDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'project': {'key': 'project', 'type': 'TeamProjectReference'}
    }

    def __init__(self, created_date=None, deleted_by=None, deleted_date=None, id=None, name=None, project=None):
        super(GitDeletedRepository, self).__init__()
        self.created_date = created_date
        self.deleted_by = deleted_by
        self.deleted_date = deleted_date
        self.id = id
        self.name = name
        self.project = project
