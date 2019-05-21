# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_functions_devops_build.organization.organization_manager import OrganizationManager
from azure_functions_devops_build.project.project_manager import ProjectManager
from azure_functions_devops_build.yaml.yaml_manager import YamlManager
from azure_functions_devops_build.repository.repository_manager import RepositoryManager
from azure_functions_devops_build.pool.pool_manager import PoolManager
from azure_functions_devops_build.service_endpoint.service_endpoint_manager import ServiceEndpointManager
from azure_functions_devops_build.extension.extension_manager import ExtensionManager
from azure_functions_devops_build.builder.builder_manager import BuilderManager
from azure_functions_devops_build.artifact.artifact_manager import ArtifactManager
from azure_functions_devops_build.release.release_manager import ReleaseManager

from azure_functions_devops_build.yaml.github_yaml_manager import GithubYamlManager
from azure_functions_devops_build.repository.github_repository_manager import GithubRepositoryManager
from azure_functions_devops_build.user.github_user_manager import GithubUserManager
from azure_functions_devops_build.service_endpoint.github_service_endpoint_manager import GithubServiceEndpointManager

from azure.cli.core._profile import Profile


class AzureDevopsBuildProvider(object):  # pylint: disable=too-many-public-methods
    """Implement a wrapper surrounding the different azure_functions_devops_build commands

    Attributes:
        cred : the credentials needed to access the classes
    """
    def __init__(self, cli_ctx):
        profile = Profile(cli_ctx=cli_ctx)
        self._creds, _, _ = profile.get_login_credentials(subscription_id=None)

    def list_organizations(self):
        """List DevOps organizations"""
        organization_manager = OrganizationManager(creds=self._creds)
        organizations = organization_manager.list_organizations()
        return organizations

    def list_regions(self):
        """List DevOps regions"""
        organization_manager = OrganizationManager(creds=self._creds)
        regions = organization_manager.list_regions()
        return regions

    def create_organization(self, organization_name, regionCode):
        """Create DevOps organization"""
        # validate the organization name
        organization_manager = OrganizationManager(creds=self._creds)
        validation = organization_manager.validate_organization_name(organization_name)
        if not validation.valid:
            return validation

        # validate region code:
        valid_region = False
        for region in self.list_regions().value:
            if region.name == regionCode:
                valid_region = True
        if not valid_region:
            validation.message = "not a valid region code - run 'az functionapp devops-build organization' regions to find a valid regionCode"  # pylint: disable=line-too-long
            validation.valid = False
            return validation

        new_organization = organization_manager.create_organization(regionCode, organization_name)
        new_organization.valid = True
        return new_organization

    def list_projects(self, organization_name):
        """List DevOps projects"""
        project_manager = ProjectManager(organization_name=organization_name, creds=self._creds)
        projects = project_manager.list_projects()
        return projects

    def create_project(self, organization_name, project_name):
        """Create DevOps project"""
        project_manager = ProjectManager(organization_name=organization_name, creds=self._creds)
        project = project_manager.create_project(project_name)
        return project

    def create_yaml(self, language, appType):  # pylint: disable=no-self-use
        """Create azure pipelines yaml"""
        yaml_manager = YamlManager(language, appType)
        yaml_manager.create_yaml()

    def create_repository(self, organization_name, project_name, repository_name):
        """Create devops repository"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.create_repository(repository_name)

    def list_repositories(self, organization_name, project_name):
        """List devops repository"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.list_repositories()

    def list_commits(self, organization_name, project_name, repository_name):
        """List devops commits"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.list_commits(repository_name)

    @staticmethod
    def check_git():
        """Check if git command does exist"""
        return RepositoryManager.check_git()

    @staticmethod
    def check_git_local_repository():
        """Check if local git repository does exist"""
        return RepositoryManager.check_git_local_repository()

    @staticmethod
    def check_git_credential_manager():
        return RepositoryManager.check_git_credential_manager()

    def check_git_remote(self, organization_name, project_name, repository_name):
        """Check if local git remote name does exist"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.check_git_remote(repository_name, remote_prefix="azuredevops")

    def remove_git_remote(self, organization_name, project_name, repository_name):
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.remove_git_remote(repository_name, remote_prefix="azuredevops")

    def get_local_git_remote_name(self, organization_name, project_name, repository_name):
        """Get the local git remote name for current repository"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.get_local_git_remote_name(repository_name, remote_prefix="azuredevops")

    def get_azure_devops_repository(self, organization_name, project_name, repository_name):
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.get_azure_devops_repository(repository_name)

    def get_azure_devops_repo_url(self, organization_name, project_name, repository_name):
        """Get the azure devops repository url"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.get_azure_devops_repo_url(repository_name)

    def setup_local_git_repository(self, organization_name, project_name, repository_name):
        """Setup a repository locally and push to devops"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.setup_local_git_repository(repository_name, remote_prefix="azuredevops")

    def get_azure_devops_repository_branches(self, organization_name, project_name, repository_name):
        """Get Azure Devops repository branches"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.get_azure_devops_repository_branches(repository_name)

    def push_local_to_azure_devops_repository(self, organization_name, project_name, repository_name, force=False):
        """Push local context to Azure Devops repository"""
        repository_manager = RepositoryManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return repository_manager.push_local_to_azure_devops_repository(
            repository_name,
            remote_prefix="azuredevops",
            force=force
        )

    def list_pools(self, organization_name, project_name):
        """List the devops pool resources"""
        pool_manager = PoolManager(organization_name=organization_name, project_name=project_name, creds=self._creds)
        return pool_manager.list_pools()

    def get_service_endpoints(self, organization_name, project_name, repository_name):
        """Query a service endpoint detail"""
        service_endpoint_manager = ServiceEndpointManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return service_endpoint_manager.get_service_endpoints(repository_name)

    def create_service_endpoint(self, organization_name, project_name, repository_name):
        """Create a service endpoint to allow authentication via ARM service principal"""
        service_endpoint_manager = ServiceEndpointManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return service_endpoint_manager.create_service_endpoint(repository_name)

    def list_service_endpoints(self, organization_name, project_name):
        """List the different service endpoints in a project"""
        service_endpoint_manager = ServiceEndpointManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return service_endpoint_manager.list_service_endpoints()

    def create_extension(self, organization_name, extension_name, publisher_name):
        """Install an azure devops extension"""
        extension_manager = ExtensionManager(organization_name=organization_name, creds=self._creds)
        return extension_manager.create_extension(extension_name, publisher_name)

    def list_extensions(self, organization_name):
        """List the azure devops extensions in an organization"""
        extension_manager = ExtensionManager(organization_name=organization_name, creds=self._creds)
        return extension_manager.list_extensions()

    def create_devops_build_definition(self, organization_name, project_name, repository_name,
                                       build_definition_name, pool_name):
        """Create a definition for an azure devops build"""
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            repository_name=repository_name,
            creds=self._creds
        )
        return builder_manager.create_devops_build_definition(
            build_definition_name=build_definition_name,
            pool_name=pool_name
        )

    def list_build_definitions(self, organization_name, project_name):
        """List the azure devops build definitions within a project"""
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return builder_manager.list_definitions()

    def create_build_object(self, organization_name, project_name, build_definition_name, pool_name):
        """Create an azure devops build based off a previous definition"""
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return builder_manager.create_build(build_definition_name, pool_name)

    def list_build_objects(self, organization_name, project_name):
        """List already running and builds that have already run in an azure devops project"""
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return builder_manager.list_builds()

    def get_build_logs_status(self, organization_name, project_name, build_id):
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return builder_manager.get_build_logs_status(build_id)

    def get_build_logs_content_from_statuses(self, organization_name, project_name, build_id, prev_log, curr_log):
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return builder_manager.get_build_logs_content_from_statuses(build_id, prev_log, curr_log)

    def list_artifacts(self, organization_name, project_name, build_id):
        """List the azure devops artifacts from a build"""
        artifact_manager = ArtifactManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return artifact_manager.list_artifacts(build_id)

    def create_release_definition(self, organization_name, project_name, build_name, artifact_name,
                                  pool_name, service_endpoint_name, release_definition_name, app_type,
                                  functionapp_name, storage_name, resource_name, settings):
        """Create a release definition for azure devops that is for azure functions"""
        release_manager = ReleaseManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return release_manager.create_release_definition(build_name, artifact_name, pool_name,
                                                         service_endpoint_name, release_definition_name,
                                                         app_type, functionapp_name, storage_name,
                                                         resource_name, settings=settings)

    def list_release_definitions(self, organization_name, project_name):
        """List the release definitions for azure devops"""
        release_manager = ReleaseManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return release_manager.list_release_definitions()

    def create_release(self, organization_name, project_name, release_definition_name):
        """Create a release based off a previously defined release definition"""
        release_manager = ReleaseManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return release_manager.create_release(release_definition_name)

    def get_latest_release(self, organization_name, project_name, release_defintion_name):
        release_manager = ReleaseManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return release_manager.get_latest_release(release_defintion_name)

    def get_github_service_endpoints(self, organization_name, project_name, github_repository):
        service_endpoint_manager = GithubServiceEndpointManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return service_endpoint_manager.get_github_service_endpoints(github_repository)

    def create_github_service_endpoint(self, organization_name, project_name, github_repository, github_pat):
        service_endpoint_manager = GithubServiceEndpointManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return service_endpoint_manager.create_github_service_endpoint(
            github_repository,
            github_pat
        )

    def create_github_build_definition(
            self,
            organization_name,
            project_name,
            github_repository,
            build_definition_name,
            pool_name
    ):
        builder_manager = BuilderManager(
            organization_name=organization_name,
            project_name=project_name,
            creds=self._creds
        )
        return builder_manager.create_github_build_definition(build_definition_name, pool_name, github_repository)

    @staticmethod
    def check_github_pat(github_pat):
        github_user_manager = GithubUserManager()
        return github_user_manager.check_github_pat(github_pat)

    @staticmethod
    def check_github_repository(pat, repository_fullname):
        github_repository_manager = GithubRepositoryManager(pat=pat)
        return github_repository_manager.check_github_repository(repository_fullname)

    @staticmethod
    def check_github_file(pat, repository_fullname, filepath):
        github_repository_manager = GithubRepositoryManager(pat=pat)
        return github_repository_manager.check_github_file(repository_fullname, filepath)

    @staticmethod
    def get_github_content(pat, repository_fullname, filepath):
        github_repository_manager = GithubRepositoryManager(pat=pat)
        return github_repository_manager.get_content(repository_fullname, filepath, get_metadata=False)

    @staticmethod
    def create_github_yaml(pat, language, app_type, repository_fullname, overwrite=False):
        github_repository_manager = GithubYamlManager(
            language=language,
            app_type=app_type,
            github_pat=pat,
            github_repository=repository_fullname
        )
        return github_repository_manager.create_yaml(overwrite)
