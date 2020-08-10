# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BuildConfiguration(Model):
    """BuildConfiguration.

    :param branch_name:
    :type branch_name: str
    :param build_definition_id:
    :type build_definition_id: int
    :param flavor:
    :type flavor: str
    :param id:
    :type id: int
    :param number:
    :type number: str
    :param platform:
    :type platform: str
    :param project:
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param repository_id:
    :type repository_id: int
    :param source_version:
    :type source_version: str
    :param uri:
    :type uri: str
    """

    _attribute_map = {
        'branch_name': {'key': 'branchName', 'type': 'str'},
        'build_definition_id': {'key': 'buildDefinitionId', 'type': 'int'},
        'flavor': {'key': 'flavor', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'number': {'key': 'number', 'type': 'str'},
        'platform': {'key': 'platform', 'type': 'str'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'repository_id': {'key': 'repositoryId', 'type': 'int'},
        'source_version': {'key': 'sourceVersion', 'type': 'str'},
        'uri': {'key': 'uri', 'type': 'str'}
    }

    def __init__(self, branch_name=None, build_definition_id=None, flavor=None, id=None, number=None, platform=None, project=None, repository_id=None, source_version=None, uri=None):
        super(BuildConfiguration, self).__init__()
        self.branch_name = branch_name
        self.build_definition_id = build_definition_id
        self.flavor = flavor
        self.id = id
        self.number = number
        self.platform = platform
        self.project = project
        self.repository_id = repository_id
        self.source_version = source_version
        self.uri = uri
