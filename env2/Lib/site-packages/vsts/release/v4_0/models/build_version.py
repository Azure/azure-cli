# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BuildVersion(Model):
    """BuildVersion.

    :param id:
    :type id: str
    :param name:
    :type name: str
    :param source_branch:
    :type source_branch: str
    :param source_repository_id:
    :type source_repository_id: str
    :param source_repository_type:
    :type source_repository_type: str
    :param source_version:
    :type source_version: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'source_branch': {'key': 'sourceBranch', 'type': 'str'},
        'source_repository_id': {'key': 'sourceRepositoryId', 'type': 'str'},
        'source_repository_type': {'key': 'sourceRepositoryType', 'type': 'str'},
        'source_version': {'key': 'sourceVersion', 'type': 'str'}
    }

    def __init__(self, id=None, name=None, source_branch=None, source_repository_id=None, source_repository_type=None, source_version=None):
        super(BuildVersion, self).__init__()
        self.id = id
        self.name = name
        self.source_branch = source_branch
        self.source_repository_id = source_repository_id
        self.source_repository_type = source_repository_type
        self.source_version = source_version
