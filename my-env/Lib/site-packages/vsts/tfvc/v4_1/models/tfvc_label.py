# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .tfvc_label_ref import TfvcLabelRef


class TfvcLabel(TfvcLabelRef):
    """TfvcLabel.

    :param _links:
    :type _links: :class:`ReferenceLinks <tfvc.v4_1.models.ReferenceLinks>`
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
    :type owner: :class:`IdentityRef <tfvc.v4_1.models.IdentityRef>`
    :param url:
    :type url: str
    :param items:
    :type items: list of :class:`TfvcItem <tfvc.v4_1.models.TfvcItem>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'label_scope': {'key': 'labelScope', 'type': 'str'},
        'modified_date': {'key': 'modifiedDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'},
        'items': {'key': 'items', 'type': '[TfvcItem]'}
    }

    def __init__(self, _links=None, description=None, id=None, label_scope=None, modified_date=None, name=None, owner=None, url=None, items=None):
        super(TfvcLabel, self).__init__(_links=_links, description=description, id=id, label_scope=label_scope, modified_date=modified_date, name=name, owner=owner, url=url)
        self.items = items
