# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from vsts.vss_connection import VssConnection

class BaseManager(object):
    """The basic manager which the other classes are build on

    Attributes:
        organization_name : The name of the DevOps organization
        project_name : The name of the DevOps project
        creds : These are credentials for an Azure user
    """

    def __init__(self, creds, organization_name="", project_name="", repository_name="", pool_name=""):
        # Create the relevant name attributes
        self._organization_name = organization_name
        self._project_name = project_name
        self._creds = creds
        self._repository_name = repository_name
        self._pool_name = pool_name

        # Create the relevant clients that are needed by the managers
        self._connection = VssConnection(base_url='https://dev.azure.com/' + organization_name, creds=creds)
        self._agent_client = self._connection.get_client("vsts.task_agent.v4_1.task_agent_client.TaskAgentClient")
        self._build_client = self._connection.get_client('vsts.build.v4_1.build_client.BuildClient')
        self._core_client = self._connection.get_client('vsts.core.v4_0.core_client.CoreClient')
        self._extension_management_client = self._connection.get_client('vsts.extension_management.v4_1.extension_management_client.ExtensionManagementClient') # pylint: disable=line-too-long
        self._git_client = self._connection.get_client("vsts.git.v4_1.git_client.GitClient")
        self._release_client = self._connection.get_client('vsts.release.v4_1.release_client.ReleaseClient')
        self._service_endpoint_client = self._connection.get_client(
            'vsts.service_endpoint.v4_1.service_endpoint_client.ServiceEndpointClient'
        )

    def _get_project_by_name(self, project_name):
        """Helper function to get the project object from its name"""
        projects = self._core_client.get_projects()
        return next((project for project in projects if project.name == project_name), None)

    def _get_repository_by_name(self, project, repository_name):
        """Helper function to get the repository object from its name"""
        repositories = self._git_client.get_repositories(project.id)
        return next((repository for repository in repositories if repository.name == repository_name), None)

    def _get_definition_by_name(self, project, definition_name):
        """Helper function to get definition object from its name"""
        definitions = self._build_client.get_definitions(project.id)
        return next((definition for definition in definitions if definition.name == definition_name), None)

    def _get_build_by_name(self, project, name):
        """Helper function to get build object from its name"""
        builds_unsorted = self._build_client.get_builds(project=project.id)
        builds = sorted(builds_unsorted, key=lambda x: x.start_time, reverse=True)
        return next((build for build in builds if build.definition.name == name), None)

    def _get_github_repository_by_name(self, github_repository_name):
        """Helper function to get a github repository object from its name"""
        service_endpoints = self._service_endpoint_client.get_service_endpoints(self._project_name, type="github")
        github_endpoint = service_endpoints[0]
        repositories = self._build_client.list_repositories(
            project=self._project_name,
            provider_name='github',
            service_endpoint_id=github_endpoint.id,
            repository=github_repository_name
        )
        repository_match = next((
            repository for repository in repositories.repositories if repository.full_name == github_repository_name
        ), None)
        return repository_match
