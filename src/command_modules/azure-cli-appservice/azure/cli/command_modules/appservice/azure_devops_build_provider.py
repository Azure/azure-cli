# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_functions_devops_build.organization.organization_manager import OrganizationManager
from azure_functions_devops_build.project.project_manager import ProjectManager
from azure_functions_devops_build.yaml.yaml_manager import YamlManager
from azure_functions_devops_build.respository.repository_manager import RepositoryManager
from azure_functions_devops_build.pool.pool_manager import PoolManager
from azure_functions_devops_build.service_endpoint.service_endpoint_manager import ServiceEndpointManager
from azure_functions_devops_build.extension.extension_manager import ExtensionManager
from azure_functions_devops_build.builder.builder_manager import BuilderManager
from azure_functions_devops_build.artifact.artifact_manager import ArtifactManager
from azure_functions_devops_build.release.release_manager import ReleaseManager

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
        repository_manager = RepositoryManager(organization_name=organization_name,
                                               project_name=project_name, creds=self._creds)
        return repository_manager.create_repository(repository_name)

    def list_repositories(self, organization_name, project_name):
        """List devops repository"""
        repository_manager = RepositoryManager(organization_name=organization_name,
                                               project_name=project_name, creds=self._creds)
        return repository_manager.list_repositories()

    def list_commits(self, organization_name, project_name, repository_name):
        """List devops commits"""
        repository_manager = RepositoryManager(organization_name=organization_name,
                                               project_name=project_name, creds=self._creds)
        return repository_manager.list_commits(repository_name)

    def setup_repository(self, organization_name, project_name, repository_name):
        """Setup a repository locally and push to devops"""
        repository_manager = RepositoryManager(organization_name=organization_name,
                                               project_name=project_name, creds=self._creds)
        return repository_manager.setup_repository(repository_name)

    def setup_remote(self, organization_name, project_name, repository_name, remote_name):
        """Setup a remote locally and push to devops"""
        repository_manager = RepositoryManager(organization_name=organization_name,
                                               project_name=project_name, creds=self._creds)
        return repository_manager.setup_remote(repository_name, remote_name)

    def list_pools(self, organization_name, project_name):
        """List the devops pool resources"""
        pool_manager = PoolManager(organization_name=organization_name, project_name=project_name, creds=self._creds)
        return pool_manager.list_pools()

    def create_service_endpoint(self, organization_name, project_name, name):
        """Create a service endpoint to allow authentication via ARM service principal"""
        service_endpoint_manager = ServiceEndpointManager(organization_name=organization_name,
                                                          project_name=project_name, creds=self._creds)
        return service_endpoint_manager.create_service_endpoint(name)

    def list_service_endpoints(self, organization_name, project_name):
        """List the different service endpoints in a project"""
        service_endpoint_manager = ServiceEndpointManager(organization_name=organization_name,
                                                          project_name=project_name, creds=self._creds)
        return service_endpoint_manager.list_service_endpoints()

    def create_extension(self, organization_name, extension_name, publisher_name):
        """Install an azure devops extension"""
        extension_manager = ExtensionManager(organization_name=organization_name, creds=self._creds)
        return extension_manager.create_extension(extension_name, publisher_name)

    def list_extensions(self, organization_name):
        """List the azure devops extensions in an organization"""
        extension_manager = ExtensionManager(organization_name=organization_name, creds=self._creds)
        return extension_manager.list_extensions()

    def create_build_definition(self, organization_name, project_name, repository_name,
                                build_definition_name, pool_name):
        """Create a definition for an azure devops build"""
        builder_manager = BuilderManager(organization_name=organization_name, project_name=project_name,
                                         repository_name=repository_name, creds=self._creds)
        return builder_manager.create_definition(build_definition_name=build_definition_name, pool_name=pool_name)

    def list_build_definitions(self, organization_name, project_name):
        """List the azure devops build definitions within a project"""
        builder_manager = BuilderManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return builder_manager.list_definitions()

    def create_build_object(self, organization_name, project_name, build_definition_name, pool_name):
        """Create an azure devops build based off a previous definition"""
        builder_manager = BuilderManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return builder_manager.create_build(build_definition_name, pool_name)

    def list_build_objects(self, organization_name, project_name):
        """List already running and builds that have already run in an azure devops project"""
        builder_manager = BuilderManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return builder_manager.list_builds()

    def list_artifacts(self, organization_name, project_name, build_id):
        """List the azure devops artifacts from a build"""
        artifact_manager = ArtifactManager(organization_name=organization_name,
                                           project_name=project_name, creds=self._creds)
        return artifact_manager.list_artifacts(build_id)

    def create_release_definition(self, organization_name, project_name, build_name, artifact_name,
                                  pool_name, service_endpoint_name, release_definition_name, app_type,
                                  functionapp_name, storage_name, resource_name, settings):
        """Create a release definition for azure devops that is for azure functions"""
        release_manager = ReleaseManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return release_manager.create_release_definition(build_name, artifact_name, pool_name,
                                                         service_endpoint_name, release_definition_name,
                                                         app_type, functionapp_name, storage_name,
                                                         resource_name, settings=settings)

    def list_release_definitions(self, organization_name, project_name):
        """List the release definitions for azure devops"""
        release_manager = ReleaseManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return release_manager.list_release_definitions()

    def create_release(self, organization_name, project_name, release_definition_name):
        """Create a release based off a previously defined release definition"""
        release_manager = ReleaseManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return release_manager.create_release(release_definition_name)

    def list_releases(self, organization_name, project_name):
        """List the releases of an azure devops project"""
        release_manager = ReleaseManager(organization_name=organization_name,
                                         project_name=project_name, creds=self._creds)
        return release_manager.list_releases()

    def list_github_repositories(self, organization_name, project_name):
        """List the github repositories that we are connected to"""
        repository_manager = RepositoryManager(organization_name=organization_name,
                                               project_name=project_name, creds=self._creds)
        return repository_manager.list_github_repositories()
