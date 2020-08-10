# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
from collections import OrderedDict
import vsts.build.v4_1.models as build_models
from vsts.exceptions import VstsServiceError
from ..base.base_manager import BaseManager
from ..pool.pool_manager import PoolManager
from ..exceptions import (
    GithubIntegrationRequestError,
    GithubContentNotFound,
    BuildErrorException
)


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

    def create_devops_build_definition(self, build_definition_name, pool_name):
        """Create a build definition in Azure DevOps"""
        project = self._get_project_by_name(self._project_name)
        pool = self._get_pool_by_name(pool_name)

        # create the relevant objects that are needed for the build definition (this is the minimum amount needed)
        pool_queue = build_models.agent_pool_queue.AgentPoolQueue(id=pool.id, name=pool.name)
        repository = self._get_repository_by_name(project, self._repository_name)
        build_repository = build_models.build_repository.BuildRepository(
            default_branch="master",
            id=repository.id,
            name=repository.name,
            type="TfsGit"
        )
        team_project_reference = self._get_project_reference(project)
        build_definition = self._get_build_definition(
            team_project_reference, build_repository, build_definition_name, pool_queue
        )
        return self._build_client.create_definition(build_definition, project=project.name)

    def create_github_build_definition(self, build_definition_name, pool_name, github_repository):
        project = self._get_project_by_name(self._project_name)
        pool = self._get_pool_by_name(pool_name)
        pool_queue = build_models.agent_pool_queue.AgentPoolQueue(id=pool.id, name=pool.name)
        repository = self._get_github_repository_by_name(github_repository)

        if repository is None:
            raise GithubContentNotFound()

        github_properties = repository.properties
        build_repository = build_models.build_repository.BuildRepository(
            default_branch="master",
            id=repository.id,
            properties=github_properties,
            name=repository.full_name,
            type="GitHub",
            url=repository.properties['cloneUrl']
        )
        team_project_reference = self._get_project_reference(project)
        build_definition = self._get_build_definition(
            team_project_reference, build_repository, build_definition_name, pool_queue
        )
        try:
            result = self._build_client.create_definition(build_definition, project=project.name)
        except VstsServiceError as vse:
            raise GithubIntegrationRequestError(vse.message)
        return result

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
        team_project_reference = self._get_project_reference(project)
        build_definition_reference = self._get_build_definition_reference(team_project_reference, definition)
        pool_queue = build_models.agent_pool_queue.AgentPoolQueue(id=pool.id, name=pool_name)
        build = build_models.build.Build(definition=build_definition_reference, queue=pool_queue)

        try:
            result = self._build_client.queue_build(build, project=project.id)
        except VstsServiceError as vse:
            raise BuildErrorException(vse.message)
        return result

    def list_builds(self):
        """List the builds that exist in Azure DevOps"""
        project = self._get_project_by_name(self._project_name)
        return self._build_client.get_builds(project=project.id)

    # Returns a dictionary containing the log status
    # {
    #   <log_id>: <vsts.build.v4_1.models.build_log>
    # }
    def get_build_logs_status(self, build_id):
        try:
            build_logs = self._build_client.get_build_logs(self._project_name, build_id)
        except VstsServiceError as vse:
            raise BuildErrorException(vse.message)

        result = OrderedDict()
        for build_log in build_logs:
            result[build_log.id] = build_log
        return result

    # Return the log content by the difference between two logs
    def get_build_logs_content_from_statuses(self, build_id, prev_logs_status=None, curr_logs_status=None):
        if prev_logs_status is None:
            prev_logs_status = {}

        if curr_logs_status is None:
            curr_logs_status = {}

        result = []
        for log_id in curr_logs_status:
            log_content = self._get_log_content_by_id(
                build_id,
                prev_logs_status.get(log_id),
                curr_logs_status.get(log_id)
            )
            result.extend(log_content)

        return os.linesep.join(result)

    # Return the log content by single build_log
    def _get_log_content_by_id(self, build_id, prev_log_status=None, curr_log_status=None):
        if prev_log_status is None or prev_log_status.line_count is None:
            starting_line = 0
        else:
            starting_line = prev_log_status.line_count

        if curr_log_status is None or curr_log_status.line_count is None:
            ending_line = 0
        else:
            ending_line = curr_log_status.line_count

        if starting_line >= ending_line:
            return []

        try:
            result = self._build_client.get_build_log_lines(
                self._project_name,
                build_id,
                curr_log_status.id,
                starting_line,
                ending_line
            )
        except VstsServiceError as vse:
            raise BuildErrorException(vse.message)
        return result

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

    def _get_process(self):
        """Helper function to create process dictionary"""
        process = {}
        process["yamlFilename"] = "azure-pipelines.yml"
        process["type"] = 2
        process["resources"] = {}
        return process

    def _get_project_reference(self, project):
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

    def _get_triggers(self):
        trigger = {}
        trigger["branchFilters"] = []
        trigger["pathFilters"] = []
        trigger["settingsSourceType"] = 2
        trigger["batchChanges"] = False
        trigger["maxConcurrentBuildsPerBranch"] = 1
        trigger["triggerType"] = "continuousIntegration"
        triggers = [trigger]
        return triggers

    def _get_build_definition(self, team_project_reference, build_repository, build_definition_name, pool_queue):
        """Helper function to create build definition"""
        process = self._get_process()
        triggers = self._get_triggers()
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

    def _get_build_definition_reference(self, team_project_reference, build_definition):
        """Helper function to create build definition reference"""
        build_definition_reference = build_models.definition_reference.DefinitionReference(
            created_date=build_definition.created_date,
            project=team_project_reference,
            type=build_definition.type,
            name=build_definition.name,
            id=build_definition.id
        )
        return build_definition_reference
