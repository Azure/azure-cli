# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Extension(Model):
    """Extension.

    :param assignment_source: Assignment source for this extension. I.e. explicitly assigned or from a group rule.
    :type assignment_source: object
    :param id: Gallery Id of the Extension.
    :type id: str
    :param name: Friendly name of this extension.
    :type name: str
    :param source: Source of this extension assignment. Ex: msdn, account, none, etc.
    :type source: object
    """

    _attribute_map = {
        'assignment_source': {'key': 'assignmentSource', 'type': 'object'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'source': {'key': 'source', 'type': 'object'}
    }

    def __init__(self, assignment_source=None, id=None, name=None, source=None):
        super(Extension, self).__init__()
        self.assignment_source = assignment_source
        self.id = id
        self.name = name
        self.source = source
