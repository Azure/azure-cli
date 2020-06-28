# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRepositoryCreateOptions(Model):
    """GitRepositoryCreateOptions.

    :param name:
    :type name: str
    :param parent_repository:
    :type parent_repository: :class:`GitRepositoryRef <git.v4_1.models.GitRepositoryRef>`
    :param project:
    :type project: :class:`TeamProjectReference <git.v4_1.models.TeamProjectReference>`
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'parent_repository': {'key': 'parentRepository', 'type': 'GitRepositoryRef'},
        'project': {'key': 'project', 'type': 'TeamProjectReference'}
    }

    def __init__(self, name=None, parent_repository=None, project=None):
        super(GitRepositoryCreateOptions, self).__init__()
        self.name = name
        self.parent_repository = parent_repository
        self.project = project
