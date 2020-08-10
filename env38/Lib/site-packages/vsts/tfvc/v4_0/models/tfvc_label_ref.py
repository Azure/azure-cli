# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcLabelRef(Model):
    """TfvcLabelRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <tfvc.v4_0.models.ReferenceLinks>`
    :param description:
    :type description: str
    :param id:
    :type id: int
    :param label_scope:
    :type label_scope: str
    :param modified_date:
    :type modified_date: datetime
    :param name:
    :type name: str
    :param owner:
    :type owner: :class:`IdentityRef <tfvc.v4_0.models.IdentityRef>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'label_scope': {'key': 'labelScope', 'type': 'str'},
        'modified_date': {'key': 'modifiedDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, description=None, id=None, label_scope=None, modified_date=None, name=None, owner=None, url=None):
        super(TfvcLabelRef, self).__init__()
        self._links = _links
        self.description = description
        self.id = id
        self.label_scope = label_scope
        self.modified_date = modified_date
        self.name = name
        self.owner = owner
        self.url = url
