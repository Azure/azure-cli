# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging

import vsts.release.v4_1.models as models
from vsts.exceptions import VstsServiceError
from ..base.base_manager import BaseManager
from ..pool.pool_manager import PoolManager
from ..constants import (LINUX_CONSUMPTION, LINUX_DEDICATED, WINDOWS)
from ..exceptions import ReleaseErrorException


class ReleaseManager(BaseManager):
    """ Manage DevOps releases

    Attributes:
        See BaseManager
    """
    def __init__(self, organization_name="", project_name="", creds=None):
        super(ReleaseManager, self).__init__(creds, organization_name=organization_name, project_name=project_name)

    def create_release_definition(self, build_name, artifact_name, pool_name, service_endpoint_name,
                                  release_definition_name, app_type, functionapp_name, storage_name,
                                  resource_name, settings=None):
        pool = self._get_pool_by_name(pool_name)
        project = self._get_project_by_name(self._project_name)
        build = self._get_build_by_name(project, build_name)
        retention_policy_environment = self._get_retention_policy()
        artifact = self._get_artifact(build, project, artifact_name)
        pre_release_approvals, post_release_approvals = self._get_pre_post_approvals()
        service_endpoint = self._get_service_endpoint_by_name(project, service_endpoint_name)
        release_deploy_step = models.release_definition_deploy_step.ReleaseDefinitionDeployStep(id=2)
        triggers = self._get_triggers(artifact_name)
        deployment_input = self._get_deployment_input(pool.id)

        phase_inputs = self._get_phase_inputs(artifact_name)

        workflowtasks = []

        if app_type == LINUX_CONSUMPTION:
            workflowtasks.append(self._blob_task(service_endpoint.id, storage_name))
            workflowtasks.append(self._sas_token_task(service_endpoint.id, storage_name))
            workflowtasks.append(self._app_settings_task(service_endpoint.id, functionapp_name, resource_name))
        elif app_type == LINUX_DEDICATED:
            workflowtasks.append(self._app_service_deploy_task_linux(service_endpoint.id, functionapp_name))
        elif app_type == WINDOWS:
            workflowtasks.append(self._app_service_deploy_task_windows(service_endpoint.id, functionapp_name))
        else:
            logging.error("Invalid app type provided. Correct types are: "
                          "Linux Consumption: %s, Linux Dedicated: %s, Windows: %s",
                          LINUX_CONSUMPTION, LINUX_DEDICATED, WINDOWS)

        if settings is not None:
            settings_str = ""
            for setting in settings:
                settings_str += (setting[0] + "='" + setting[1] + "'")
            # Check that settings were actually set otherwise we don't want to use the task
            if settings_str != "":
                workflowtasks.append(self._app_settings_task_customized(
                    service_endpoint.id, functionapp_name, resource_name, settings_str
                ))

        deploy_phases = self._get_deploy_phases(deployment_input, workflowtasks, phase_inputs)

        condition = models.condition.Condition(condition_type=1, name="ReleaseStarted", value="")

        release_definition_environment = models.release_definition_environment.ReleaseDefinitionEnvironment(
            name="deploy build",
            rank=1,
            retention_policy=retention_policy_environment,
            pre_deploy_approvals=pre_release_approvals,
            post_deploy_approvals=post_release_approvals,
            deploy_phases=deploy_phases,
            deploy_step=release_deploy_step,
            conditions=[condition]
        )

        release_definition = models.release_definition.ReleaseDefinition(
            name=release_definition_name,
            environments=[release_definition_environment],
            artifacts=[artifact],
            triggers=triggers
        )

        return self._release_client.create_release_definition(release_definition, project.id)

    def list_release_definitions(self):
        project = self.get_project_by_name(self._project_name)
        return self._release_client.get_release_definitions(project.id)

    def create_release(self, release_definition_name):
        project = self.get_project_by_name(self._project_name)
        release_definition = self.get_release_definition_by_name(project, release_definition_name)

        release_start_metadata = models.release_start_metadata.ReleaseStartMetadata(
            definition_id=release_definition.id,
            is_draft=False,
            properties={"ReleaseCreationSource": "ReleaseHub"}
        )

        try:
            new_release = self._release_client.create_release(release_start_metadata, project.id)
        except VstsServiceError as vse:
            raise ReleaseErrorException(vse.message)
        return new_release

    def list_releases(self):
        project = self.get_project_by_name(self._project_name)
        return self._release_client.get_releases(project.id)

    def get_latest_release(self, release_definition_name):
        project = self.get_project_by_name(self._project_name)
        build_definition = self.get_release_definition_by_name(project, release_definition_name)

        try:
            releases = self._release_client.get_releases(self._project_name, definition_id=build_definition.id)
        except VstsServiceError:
            return None

        releases.sort(key=lambda r: r.id, reverse=True)
        if releases:
            return releases[0]
        return None

    def _get_service_endpoint_by_name(self, project, service_endpoint_name):
        service_endpoints = self._service_endpoint_client.get_service_endpoints(project.id)
        return next((service_endpoint for service_endpoint in service_endpoints
                     if service_endpoint.name == service_endpoint_name), None)

    def _get_pool_by_name(self, pool_name):
        """Helper function to get the pool object from its name"""
        pool_manager = PoolManager(organization_name=self._organization_name,
                                   project_name=self._project_name, creds=self._creds)
        pools = pool_manager.list_pools()
        return next((pool for pool in pools.value if pool.name == pool_name), None)

    def get_project_by_name(self, name):
        for p in self._core_client.get_projects():
            if p.name == name:
                return p
        return None

    def get_release_definition_by_name(self, project, name):
        for p in self._release_client.get_release_definitions(project.id):
            if p.name == name:
                return p
        return None

    def _get_triggers(self, artifact_name):
        trigger = {}
        trigger["triggerType"] = "artifactSource"
        trigger["triggerConditions"] = []
        trigger["artifactAlias"] = artifact_name
        triggers = [trigger]
        return triggers

    def _get_deployment_input(self, pool_id):
        deployment_input = {}
        deployment_input["parallelExecution"] = {"parallelExecutionType": 0}
        deployment_input["queueId"] = pool_id
        return deployment_input

    def _get_phase_inputs(self, artifact_name):
        phase_inputs = {}
        download_input = {}
        download_input["artifactItems"] = []
        download_input["alias"] = artifact_name
        download_input["artifactType"] = "Build"
        download_input["artifactDownloadMode"] = "All"
        artifacts_download_input = {}
        artifacts_download_input["downloadInputs"] = [download_input]
        phase_input_artifact_download_input = {}
        phase_input_artifact_download_input["skipArtifactsDownload"] = False
        phase_input_artifact_download_input["artifactsDownloadInput"] = artifacts_download_input
        phase_inputs["phaseinput_artifactdownloadinput"] = phase_input_artifact_download_input
        return phase_inputs

    def _get_deploy_phases(self, deployment_input, workflowtasks, phase_inputs):
        deploy_phase = {}
        deploy_phase["deploymentInput"] = deployment_input
        deploy_phase["rank"] = 1
        deploy_phase["phaseType"] = 1
        deploy_phase["name"] = "Agent Job"
        deploy_phase["workflowTasks"] = workflowtasks
        deploy_phase["phaseInputs"] = phase_inputs

        deploy_phases = [deploy_phase]

        return deploy_phases

    def _get_retention_policy(self):
        return models.environment_retention_policy.EnvironmentRetentionPolicy(
            days_to_keep=300, releases_to_keep=3, retain_build=True
        )

    def _get_artifact(self, build, project, artifact_name):
        artifacts = self._build_client.get_artifacts(build.id, project.id)
        artifact = None
        for a in artifacts:
            if a.name == artifact_name:
                artifact = a
        definition_reference = {}
        definition_reference["project"] = {"id": project.id, "name": project.name}
        definition_reference["definition"] = {"id": build.definition.id, "name": build.definition.name}
        definition_reference["defaultVersionType"] = {"id": "latestType", "name": "Latest"}

        return models.artifact.Artifact(
            source_id=artifact.id,
            alias=artifact.name,
            type="Build",
            definition_reference=definition_reference)

    def _get_pre_post_approvals(self):
        pre_approval = models.release_definition_approval_step.ReleaseDefinitionApprovalStep(
            id=0,
            rank=1,
            is_automated=True,
            is_notification_on=False
        )

        post_approval = models.release_definition_approval_step.ReleaseDefinitionApprovalStep(
            id=0,
            rank=1,
            is_automated=True,
            is_notification_on=False
        )

        pre_release_approvals = models.release_definition_approvals.ReleaseDefinitionApprovals(
            approvals=[pre_approval]
        )

        post_release_approvals = models.release_definition_approvals.ReleaseDefinitionApprovals(
            approvals=[post_approval]
        )

        return pre_release_approvals, post_release_approvals

    def _blob_task(self, connectedServiceNameARM, storage_name):
        blobtask = {}
        blobtask["name"] = "AzureBlob File Copy"
        blobtask["enabled"] = True
        blobtask_inputs = {}
        blobtask_inputs["SourcePath"] = "$(System.DefaultWorkingDirectory)/drop/drop/build$(Build.BuildId).zip"
        blobtask_inputs["ConnectedServiceNameSelector"] = 'ConnectedServiceNameARM'
        blobtask_inputs["ConnectedServiceNameARM"] = connectedServiceNameARM
        blobtask_inputs["Destination"] = "AzureBlob"
        blobtask_inputs["StorageAccountRM"] = storage_name
        blobtask_inputs["ContainerName"] = 'azure-build'
        blobtask_inputs["outputStorageUri"] = "outputstorageuri"
        blobtask_inputs["outputStorageContainerSasToken"] = "sastoken"
        blobtask["inputs"] = blobtask_inputs
        blobtask["version"] = "2.*"
        blobtask["definitionType"] = "task"
        blobtask["taskId"] = "eb72cb01-a7e5-427b-a8a1-1b31ccac8a43"
        return blobtask

    def _sas_token_task(self, connectedServiceNameARM, storage_name):
        sastokentask = {}
        sastokentask["name"] = "Create SAS Token for Storage Account " + storage_name
        sastokentask["enabled"] = True
        sastokentask["taskId"] = "9e0b2bda-6a8d-4215-8e8c-3d47614db813"
        sastokentask["version"] = "1.*"
        sastokentask["definitionType"] = "task"
        sastokentask_inputs = {}
        sastokentask_inputs["ConnectedServiceName"] = connectedServiceNameARM
        sastokentask_inputs["StorageAccountRM"] = storage_name
        sastokentask_inputs["SasTokenTimeOutInHours"] = 10000
        sastokentask_inputs["Permission"] = "r"
        sastokentask_inputs["StorageContainerName"] = "azure-build"
        sastokentask_inputs["outputStorageUri"] = "storageUri"
        sastokentask_inputs["outputStorageContainerSasToken"] = "storageToken"
        sastokentask["inputs"] = sastokentask_inputs
        return sastokentask

    def _app_settings_task(self, connectedServiceNameARM, functionapp_name, resource_name):
        appsetttingstask = {}
        appsetttingstask["name"] = "Set App Settings: "
        appsetttingstask["enabled"] = True
        appsetttingstask["taskId"] = "9d2e4cf0-f3bb-11e6-978b-770d284f4f2d"
        appsetttingstask["version"] = "2.*"
        appsetttingstask["definitionType"] = "task"
        appsetttingstask_inputs = {}
        appsetttingstask_inputs["ConnectedServiceName"] = connectedServiceNameARM
        appsetttingstask_inputs["WebAppName"] = functionapp_name
        appsetttingstask_inputs["ResourceGroupName"] = resource_name
        appsetttingstask_inputs["AppSettings"] = (
            "WEBSITE_RUN_FROM_PACKAGE='$(storageUri)/build$(Build.BuildId).zip$(storageToken)'"
        )
        appsetttingstask["inputs"] = appsetttingstask_inputs
        return appsetttingstask

    def _app_settings_task_customized(self, connectedServiceNameARM, functionapp_name, resource_name, settings):
        appsetttingstask = {}
        appsetttingstask["name"] = "Set App Settings: "
        appsetttingstask["enabled"] = True
        appsetttingstask["taskId"] = "9d2e4cf0-f3bb-11e6-978b-770d284f4f2d"
        appsetttingstask["version"] = "2.*"
        appsetttingstask["definitionType"] = "task"
        appsetttingstask_inputs = {}
        appsetttingstask_inputs["ConnectedServiceName"] = connectedServiceNameARM
        appsetttingstask_inputs["WebAppName"] = functionapp_name
        appsetttingstask_inputs["ResourceGroupName"] = resource_name
        appsetttingstask_inputs["AppSettings"] = settings
        appsetttingstask["inputs"] = appsetttingstask_inputs
        return appsetttingstask

    def _app_service_deploy_task_linux(self, connectedServiceNameARM, functionapp_name):
        appservicetask = {}
        appservicetask["name"] = "Azure App Service Deploy: " + functionapp_name
        appservicetask["enabled"] = True
        appservicetask["taskId"] = "497d490f-eea7-4f2b-ab94-48d9c1acdcb1"
        appservicetask["version"] = "4.*"
        appservicetask["definitionType"] = "task"
        appservicetask_inputs = {}
        appservicetask_inputs["ConnectionType"] = "AzureRM"
        appservicetask_inputs["ConnectedServiceName"] = connectedServiceNameARM
        appservicetask_inputs["PublishProfilePath"] = "$(System.DefaultWorkingDirectory)/**/*.pubxml"
        appservicetask_inputs["WebAppKind"] = "functionAppLinux"
        appservicetask_inputs["WebAppName"] = functionapp_name
        appservicetask_inputs["SlotName"] = "production"
        appservicetask_inputs["Package"] = "$(System.DefaultWorkingDirectory)/**/*.zip"
        appservicetask["inputs"] = appservicetask_inputs
        return appservicetask

    def _app_service_deploy_task_windows(self, connectedServiceNameARM, functionapp_name):
        appservicetask = {}
        appservicetask["name"] = "Azure App Service Deploy: " + functionapp_name
        appservicetask["enabled"] = True
        appservicetask["taskId"] = "497d490f-eea7-4f2b-ab94-48d9c1acdcb1"
        appservicetask["version"] = "4.*"
        appservicetask["definitionType"] = "task"
        appservicetask_inputs = {}
        appservicetask_inputs["ConnectionType"] = "AzureRM"
        appservicetask_inputs["ConnectedServiceName"] = connectedServiceNameARM
        appservicetask_inputs["PublishProfilePath"] = "$(System.DefaultWorkingDirectory)/**/*.pubxml"
        appservicetask_inputs["WebAppKind"] = "functionAppWindows"
        appservicetask_inputs["WebAppName"] = functionapp_name
        appservicetask_inputs["SlotName"] = "production"
        appservicetask_inputs["Package"] = "$(System.DefaultWorkingDirectory)/**/*.zip"
        appservicetask["inputs"] = appservicetask_inputs
        return appservicetask
