# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiCreateBaseParameters(Model):
    """WikiCreateBaseParameters.

    :param mapped_path: Folder path inside repository which is shown as Wiki. Not required for ProjectWiki type.
    :type mapped_path: str
    :param name: Wiki name.
    :type name: str
    :param project_id: ID of the project in which the wiki is to be created.
    :type project_id: str
    :param repository_id: ID of the git repository that backs up the wiki. Not required for ProjectWiki type.
    :type repository_id: str
    :param type: Type of the wiki.
    :type type: object
    """

    _attribute_map = {
        'mapped_path': {'key': 'mappedPath', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, mapped_path=None, name=None, project_id=None, repository_id=None, type=None):
        super(WikiCreateBaseParameters, self).__init__()
        self.mapped_path = mapped_path
        self.name = name
        self.project_id = project_id
        self.repository_id = repository_id
        self.type = type
