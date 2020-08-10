# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .wiki_create_base_parameters import WikiCreateBaseParameters


class WikiV2(WikiCreateBaseParameters):
    """WikiV2.

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
    :param id: ID of the wiki.
    :type id: str
    :param properties: Properties of the wiki.
    :type properties: dict
    :param remote_url: Remote web url to the wiki.
    :type remote_url: str
    :param url: REST url for this wiki.
    :type url: str
    :param versions: Versions of the wiki.
    :type versions: list of :class:`GitVersionDescriptor <wiki.v4_1.models.GitVersionDescriptor>`
    """

    _attribute_map = {
        'mapped_path': {'key': 'mappedPath', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'},
        'id': {'key': 'id', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{str}'},
        'remote_url': {'key': 'remoteUrl', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'versions': {'key': 'versions', 'type': '[GitVersionDescriptor]'}
    }

    def __init__(self, mapped_path=None, name=None, project_id=None, repository_id=None, type=None, id=None, properties=None, remote_url=None, url=None, versions=None):
        super(WikiV2, self).__init__(mapped_path=mapped_path, name=name, project_id=project_id, repository_id=repository_id, type=type)
        self.id = id
        self.properties = properties
        self.remote_url = remote_url
        self.url = url
        self.versions = versions
