# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemClassificationNode(WorkItemTrackingResource):
    """WorkItemClassificationNode.

    :param url:
    :type url: str
    :param _links: Link references to related REST resources.
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_1.models.ReferenceLinks>`
    :param attributes: Dictionary that has node attributes like start/finish date for iteration nodes.
    :type attributes: dict
    :param children: List of child nodes fetched.
    :type children: list of :class:`WorkItemClassificationNode <work-item-tracking.v4_1.models.WorkItemClassificationNode>`
    :param has_children: Flag that indicates if the classification node has any child nodes.
    :type has_children: bool
    :param id: Integer ID of the classification node.
    :type id: int
    :param identifier: GUID ID of the classification node.
    :type identifier: str
    :param name: Name of the classification node.
    :type name: str
    :param structure_type: Node structure type.
    :type structure_type: object
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'attributes': {'key': 'attributes', 'type': '{object}'},
        'children': {'key': 'children', 'type': '[WorkItemClassificationNode]'},
        'has_children': {'key': 'hasChildren', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'int'},
        'identifier': {'key': 'identifier', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'structure_type': {'key': 'structureType', 'type': 'object'}
    }

    def __init__(self, url=None, _links=None, attributes=None, children=None, has_children=None, id=None, identifier=None, name=None, structure_type=None):
        super(WorkItemClassificationNode, self).__init__(url=url, _links=_links)
        self.attributes = attributes
        self.children = children
        self.has_children = has_children
        self.id = id
        self.identifier = identifier
        self.name = name
        self.structure_type = structure_type
