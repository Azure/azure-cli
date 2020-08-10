# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRepository(Model):
    """GitRepository.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param default_branch:
    :type default_branch: str
    :param id:
    :type id: str
    :param is_fork: True if the repository was created as a fork
    :type is_fork: bool
    :param name:
    :type name: str
    :param parent_repository:
    :type parent_repository: :class:`GitRepositoryRef <git.v4_1.models.GitRepositoryRef>`
    :param project:
    :type project: :class:`TeamProjectReference <git.v4_1.models.TeamProjectReference>`
    :param remote_url:
    :type remote_url: str
    :param ssh_url:
    :type ssh_url: str
    :param url:
    :type url: str
    :param valid_remote_urls:
    :type valid_remote_urls: list of str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'default_branch': {'key': 'defaultBranch', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_fork': {'key': 'isFork', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'parent_repository': {'key': 'parentRepository', 'type': 'GitRepositoryRef'},
        'project': {'key': 'project', 'type': 'TeamProjectReference'},
        'remote_url': {'key': 'remoteUrl', 'type': 'str'},
        'ssh_url': {'key': 'sshUrl', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'valid_remote_urls': {'key': 'validRemoteUrls', 'type': '[str]'}
    }

    def __init__(self, _links=None, default_branch=None, id=None, is_fork=None, name=None, parent_repository=None, project=None, remote_url=None, ssh_url=None, url=None, valid_remote_urls=None):
        super(GitRepository, self).__init__()
        self._links = _links
        self.default_branch = default_branch
        self.id = id
        self.is_fork = is_fork
        self.name = name
        self.parent_repository = parent_repository
        self.project = project
        self.remote_url = remote_url
        self.ssh_url = ssh_url
        self.url = url
        self.valid_remote_urls = valid_remote_urls
