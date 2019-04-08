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

from azure.cli.testsdk import (
    ScenarioTest, 
    ResourceGroupPreparer, 
    StorageAccountPreparer)

from msrestazure.azure_exceptions import CloudError

location = 'CentralUS'
name_prefix = 'cliadm'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

createRolloutTemplate = ".\CreateRollout.json"
failureCreateRolloutTemplate = ".\CreateRollout_FailureRollout.json"

parametersFileName = "Storage.Parameters.json"
invalidParametersFileName = "Storage_Invalid.Parameters.json"
templateFileName = "Storage.Template.json"
parametersCopyFileName = "Storage.Copy.Parameters.json"
templateCopyFileName = "Storage.Copy.Template.json"
rootPath = "ArtifactRoot\\" 

parametersArtifactSourceRelativePath = rootPath + parametersFileName
templateArtifactSourceRelativePath = rootPath + templateFileName
invalidParametersArtifactSourceRelativePath = rootPath + invalidParametersFileName
parametersCopyArtifactSourceRelativePath = rootPath + parametersCopyFileName
templateCopyArtifactSourceRelativePath = rootPath + templateCopyFileName

class DeploymentManagerTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix=name_prefix)
    @StorageAccountPreparer(name_prefix=name_prefix, location='centralus')
    def test_deploymentmanager_scenario(self, resource_group, storage_account):

        subscription_id = self.get_subscription_id()
        artifact_source_name = resource_group + "ArtifactSource"
        updated_artifact_source_name = resource_group + "ArtifactSourceUpdated"

        self.kwargs = {
            'provider_name': "Microsoft.DeploymentManager",
        }
        location = self.cmd('az provider show -n {provider_name}').get_output_in_json()['resourceTypes'][0]['locations'][0]

        self.set_managed_identity(subscription_id, resource_group)

        artifact_source_id = self.new_artifact_source(
            resource_group, 
            storage_account, 
            artifact_source_name, 
            location, 
            True)

        self.test_service_topology(
            subscription_id,
            resource_group,
            location,
            artifact_source_id,
            updated_artifact_source_name,
            storage_account)

        delete_artifact_source(resource_group, artifact_source_name)
        delete_artifact_source(resource_group, updated_artifact_source_name)

    
    def test_service_topology(
        self, 
        subscription_id, 
        resource_group_name, 
        location, 
        artifact_source_id, 
        updated_artifact_source_name, 
        storage_account_name):

        topology_name = resource_group_name + "ServiceTopology"

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': topology_name,
            'as_id': artifact_source_id,
        }

        self.cmd('az deploymentmanager service-topology create -g {rg} -n {st_name} -l {location} --artifact-source-id {as_id}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies'),
            self.check('name', topology_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('artifact_source_id', artifact_source_id)])

        service_topology_id = self.cmd('az deploymentmanager service-topology show -g {rg} -n {st_name}').get_output_in_json()['id']
        
        self.test_services(
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

        self.cmd('az deploymentmanager service-topology update -g {rg} -n {st_name} --artifact-source-id {as_id}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies'),
            self.check('name', topology_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('artifact_source_id', updated_artifact_source_id)])

        self.cmd('az deploymentmanager service-topology delete -g {rg} -n {st_name}')
        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager service-topology show -n {st_name} -g {rg}')

    def test_services(
        self,
        resource_group_name,
        location,
        artifact_source_id,
        service_topology_id,
        service_topology_name,
        subscription_id):

        service_name = resource_group_name + "Service"
        
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            't_l': location,
            't_sub_id': subscription_id
        }

        self.cmd('az deploymentmanager service create -g {rg} --service-topology-name {st_name} -n {s_name} -l {location} --target-location {t_l} --target-subscription-id {t_sub_id}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies/services'),
            self.check('name', service_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('targetSubscriptionId', subscription_id),
            self.check('targetLocation', location)])
        
        self.test_service_units(
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
            't_l': location,
            't_sub_id': updated_target_subscription_id
        }

        self.cmd('az deploymentmanager service update -g {rg} --service-topology-name {st_name} -n {s_name} --target-subscription-id {t_sub_id}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies/services'),
            self.check('name', service_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('targetSubscriptionId', updated_target_subscription_id)])

        self.cmd('az deploymentmanager service delete -g {rg} --service-topology-name {st_name} -n {s_name}')
        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager service show --service-topology-name {st_name} -n {s_name}')

    def test_service_units(
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
            'd_mode':deployment_mode ,
            'p_path': parametersFileName,
            't_path': templateFileName 
        }

        self.cmd('az deploymentmanager service-unit create -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name} -l {location} --target-resource-group {rg} --deployment-mode {d_mode} --parameters-artifact-source-relative-path {p_path} --template-artifact-source-relative-path {t_path}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies/services/serviceUnits'),
            self.check('name', service_unit_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('artifacts.parametersArtifactSourceRelativePath', parametersFileName),
            self.check('artifacts.templateArtifactSourceRelativePath', templateFileName),
            self.check('deploymentMode', deployment_mode),
            self.check('targetResourceGroup', resource_group_name)])

        service_unit_id = self.cmd('az deploymentmanager service show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}').get_output_in_json()['id']

        # Create a service unit that is invalid to test rollout failure operations
        invalid_service_unit_name = resource_group_name + "InvalidServiceUnit"
        
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': invalid_service_unit_name,
            'd_mode':deployment_mode ,
            'p_path': invalidParametersFileName,
            't_path': templateFileName 
        }

        self.cmd('az deploymentmanager service-unit create -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name} -l {location} --target-resource-group {rg} --deployment-mode {d_mode} --parameters-artifact-source-relative-path {p_path} --template-artifact-source-relative-path {t_path}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies/services/serviceUnits'),
            self.check('name', invalid_service_unit_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('artifacts.parametersArtifactSourceRelativePath', invalidParametersFileName),
            self.check('artifacts.templateArtifactSourceRelativePath', templateFileName),
            self.check('deploymentMode', deployment_mode),
            self.check('targetResourceGroup', resource_group_name)])

        invalid_service_unit_id = self.cmd('az deploymentmanager service show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}').get_output_in_json()['id']
        
        self.test_steps(
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
            'p_path': parametersFileName,
            't_path': templateFileName 
        }

        self.cmd('az deploymentmanager service-unit update -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name} --deployment-mode {d_mode}', checks[
            self.check('type', 'Microsoft.DeploymentManager/servicetopologies/services'),
            self.check('name', service_unit_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('deploymentMode', deployment_mode)])

        self.cmd('az deploymentmanager service-unit delete -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')
        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager service-unit show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')

        self.kwargs = {
            'rg': resource_group_name,
            'st_name': service_topology_name,
            's_name': service_name,
            'su_name': invalid_service_unit_name,
        }

        self.cmd('az deploymentmanager service-unit delete -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')
        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager service-unit show -g {rg} --service-topology-name {st_name} --service-name {s_name} -n {su_name}')

    def test_steps(
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

        self.cmd('az deploymentmanager step create -g {rg} -l {location} -n {step_name} --duration {duration}', checks[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('duration', duration)])

        step_id = self.cmd('az deploymentmanager step create -g {rg} -n {step_name}').get_output_in_json()['id']

        self.test_rollouts(
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

        self.cmd('az deploymentmanager step update -g {rg} -n {step_name} --duration {duration}', checks[
            self.check('type', 'Microsoft.DeploymentManager/steps'),
            self.check('name', step_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('duration', updated_duration)])

        self.cmd('az deploymentmanager step delete -g {rg} -l {location} -n {step_name}')
        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager step show -g {rg} -n {step_name}')

    def test_rollouts(
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
            createRolloutTemplate
        )

        self.replace_rollout_placeholders(
            failed_rollout_name,
            service_topology_id,
            artifact_source_id,
            step_id,
            invalid_service_unit_id,
            failureCreateRolloutTemplate 
        )
        
        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            't_path': createRolloutTemplate,
            'invalid_t_path': failureCreateRolloutTemplate,
            'rollout_name': rollout_name,
            'failed_rollout_name': failed_rollout_name 
        }

        self.cmd('az deployment create -g {rg} -l {location} --template-file {t_path}', checks[
            self.check('type', 'Microsoft.DeploymentManager/deployments'),
            self.check('provisioningState', 'Succeeded')])

        self.cmd('az deploymentmanager rollout show -g {rg} -n {rollout_name}', checks[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('status', 'Running'),
            self.check('totalRetryAttempts', '0'),
            self.check('operationInfo.retryAttempt', '0'),
            self.check('artifactSourceId', artifact_source_id),
            self.check('targetServiceTopologyId', service_topology_id)])

        self.cmd('az deploymentmanager rollout stop -g {rg} -n {rollout_name} --yes', checks[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('status', 'Canceling')])

        while True:
            self.test_sleep(120)  
            rollout = self.cmd('az deploymentmanager rollout show -g {rg} -n {rollout_name}').get_output_in_json()
            if (rollout['status'] != 'Canceling'):
                break

        self.assertEqual('Canceled', rollout['status'])

        self.cmd('az deployment create -g {rg} -l {location} --template-file {invalid_t_path}', checks[
            self.check('type', 'Microsoft.DeploymentManager/deployments'),
            self.check('provisioningState', 'Succeeded')])

        self.cmd('az deploymentmanager rollout show -g {rg} -n {failed_rollout_name}', checks[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('status', 'Running'),
            self.check('totalRetryAttempts', '0'),
            self.check('operationInfo.retryAttempt', '0'),
            self.check('artifactSourceId', artifact_source_id),
            self.check('targetServiceTopologyId', service_topology_id)])

        # Now validate that the rollout expected to fail has failed.
        while True:
            self.test_sleep(120)  
            rollout = self.cmd('az deploymentmanager rollout show -g {rg} -n {failed_rollout_name}').get_output_in_json()
            if (rollout['status'] != 'Running'):
                break

        self.assertEqual('Failed', rollout['status'])

        self.cmd('az deploymentmanager rollout restart -g {rg} -n {failed_rollout_name} --skip-succeeded True --yes', checks[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('operationInfo.retryAttempt', '1'),
            self.check('operationInfo.skipSucceededOnRetry', True),
            self.check('status', 'Running')])

        self.cmd('az deploymentmanager rollout stop -g {rg} -n {failed_rollout_name} --yes', checks[
            self.check('type', 'Microsoft.DeploymentManager/rollouts'),
            self.check('operationInfo.retryAttempt', '1'),
            self.check('operationInfo.skipSucceededOnRetry', True),
            self.check('status', 'Canceling')])

        while True:
            self.test_sleep(120)  
            rollout = self.cmd('az deploymentmanager rollout show -g {rg} -n {failed_rollout_name}').get_output_in_json()
            if (rollout['status'] != 'Canceling'):
                break

        self.cmd('az deploymentmanager rollout delete -g {rg} -n {failed_rollout_name}')
        self.cmd('az deploymentmanager rollout delete -g {rg} -n {rollout_name}')

        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager rollout show -g {rg} -n {failed_rollout_name}')
        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager rollout show -g {rg} -n {rollout_name}')

    def set_managed_identity(self, subscription_id, resource_group_name):

        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            identity_name = resource_group_name + "Identity"
             
            self.kwargs = {
                'rg': resource_group_name,
                'name': identity_name,
            }
            identity = self.cmd('az identity create -n {name} -g {rg}').get_output_in_json()
            identityId = identity['id']

            self.test_sleep(120)  

            self.kwargs = {
                'rg': resource_group_name,
                'principalId': identity['principalId'],
                'role': "Contributor",
                'scope': "/subscriptions/{0}".format(subscription_id),
            }

            roleAssignment = self.cmd('az role assignment create -assignee {principalId} -role {role} --scope {scope}').get_output_in_json()

            self.test_sleep(30)

            self.replace_string("__USER_ASSIGNED_IDENTITY__", identityId, createRolloutTemplate)
            self.replace_string("__USER_ASSIGNED_IDENTITY__", identityId, failureCreateRolloutTemplate)

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

        sas = self.get_sas_for_artifacts_container(
            resource_group_name, 
            storage_account_name, 
            container_name,
            artifact_root,
            setup_container)

        self.kwargs = {
            'rg': resource_group_name,
            'location': location,
            'as_name': artifact_source_name,
            'sas': sas,
            'artifactroot': artifact_root,
        }

        self.cmd('az deploymentmanager artifact-source create -g {rg} -n {as_name} -l {location} --sas-uri {sas} --artifact-root {artifactroot}', checks[
            self.check('type', 'Microsoft.DeploymentManager/artifactSources'),
            self.check('name', artifact_source_name),
            self.check('provisioningState', 'Succeeded'),
            self.check('artifactRoot', artifact_root),
            self.check('authentication.type', 'Sas'),
            self.check('sourceType', 'AzureStorage'),
        ])

        return self.cmd('az deploymentmanager artifact-source show -g {rg} -n {as_name}').get_output_in_json()['id']

    def get_sas_for_artifacts_container(
        self,
        resource_group_name,
        storage_account_name,
        storage_container_name,
        artifact_root,
        setup_container
    ):
        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            if setup_container:
                self.setup_artifacts_container(storage_account_name, storage_container_name) 

            sas_key = self.create_sas_key_for_container(storage_account_name, storage_container_name)

        return "dummysasforcontainer"

    def create_sas_key_for_container(self, storage_account_name, container_name):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        self.kwargs = {
            'account': storage_account_name,
            'container': container_name,
            'expiry': expiry
        }

        sas = self.cmd('storage container generate-sas -n {container} --account-name {account} --https-only '
                    '--permissions rl --expiry {expiry} -otsv').output.strip()
        
        return sas

    def setup_artifacts_container(self, resource_group_name, storage_account_name, container_name):
        		
        stgAcctForTemplate = resource_group_name + "stgtemplate"
        storageAcountReplacementSymbol = "__STORAGEACCOUNTNAME__"

        self.replace_string(storageAcountReplacementSymbol, stgAcctForTemplate, parametersArtifactSourceRelativePath)
        self.replace_string(storageAcountReplacementSymbol, stgAcctForTemplate, templateArtifactSourceRelativePath)
        self.replace_string(storageAcountReplacementSymbol, stgAcctForTemplate, parametersCopyArtifactSourceRelativePath)
        self.replace_string(storageAcountReplacementSymbol, stgAcctForTemplate, templateCopyArtifactSourceRelativePath)

        storage_account_info = self.get_stg_account_info(resource_group_name, storage_account_name)
        storage_container = self.create_container(storage_account_info)

        self.upload_blob(storage_account_info, storage_container, parametersArtifactSourceRelativePath)
        self.upload_blob(storage_account_info, storage_container, parametersCopyArtifactSourceRelativePath)
        self.upload_blob(storage_account_info, storage_container, templateArtifactSourceRelativePath)
        self.upload_blob(storage_account_info, storage_container, templateCopyArtifactSourceRelativePath)
        self.upload_blob(storage_account_info, storage_container, invalidParametersArtifactSourceRelativePath)

    def delete_artifact_source(self, resource_group_name, artifact_source_name):
        self.kwargs = {
            'rg': resource_group_name,
            'name': artifact_source_name,
        }
        self.cmd('az deploymentmanager artifact-source delete -n {name} -g {rg}')

        with self.assertRaisesRegexp(CloudError, 'not found'):
            self.cmd('az deploymentmanager artifact-source show -n {name} -g {rg}')

    def upload_blob(self, storage_account_info, storage_container_info, file_path):
        # blobPath = os.path.join(TEST_DIR, file_path)
        self.storage_cmd('storage blob upload -c {} -n src -f "{}" -t page', storage_account_info,
                    storage_container_info, parametersArtifactSourceRelativePath)

    def get_stg_account_key(self, group, name):
        if self.get_current_profile() == '2017-03-09-profile':
            template = 'storage account keys list -n {} -g {} --query "key1" -otsv'
        else:
            template = 'storage account keys list -n {} -g {} --query "[0].value" -otsv'

        return self.cmd(template.format(name, group)).output

    def get_stg_account_info(self, group, name):
        """Returns the storage account name and key in a tuple"""
        return name, self.get_account_key(group, name)

    def create_container(self, account_info, container_name):
        self.storage_cmd('storage container create -n {}', account_info, container_name)
        return container_name

    def storage_cmd(self, cmd, account_info, *args):
        cmd = cmd.format(*args)
        cmd = '{} --account-name {} --account-key {}'.format(cmd, *account_info)
        return self.cmd(cmd)

    def replace_string(self, replacement_symbol, replacement_value, filePath):
        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            with fileinput.FileInput(filePath, inplace=True) as file:
                for line in file:
                    print(line.replace(replacement_symbol, replacement_value), end='')

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

    def test_sleep(self, duration):
        is_playback = os.path.exists(self.recording_file)
        if not is_playback:
            time.sleep(duration)