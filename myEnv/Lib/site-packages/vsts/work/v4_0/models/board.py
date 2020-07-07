# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .board_reference import BoardReference


class Board(BoardReference):
    """Board.

    :param id: Id of the resource
    :type id: str
    :param name: Name of the resource
    :type name: str
    :param url: Full http link to the resource
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work.v4_0.models.ReferenceLinks>`
    :param allowed_mappings:
    :type allowed_mappings: dict
    :param can_edit:
    :type can_edit: bool
    :param columns:
    :type columns: list of :class:`BoardColumn <work.v4_0.models.BoardColumn>`
    :param fields:
    :type fields: :class:`BoardFields <work.v4_0.models.BoardFields>`
    :param is_valid:
    :type is_valid: bool
    :param revision:
    :type revision: int
    :param rows:
    :type rows: list of :class:`BoardRow <work.v4_0.models.BoardRow>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'allowed_mappings': {'key': 'allowedMappings', 'type': '{{[str]}}'},
        'can_edit': {'key': 'canEdit', 'type': 'bool'},
        'columns': {'key': 'columns', 'type': '[BoardColumn]'},
        'fields': {'key': 'fields', 'type': 'BoardFields'},
        'is_valid': {'key': 'isValid', 'type': 'bool'},
        'revision': {'key': 'revision', 'type': 'int'},
        'rows': {'key': 'rows', 'type': '[BoardRow]'}
    }

    def __init__(self, id=None, name=None, url=None, _links=None, allowed_mappings=None, can_edit=None, columns=None, fields=None, is_valid=None, revision=None, rows=None):
        super(Board, self).__init__(id=id, name=name, url=url)
        self._links = _links
        self.allowed_mappings = allowed_mappings
        self.can_edit = can_edit
        self.columns = columns
        self.fields = fields
        self.is_valid = is_valid
        self.revision = revision
        self.rows = rows
