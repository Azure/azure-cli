# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BuildReference(Model):
    """BuildReference.

    :param branch_name:
    :type branch_name: str
    :param build_system:
    :type build_system: str
    :param definition_id:
    :type definition_id: int
    :param id:
    :type id: int
    :param number:
    :type number: str
    :param repository_id:
    :type repository_id: str
    :param uri:
    :type uri: str
    """

    _attribute_map = {
        'branch_name': {'key': 'branchName', 'type': 'str'},
        'build_system': {'key': 'buildSystem', 'type': 'str'},
        'definition_id': {'key': 'definitionId', 'type': 'int'},
        'id': {'key': 'id', 'type': 'int'},
        'number': {'key': 'number', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'},
        'uri': {'key': 'uri', 'type': 'str'}
    }

    def __init__(self, branch_name=None, build_system=None, definition_id=None, id=None, number=None, repository_id=None, uri=None):
        super(BuildReference, self).__init__()
        self.branch_name = branch_name
        self.build_system = build_system
        self.definition_id = definition_id
        self.id = id
        self.number = number
        self.repository_id = repository_id
        self.uri = uri
