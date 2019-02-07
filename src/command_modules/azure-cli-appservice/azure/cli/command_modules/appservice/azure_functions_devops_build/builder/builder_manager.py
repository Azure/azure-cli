# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import vsts.build.v4_1.models as build_models
from ..base.base_manager import BaseManager
from ..pool.pool_manager import PoolManager


class BuilderManager(BaseManager):
    """ Manage DevOps Builds

    This class enables users to create DevOps build definitions and builds specifically for yaml file builds.
    It can also be used to retrieve existing build definitions and builds.

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", project_name="", repository_name="", creds=None):
        """Inits BuilderManager as per BaseManager"""
        super(BuilderManager, self).__init__(creds, organization_name, project_name, repository_name=repository_name)

    def create_definition(self, build_definition_name, pool_name, github=False):
        """Create a build definition in Azure DevOps"""
        project = self._get_project_by_name(self._project_name)
        pool = self._get_pool_by_name(pool_name)

        # create the relevant objects that are needed for the build definition (this is the minimum amount needed)
        pool_queue = build_models.agent_pool_queue.AgentPoolQueue(id=pool.id, name=pool.name)
        if github:
            repository = self._get_github_repository_by_name(project, self._repository_name)
            github_properties = repository.properties
            build_repository = build_models.build_repository.BuildRepository(default_branch="master", id=repository.id,
                                                                             properties=github_properties, name=repository.full_name,  # pylint: disable=line-too-long
                                                                             type="GitHub", url=repository.properties['cloneUrl'])   # pylint: disable=line-too-long
        else:
            repository = self._get_repository_by_name(project, self._repository_name)
            build_repository = build_models.build_repository.BuildRepository(default_branch="master", id=repository.id,
                                                                             name=repository.name, type="TfsGit")
        team_project_reference = _get_project_reference(project)
        build_definition = _get_build_definition(team_project_reference, build_repository,
                                                 build_definition_name, pool_queue)

        return self._build_client.create_definition(build_definition, project=project.name)

    def list_definitions(self):
        """List the build definitions that exist in Azure DevOps"""
        project = self._get_project_by_name(self._project_name)
        return self._build_client.get_definitions(project=project.id)

    def create_build(self, build_definition_name, pool_name):
        """Create a build definition in Azure DevOps"""
        pool = self._get_pool_by_name(pool_name)
        project = self._get_project_by_name(self._project_name)
        definition = self._get_definition_by_name(project, build_definition_name)

        # create the relevant objects that are needed for the build (this is the minimum amount needed)
        team_project_reference = _get_project_reference(project)
        build_definition_reference = _get_build_definition_reference(team_project_reference, definition)
        pool_queue = build_models.agent_pool_queue.AgentPoolQueue(id=pool.id, name=pool_name)
        build = build_models.build.Build(definition=build_definition_reference, queue=pool_queue)

        return self._build_client.queue_build(build, project=project.id)

    def list_builds(self):
        """List the builds that exist in Azure DevOps"""
        project = self._get_project_by_name(self._project_name)
        return self._build_client.get_builds(project=project.id)

    def _get_build_by_id(self, build_id):
        builds = self.list_builds()
        return next((build for build in builds if build.id == build_id))

    def poll_build(self, build_name):
        project = self._get_project_by_name(self._project_name)
        build = self._get_build_by_name(project, build_name)
        while build.status != 'completed':
            time.sleep(1)
            build = self._get_build_by_id(build.id)
        return build

    def _get_pool_by_name(self, pool_name):
        """Helper function to get the pool object from its name"""
        pool_manager = PoolManager(organization_name=self._organization_name,
                                   project_name=self._project_name, creds=self._creds)
        pools = pool_manager.list_pools()
        return next((pool for pool in pools.value if pool.name == pool_name), None)


def _get_build_definition(team_project_reference, build_repository, build_definition_name, pool_queue):
    """Helper function to create build definition"""
    process = _get_process()
    triggers = _get_triggers()
    build_definition = build_models.build_definition.BuildDefinition(
        project=team_project_reference,
        type=2,
        name=build_definition_name,
        process=process,
        repository=build_repository,
        triggers=triggers,
        queue=pool_queue
    )
    return build_definition


def _get_build_definition_reference(team_project_reference, build_definition):
    """Helper function to create build definition reference"""
    build_definition_reference = build_models.definition_reference.DefinitionReference(
        created_date=build_definition.created_date,
        project=team_project_reference,
        type=build_definition.type,
        name=build_definition.name,
        id=build_definition.id
    )
    return build_definition_reference


def _get_process():
    """Helper function to create process dictionary"""
    process = {}
    process["yamlFilename"] = "azure-pipelines.yml"
    process["type"] = 2
    process["resources"] = {}
    return process


def _get_project_reference(project):
    """Helper function to create project reference"""
    team_project_reference = build_models.team_project_reference.TeamProjectReference(
        abbreviation=project.abbreviation,
        description=project.description,
        id=project.id,
        name=project.name,
        revision=project.revision,
        state=project.state,
        url=project.url,
        visibility=project.visibility
    )
    return team_project_reference


def _get_triggers():
    trigger = {}
    trigger["branchFilters"] = []
    trigger["pathFilters"] = []
    trigger["settingsSourceType"] = 2
    trigger["batchChanges"] = False
    trigger["maxConcurrentBuildsPerBranch"] = 1
    trigger["triggerType"] = "continuousIntegration"
    triggers = [trigger]
    return triggers
