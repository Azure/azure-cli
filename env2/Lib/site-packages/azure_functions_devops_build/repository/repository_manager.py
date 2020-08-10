# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from msrest.service_client import ServiceClient
from msrest import Configuration, Deserializer
import vsts.git.v4_1.models.git_repository_create_options as git_repository_create_options
from vsts.exceptions import VstsServiceError

from ..base.base_manager import BaseManager
from . import models
from .local_git_utils import (
        git_init,
        git_add_remote,
        git_remove_remote,
        git_stage_all,
        git_commit,
        git_push,
        does_git_exist,
        does_local_git_repository_exist,
        does_git_has_credential_manager,
        does_git_remote_exist,
        construct_git_remote_name,
        construct_git_remote_url
)

class RepositoryManager(BaseManager):
    """ Manage DevOps repositories

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", project_name="", creds=None):
        base_url = 'https://dev.azure.com'
        self._config = Configuration(base_url=base_url)
        self._client = ServiceClient(creds, self._config)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)
        super(RepositoryManager, self).__init__(creds, organization_name=organization_name, project_name=project_name)

    @staticmethod
    def check_git():
        return does_git_exist()

    @staticmethod
    def check_git_local_repository():
        return does_local_git_repository_exist()

    @staticmethod
    def check_git_credential_manager():
        return does_git_has_credential_manager()

    # Check if the git repository exists first. If it does, check if the git remote exists.
    def check_git_remote(self, repository_name, remote_prefix):
        if not does_local_git_repository_exist():
            return False

        remote_name = construct_git_remote_name(
            self._organization_name, self._project_name, repository_name, remote_prefix
        )
        return does_git_remote_exist(remote_name)

    def remove_git_remote(self, repository_name, remote_prefix):
        remote_name = construct_git_remote_name(
            self._organization_name, self._project_name, repository_name, remote_prefix
        )
        git_remove_remote(remote_name)

    def get_azure_devops_repository_branches(self, repository_name):
        try:
            result = self._git_client.get_branches(repository_name, self._project_name)
        except VstsServiceError:
            return []
        return result

    def get_azure_devops_repository(self, repository_name):
        try:
            result = self._git_client.get_repository(repository_name, self._project_name)
        except VstsServiceError:
            return None
        return result

    def create_repository(self, repository_name):
        project = self._get_project_by_name(self._project_name)
        git_repo_options = git_repository_create_options.GitRepositoryCreateOptions(
            name=repository_name,
            project=project
        )
        return self._git_client.create_repository(git_repo_options)

    def list_repositories(self):
        return self._git_client.get_repositories(self._project_name)

    def list_commits(self, repository_name):
        project = self._get_project_by_name(self._project_name)
        repository = self._get_repository_by_name(project, repository_name)
        return self._git_client.get_commits(repository.id, None, project=project.id)

    def get_local_git_remote_name(self, repository_name, remote_prefix):
        return construct_git_remote_name(self._organization_name, self._project_name, repository_name, remote_prefix)

    # Since the portal url and remote url are same. We only need one function to handle portal access and git push
    def get_azure_devops_repo_url(self, repository_name):
        return construct_git_remote_url(self._organization_name, self._project_name, repository_name)

    # The function will initialize a git repo, create git remote, stage all changes and commit the code
    # Exceptions: GitOperationException
    def setup_local_git_repository(self, repository_name, remote_prefix):
        remote_name = construct_git_remote_name(
            self._organization_name, self._project_name, repository_name, remote_prefix
        )
        remote_url = construct_git_remote_url(self._organization_name, self._project_name, repository_name)

        if not does_local_git_repository_exist():
            git_init()

        git_add_remote(remote_name, remote_url)
        git_stage_all()
        git_commit("Create function app with azure devops build. Remote repository url: {url}".format(url=remote_url))

    # The function will push the current context in local git repository to Azure Devops
    # Exceptions: GitOperationException
    def push_local_to_azure_devops_repository(self, repository_name, remote_prefix, force):
        remote_name = construct_git_remote_name(
            self._organization_name, self._project_name, repository_name, remote_prefix
        )
        git_push(remote_name, force)
