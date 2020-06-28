# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Folder(Model):
    """Folder.

    :param created_by:
    :type created_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param created_on:
    :type created_on: datetime
    :param description:
    :type description: str
    :param last_changed_by:
    :type last_changed_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param last_changed_date:
    :type last_changed_date: datetime
    :param path:
    :type path: str
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'last_changed_by': {'key': 'lastChangedBy', 'type': 'IdentityRef'},
        'last_changed_date': {'key': 'lastChangedDate', 'type': 'iso-8601'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, created_by=None, created_on=None, description=None, last_changed_by=None, last_changed_date=None, path=None):
        super(Folder, self).__init__()
        self.created_by = created_by
        self.created_on = created_on
        self.description = description
        self.last_changed_by = last_changed_by
        self.last_changed_date = last_changed_date
        self.path = path
