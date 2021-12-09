# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import os
import platform
import tempfile
import time
import fileinput
import unittest

from azure.cli.testsdk import (
    ScenarioTest,
    ResourceGroupPreparer,
    StorageAccountPreparer)

from msrestazure.azure_exceptions import CloudError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

name_prefix = 'cliadm'
resource_location = 'centralus'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
curr_dir = os.path.dirname(os.path.realpath(__file__))

create_rollout_template = os.path.join(curr_dir, "createrollout.json").replace('\\', '\\\\')
failure_create_rollout_template = os.path.join(curr_dir, "createrollout_failurerollout.json").replace('\\', '\\\\')
healthcheck_file_path = os.path.join(curr_dir, "healthcheck_step.json").replace('\\', '\\\\')

parameters_file_name = "storage.parameters.json"
invalid_parameters_file_name = "storage_invalid.parameters.json"
template_file_name = "storage.template.json"
params_copy_file_name = "storage.copy.parameters.json"
template_copy_file_name = "storage.copy.template.json"
path_to_tests = ".\\azure\\cli\\command_modules\\deploymentmanager\\tests\\latest\\"
artifact_root = "artifactroot"

parametersArtifactSourceRelativePath = os.path.join(curr_dir, artifact_root, parameters_file_name)
templateArtifactSourceRelativePath = os.path.join(curr_dir, artifact_root, template_file_name)
invalidParametersArtifactSourceRelativePath = os.path.join(curr_dir, artifact_root, invalid_parameters_file_name)
parametersCopyArtifactSourceRelativePath = os.path.join(curr_dir, artifact_root, params_copy_file_name)
templateCopyArtifactSourceRelativePath = os.path.join(curr_dir, artifact_root, template_copy_file_name)


class DeploymentManagerTests(ScenarioTest):

    @unittest.skip('Deployment failed')
    @ResourceGroupPreparer(name_prefix=name_prefix, random_name_length=12, location=resource_location)
    @StorageAccountPreparer(name_prefix=name_prefix, location=resource_location)
    @AllowLargeResponse()
    def test_deploymentmanager_scenario(self, resource_group, storage_account):

        subscription_id = self.get_subscription_id()
        artifact_source_name = resource_group + "ArtifactSource"
        updated_artifact_source_name = resource_group + "ArtifactSourceUpdated"
        location = resource_location

        self.assertFalse(location is None)

        self.set_managed_identity(subscription_id, resource_group)

        artifact_source_id = self.new_artifact_source(
            resource_group,
            storage_account,
            artifact_source_name,
            location,
            True)

        self.service_topology_validations(
            subscription_id,
            resource_group,
            location,
            artifact_source_id,
            updated_artifact_source_name,
            storage_account)

        self.list_artifact_sources(resource_group, artifact_source_name)

        self.delete_artifact_source(resource_group, artifact_source_name)
        self.delete_artifact_source(resource_group, updated_artifact_source_name)

    def service_topology_validations(
            self,
            subscription_id,
            resource_group_name,
            location,
            artifact_source_id,
            updated_artifact_source_name,
            storage_account_name):

        topology_name = resource_group_name + "ServiceTopology"
        topology2_name = resource_group_name + "ServiceTopology2"

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': topology_name,
            'as_id': artifact_source_id,
        }

        self.cmd('deploymentmanager service-topology create -g {rg} -n {st_name} -l \"{location}\" --artifact-source {as_id}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies'),
            self.check('name', topology_name),
            self.check('artifactSourceId', artifact_source_id)])

        service_topology_id = self.cmd('deploymentmanager service-topology show -g {rg} -n {st_name}').get_output_in_json()['id']
        self.services_validations(
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            topology_name,
            subscription_id
        )

        updated_artifact_source_id = self.new_artifact_source(
            resource_group_name,
            storage_account_name,
            updated_artifact_source_name,
            location,
            False)

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': topology_name,
            'as_id': updated_artifact_source_id,
        }

        self.cmd('deploymentmanager service-topology update -g {rg} -n {st_name} --artifact-source {as_id}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies'),
            self.check('name', topology_name),
            self.check('artifactSourceId', updated_artifact_source_id)])

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': topology2_name,
            'as_id': artifact_source_id,
        }

        self.cmd('deploymentmanager service-topology create -g {rg} -n {st_name} -l \"{location}\" --artifact-source {as_id}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies'),
            self.check('name', topology2_name),
            self.check('artifactSourceId', artifact_source_id)])

        self.list_service_topologies(resource_group_name, topology_name)

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': topology_name,
            'as_id': artifact_source_id,
        }

        self.cmd('deploymentmanager service-topology delete -g {rg} -n {st_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager service-topology show -n {st_name} -g {rg}')

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': topology2_name,
            'as_id': artifact_source_id,
        }

        self.cmd('deploymentmanager service-topology delete -g {rg} -n {st_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager service-topology show -n {st_name} -g {rg}')

    def services_validations(
            self,
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_topology_name,
            subscription_id):

        service_name = resource_group_name + "Service"
        service2_name = resource_group_name + "Service2"

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            's2_name': service2_name,
            't_l': location,
            't_sub_id': subscription_id
        }

        self.cmd('deploymentmanager service create -g {rg} --service-topology-name {st_name} -n {s_name} -l \"{location}\" --target-location \"{t_l}\" --target-subscription-id {t_sub_id}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies/services'),
            self.check('name', service_name),
            self.check('targetLocation', location)])
        self.service_units_validations(
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_topology_name,
            service_name
        )

        # dummy subscription id created for testing. No resources are created in this.
        updated_target_subscription_id = "29843263-a568-4db8-899f-10977b9d5c7b"
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            's2_name': service2_name,
            't_l': location,
            't_sub_id': updated_target_subscription_id
        }

        self.cmd('deploymentmanager service update -g {rg} --service-topology-name {st_name} -n {s_name} --target-subscription-id {t_sub_id}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies/services'),
            self.check('name', service_name),
            self.check('targetSubscriptionId', updated_target_subscription_id)])

        self.cmd('deploymentmanager service create -g {rg} --service-topology-name {st_name} -n {s2_name} -l \"{location}\" --target-location \"{t_l}\" --target-subscription-id {t_sub_id}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies/services'),
            self.check('name', service2_name),
            self.check('targetLocation', location)])

        self.list_services(resource_group_name, service_topology_name, service_name)

        self.kwargs = {
            'rg': resource_group_name,
            'st_name': service_topology_name,
            's_name': service_name,
            's2_name': service2_name,
        }

        self.cmd('deploymentmanager service delete -g {rg} --service-topology-name {st_name} -n {s_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager service show -g {rg} --service-topology-name {st_name} -n {s_name}')

        self.cmd('deploymentmanager service delete -g {rg} --service-topology-name {st_name} -n {s2_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager service show -g {rg} --service-topology-name {st_name} -n {s2_name}')

    def service_units_validations(
            self,
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_topology_name,
            service_name):

        service_unit_name = resource_group_name + "ServiceUnit"
        deployment_mode = "Incremental"
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': service_unit_name,
            'd_mode': deployment_mode,
            'p_path': parameters_file_name,
            't_path': template_file_name
        }

        self.cmd('deploymentmanager service-unit create -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name} -l \"{location}\" --target-resource-group {rg} --deployment-mode {d_mode} --parameters-path {p_path} --template-path {t_path}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies/services/serviceUnits'),
            self.check('name', service_unit_name),
            self.check('artifacts.parametersArtifactSourceRelativePath', parameters_file_name),
            self.check('artifacts.templateArtifactSourceRelativePath', template_file_name),
            self.check('deploymentMode', deployment_mode),
            self.check('targetResourceGroup', resource_group_name)])

        service_unit_id = self.cmd('deploymentmanager service-unit show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}').get_output_in_json()['id']

        # Create a service unit that is invalid to test rollout failure operations
        invalid_service_unit_name = resource_group_name + "InvalidServiceUnit"
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': invalid_service_unit_name,
            'd_mode': deployment_mode,
            'p_path': invalid_parameters_file_name,
            't_path': template_file_name
        }

        self.cmd('deploymentmanager service-unit create -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name} -l \"{location}\" --target-resource-group {rg} --deployment-mode {d_mode} --parameters-path {p_path} --template-path {t_path}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies/services/serviceUnits'),
            self.check('name', invalid_service_unit_name),
            self.check('artifacts.parametersArtifactSourceRelativePath', invalid_parameters_file_name),
            self.check('artifacts.templateArtifactSourceRelativePath', template_file_name),
            self.check('deploymentMode', deployment_mode),
            self.check('targetResourceGroup', resource_group_name)])

        invalid_service_unit_id = self.cmd('deploymentmanager service-unit show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}').get_output_in_json()['id']
        self.steps_validations(
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_topology_name,
            service_unit_id,
            invalid_service_unit_id)

        deployment_mode = "Complete"
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': service_unit_name,
            'd_mode': deployment_mode,
            'p_path': parameters_file_name,
            't_path': template_file_name
        }

        self.cmd('deploymentmanager service-unit update -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name} --deployment-mode {d_mode}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/serviceTopologies/services/serviceUnits'),
            self.check('name', service_unit_name),
            self.check('deploymentMode', deployment_mode)])

        self.list_service_units(resource_group_name, service_topology_name, service_name, service_unit_name)

        self.kwargs = {
            'rg': resource_group_name,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': service_unit_name,
        }

        self.cmd('deploymentmanager service-unit delete -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager service-unit show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')

        self.kwargs = {
            'rg': resource_group_name,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': invalid_service_unit_name,
        }

        self.cmd('deploymentmanager service-unit delete -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager service-unit show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')

    def steps_validations(
            self,
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_topology_name,
            service_unit_id,
            invalid_service_unit_id):

        step_name = resource_group_name + "WaitStep"
        duration = "PT5M"
        updated_duration = "PT10M"

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'step_name': step_name,
            'duration': duration
        }

        self.cmd('deploymentmanager step create -g {rg} -l \"{location}\" -n {step_name} --duration {duration}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step_name),
            self.check('properties.stepType', 'Wait'),
            self.check('properties.attributes.duration', duration)])

        step_id = self.cmd('deploymentmanager step show -g {rg} -n {step_name}').get_output_in_json()['id']

        self.rollouts_validations(
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_unit_id,
            invalid_service_unit_id,
            step_id
        )

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'step_name': step_name,
            'duration': updated_duration
        }

        self.cmd('deploymentmanager step update -g {rg} -n {step_name} --duration {duration}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step_name),
            self.check('properties.attributes.duration', updated_duration)])

        self.healthcheck_step_validations(resource_group_name, location)

        self.kwargs = {
            'rg': resource_group_name,
            'step_name': step_name
        }

        self.cmd('deploymentmanager step delete -g {rg} -n {step_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager step show -g {rg} -n {step_name}')

    def healthcheck_step_validations(
            self,
            resource_group_name,
            location):

        step_name = resource_group_name + "RestHealthCheckStep"
        updated_healthy_state_duration = "PT30M"

        self.replace_string("__HEALTH_CHECK_STEP_NAME__", step_name, healthcheck_file_path, True)

        self.kwargs = {
            'rg': resource_group_name,
            'step_name': step_name,
            'rest_health_check_file': healthcheck_file_path,
            'healthy_state_duration': updated_healthy_state_duration
        }

        json_obj = None
        with open(healthcheck_file_path) as f:
            json_obj = json.load(f)

        self.cmd('deploymentmanager step create -g {rg} --step "{rest_health_check_file}"', checks=[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step_name),
            self.check('properties.stepType', 'HealthCheck'),
            self.check('properties.attributes.waitDuration', json_obj['properties']['attributes']['waitDuration']),
            self.check('properties.attributes.maxElasticDuration', json_obj['properties']['attributes']['maxElasticDuration']),
            self.check('properties.attributes.healthyStateDuration', json_obj['properties']['attributes']['healthyStateDuration'])])

        step_id = self.cmd('deploymentmanager step show -g {rg} -n {step_name}').get_output_in_json()['id']
        self.assertFalse(step_id is None)

        # Revert health check file change for playback mode.
        self.replace_string(step_name, "__HEALTH_CHECK_STEP_NAME__", healthcheck_file_path, True)

        json_obj['properties']['attributes']['healthyStateDuration'] = updated_healthy_state_duration

        serialized_json = json.dumps(json_obj)
        self.assertFalse(serialized_json is None)

        self.kwargs = {
            'rg': resource_group_name,
            'step_name': step_name,
            'step': serialized_json
        }

        self.cmd('deploymentmanager step update -g {rg} -n {step_name} --step \'{step}\'', checks=[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step_name),
            self.check('properties.attributes.healthyStateDuration', updated_healthy_state_duration)])

        step2_name = resource_group_name + "RestHealthCheckStep2"
        json_obj['name'] = step2_name

        serialized_json = json.dumps(json_obj)
        self.assertFalse(serialized_json is None)

        self.kwargs = {
            'rg': resource_group_name,
            'step': serialized_json
        }

        self.cmd('deploymentmanager step create -g {rg} --step \'{step}\'', checks=[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step2_name),
            self.check('properties.stepType', 'HealthCheck'),
            self.check('properties.attributes.healthyStateDuration', updated_healthy_state_duration)])

        self.list_steps(resource_group_name, step_name)

        self.kwargs = {
            'rg': resource_group_name,
            'step_name': step_name
        }

        self.cmd('deploymentmanager step delete -g {rg} -n {step_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager step show -g {rg} -n {step_name}')

        self.kwargs = {
            'rg': resource_group_name,
            'step2_name': step2_name
        }

        self.cmd('deploymentmanager step delete -g {rg} -n {step2_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager step show -g {rg} -n {step2_name}')

    def rollouts_validations(
            self,
            resource_group_name,
            location,
            artifact_source_id,
            service_topology_id,
            service_unit_id,
            invalid_service_unit_id,
            step_id):

        rollout_name = resource_group_name + "Rollout"
        failed_rollout_name = resource_group_name + "InvalidRollout"

        self.replace_rollout_placeholders(
            rollout_name,
            service_topology_id,
            artifact_source_id,
            step_id,
            service_unit_id,
            create_rollout_template
        )

        self.replace_rollout_placeholders(
            failed_rollout_name,
            service_topology_id,
            artifact_source_id,
            step_id,
            invalid_service_unit_id,
            failure_create_rollout_template
        )

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            't_path': create_rollout_template,
            'invalid_t_path': failure_create_rollout_template,
            'rollout_name': rollout_name,
            'failed_rollout_name': failed_rollout_name
        }

        self.cmd('group deployment create -g {rg} --template-file "{t_path}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')])

        self.cmd('deploymentmanager rollout show -g {rg} -n {rollout_name}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('status', 'Running'),
            self.check('totalRetryAttempts', '0'),
            self.check('operationInfo.retryAttempt', '0'),
            self.check('artifactSourceId', artifact_source_id),
            self.check('targetServiceTopologyId', service_topology_id)])

        self.cmd('deploymentmanager rollout stop -g {rg} -n {rollout_name} --yes', checks=[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('status', 'Canceling')])

        while True:
            self.sleep(120)
            rollout = self.cmd('deploymentmanager rollout show -g {rg} -n {rollout_name}').get_output_in_json()
            if (rollout['status'] != 'Canceling'):
                break

        self.assertEqual('Canceled', rollout['status'])

        self.cmd('group deployment create -g {rg} --template-file "{invalid_t_path}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')])

        self.cmd('deploymentmanager rollout show -g {rg} -n {failed_rollout_name}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('totalRetryAttempts', '0'),
            self.check('operationInfo.retryAttempt', '0'),
            self.check('artifactSourceId', artifact_source_id),
            self.check('targetServiceTopologyId', service_topology_id)])

        # Now validate that the rollout expected to fail has failed.
        while True:
            self.sleep(120)
            failed_rollout = self.cmd('deploymentmanager rollout show -g {rg} -n {failed_rollout_name}').get_output_in_json()
            if (failed_rollout['status'] != 'Running'):
                break

        self.assertEqual('Failed', failed_rollout['status'])

        self.cmd('deploymentmanager rollout restart -g {rg} -n {failed_rollout_name} --skip-succeeded --yes', checks=[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('operationInfo.retryAttempt', '1'),
            self.check('operationInfo.skipSucceededOnRetry', True),
            self.check('status', 'Running')])

        self.cmd('deploymentmanager rollout stop -g {rg} -n {failed_rollout_name} --yes', checks=[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('operationInfo.retryAttempt', '1'),
            self.check('operationInfo.skipSucceededOnRetry', True),
            self.check('status', 'Canceling')])

        while True:
            self.sleep(120)
            failed_rollout = self.cmd('deploymentmanager rollout show -g {rg} -n {failed_rollout_name}').get_output_in_json()
            if (failed_rollout['status'] != 'Canceling'):
                break

        self.cmd('deploymentmanager rollout delete -g {rg} -n {failed_rollout_name}')
        self.cmd('deploymentmanager rollout delete -g {rg} -n {rollout_name}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager rollout show -g {rg} -n {failed_rollout_name}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager rollout show -g {rg} -n {rollout_name}')

    def set_managed_identity(self, subscription_id, resource_group_name):

        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            identity_name = resource_group_name + "Identity"
            self.kwargs = {
                'rg': resource_group_name,
                'name': identity_name,
            }
            identity = self.cmd('identity create -n {name} -g {rg}').get_output_in_json()
            identityId = identity['id']

            self.sleep(120)

            self.kwargs = {
                'rg': resource_group_name,
                'principalId': identity['principalId'],
                'role': "Contributor",
                'scope': "/subscriptions/{0}".format(subscription_id),
            }

            self.cmd('role assignment create --assignee {principalId} --role {role} --scope {scope}')

            self.sleep(30)

            self.replace_string("__USER_ASSIGNED_IDENTITY__", identityId, create_rollout_template)
            self.replace_string("__USER_ASSIGNED_IDENTITY__", identityId, failure_create_rollout_template)

            return identityId

        return "dummyid"

    def new_artifact_source(
            self,
            resource_group_name,
            storage_account_name,
            artifact_source_name,
            location,
            setup_container):

        artifact_root = "artifactroot"
        container_name = "artifacts"

        sas_uri = self.get_sas_for_artifacts_container(
            resource_group_name,
            storage_account_name,
            container_name,
            artifact_root,
            setup_container)

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'as_name': artifact_source_name,
            'sas': sas_uri,
            'artifactroot': artifact_root
        }

        self.cmd('deploymentmanager artifact-source create -g {rg} -n {as_name} -l \"{location}\" --sas-uri \"{sas}\" --artifact-root {artifactroot}', checks=[
            self.check('type', 'Microsoft.DeploymentManager/artifactSources'),
            self.check('artifactRoot', artifact_root),
            self.check('name', artifact_source_name)
        ])

        return self.cmd('deploymentmanager artifact-source show -g {rg} -n {as_name}').get_output_in_json()['id']

    def get_sas_for_artifacts_container(
            self,
            resource_group_name,
            storage_account_name,
            storage_container_name,
            artifact_root,
            setup_container):

        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            if setup_container:
                self.setup_artifacts_container(resource_group_name, storage_account_name, storage_container_name)

            return self.create_sas_key_for_container(storage_account_name, storage_container_name)

        return "dummysasforcontainer"

    def create_sas_key_for_container(self, storage_account_name, container_name):
        from datetime import datetime, timedelta
        start = (datetime.utcnow() + timedelta(hours=-1)).strftime('%Y-%m-%dT%H:%MZ')
        expiry = (datetime.utcnow() + timedelta(hours=10)).strftime('%Y-%m-%dT%H:%MZ')
        self.kwargs = {
            'account': storage_account_name,
            'container': container_name,
            'expiry': expiry,
            'start': start
        }

        sas = self.cmd('storage container generate-sas -n {container} --account-name {account} '
                       '--permissions rl --start {start} --expiry {expiry} -otsv').output.strip()

        full_uri = "https://" + storage_account_name + ".blob.core.windows.net/" + container_name + "?" + sas
        return full_uri

    def setup_artifacts_container(self, resource_group_name, storage_account_name, container_name):
        stgAcctForTemplate = resource_group_name + "stgtemplate"
        storageAcountReplacementSymbol = "__STORAGEACCOUNTNAME__"

        self.replace_string(storageAcountReplacementSymbol, stgAcctForTemplate, parametersArtifactSourceRelativePath)
        self.replace_string(storageAcountReplacementSymbol, stgAcctForTemplate, parametersCopyArtifactSourceRelativePath)

        storage_account_info = self.get_stg_account_info(resource_group_name, storage_account_name)
        self.create_container(storage_account_info, container_name)

        self.upload_blob(storage_account_info, container_name, parametersArtifactSourceRelativePath, parameters_file_name)
        self.upload_blob(storage_account_info, container_name, parametersCopyArtifactSourceRelativePath, params_copy_file_name)
        self.upload_blob(storage_account_info, container_name, templateArtifactSourceRelativePath, template_file_name)
        self.upload_blob(storage_account_info, container_name, templateCopyArtifactSourceRelativePath, template_copy_file_name)
        self.upload_blob(storage_account_info, container_name, invalidParametersArtifactSourceRelativePath, invalid_parameters_file_name)

    def list_steps(self, resource_group_name, step_name):
        self.kwargs = {
            'rg': resource_group_name,
            'step_name': step_name
        }

        steps = self.cmd('deploymentmanager step list -g {rg}', checks=[
            self.check("length(@)", 3)
        ]).get_output_in_json()

        selected_step = [x for x in steps if(x['name'].lower() == step_name.lower())]
        self.assertIsNotNone(selected_step, "list steps did not return {step_name}.")

    def list_service_units(self, resource_group_name, service_topology_name, service_name, service_unit_name):
        self.kwargs = {
            'rg': resource_group_name,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': service_unit_name
        }

        service_units = self.cmd('deploymentmanager service-unit list -g {rg} --service-topology-name {st_name} --service-name {s_name}', checks=[
            self.check("length(@)", 2)
        ]).get_output_in_json()

        selected_service_unit = [x for x in service_units if(x['name'].lower() == service_unit_name.lower())]
        self.assertIsNotNone(selected_service_unit, "list service units did not return {su_name}.")

    def list_services(self, resource_group_name, service_topology_name, service_name):
        self.kwargs = {
            'rg': resource_group_name,
            'st_name': service_topology_name
        }

        services = self.cmd('deploymentmanager service list -g {rg} --service-topology-name {st_name}', checks=[
            self.check("length(@)", 2)
        ]).get_output_in_json()

        self.kwargs = {
            's_name': service_name
        }

        selected_service = [x for x in services if(x['name'].lower() == service_name.lower())]
        self.assertIsNotNone(selected_service, "list services did not return {s_name}.")

    def list_service_topologies(self, resource_group_name, service_topology_name):
        self.kwargs = {
            'rg': resource_group_name
        }

        service_topologies = self.cmd('deploymentmanager service-topology list -g {rg}', checks=[
            self.check("length(@)", 2)
        ]).get_output_in_json()

        self.kwargs = {
            'st_name': service_topology_name
        }

        selected_service_topology = [x for x in service_topologies if(x['name'].lower() == service_topology_name.lower())]
        self.assertIsNotNone(selected_service_topology, "list service topologies did not return {st_name}.")

    def list_artifact_sources(self, resource_group_name, artifact_source_name):
        self.kwargs = {
            'rg': resource_group_name
        }

        artifact_sources = self.cmd('deploymentmanager artifact-source list -g {rg}', checks=[
            self.check("length(@)", 2)
        ]).get_output_in_json()

        self.kwargs = {
            'as_name': artifact_source_name
        }

        selected_artifact_source = [x for x in artifact_sources if(x['name'].lower() == artifact_source_name.lower())]
        self.assertIsNotNone(selected_artifact_source, "list artifact sources did not return {as_name}.")

    def delete_artifact_source(self, resource_group_name, artifact_source_name):
        self.kwargs = {
            'rg': resource_group_name,
            'name': artifact_source_name,
        }
        self.cmd('deploymentmanager artifact-source delete -n {name} -g {rg} --yes')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('deploymentmanager artifact-source show -n {name} -g {rg}')

    def upload_blob(self, storage_account_info, storage_container_name, file_path, file_name):
        abs_file_path = os.path.join(TEST_DIR, file_path).replace('\\', '\\\\')
        blob_path = artifact_root + "/" + file_name
        self.storage_cmd('storage blob upload -c {} -n {} -f "{}" -t block', storage_account_info,
                         storage_container_name, blob_path, abs_file_path)

    def get_stg_account_key(self, group, name):

        template = 'storage account keys list -n {} -g {} --query "[0].value" -otsv'
        return self.cmd(template.format(name, group)).output

    def get_stg_account_info(self, group, name):
        """Returns the storage account name and key in a tuple"""
        return name, self.get_stg_account_key(group, name)

    def create_container(self, account_info, container_name):
        self.storage_cmd('storage container create -n {}', account_info, container_name)
        return container_name

    def storage_cmd(self, cmd, account_info, *args):
        cmd = cmd.format(*args)
        cmd = '{} --account-name {} --account-key {}'.format(cmd, *account_info)
        return self.cmd(cmd)

    def replace_string(self, replacement_symbol, replacement_value, filePath, overridePlayback=False):
        is_playback = os.path.exists(self.recording_file)
        if (not is_playback or overridePlayback):
            file = fileinput.FileInput(filePath, inplace=True)
            for line in file:
                print(line.replace(replacement_symbol, replacement_value), end='')
            file.close()

    def replace_rollout_placeholders(
        self,
        rollout_name,
        target_service_topology_id,
        artifact_source_id,
        step_id,
        service_unit_id,
        file_path
    ):
        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            self.replace_string("__ROLLOUT_NAME__", rollout_name, file_path)
            self.replace_string("__TARGET_SERVICE_TOPOLOGY__", target_service_topology_id, file_path)
            self.replace_string("__ARTIFACT_SOURCE_ID__", artifact_source_id, file_path)
            self.replace_string("__STEP_ID__", step_id, file_path)
            self.replace_string("__SERVICE_UNIT_ID__", service_unit_id, file_path)

    def sleep(self, duration):
        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            time.sleep(duration)
