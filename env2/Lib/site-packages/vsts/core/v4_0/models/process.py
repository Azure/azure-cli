# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .process_reference import ProcessReference


class Process(ProcessReference):
    """Process.

    :param name:
    :type name: str
    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <core.v4_0.models.ReferenceLinks>`
    :param description:
    :type description: str
    :param id:
    :type id: str
    :param is_default:
    :type is_default: bool
    :param type:
    :type type: object
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_default': {'key': 'isDefault', 'type': 'bool'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, name=None, url=None, _links=None, description=None, id=None, is_default=None, type=None):
        super(Process, self).__init__(name=name, url=url)
        self._links = _links
        self.description = description
        self.id = id
        self.is_default = is_default
        self.type = type
