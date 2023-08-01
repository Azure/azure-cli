# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, StorageAccountPreparer)
from azext_containerapp.tests.latest.common import (write_test_file, clean_up_test_file)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

from azext_containerapp.tests.latest.common import TEST_LOCATION
from .utils import create_containerapp_env

class ContainerAppJobsExecutionsTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    def test_containerappjob_create_with_yaml(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        job = self.create_random_name(prefix='yaml', length=24)
        storage = self.create_random_name(prefix='storage', length=24)
        share = self.create_random_name(prefix='share', length=24)

        self.cmd(
            f'az storage account create --resource-group {resource_group}  --name {storage} --location {TEST_LOCATION} --kind StorageV2 --sku Standard_LRS --enable-large-file-share --output none')
        self.cmd(
            f'az storage share-rm create --resource-group {resource_group}  --storage-account {storage} --name {share} --quota 1024 --enabled-protocols SMB --output none')

        create_containerapp_env(self, env, resource_group)
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        account_key = self.cmd(f'az storage account keys list -g {resource_group} -n {storage} --query "[0].value" '
                               '-otsv').output.strip()
        self.cmd(
            f'az containerapp env storage set -g {resource_group} -n {env} -a {storage} -k {account_key} -f {share} --storage-name {share} --access-mode ReadWrite')

        user_identity_name = self.create_random_name(prefix='containerapp-user', length=24)
        user_identity = self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name)).get_output_in_json()
        user_identity_id = user_identity['id']

        # test job create with yaml
        containerappjob_yaml_text = f"""
            location: {TEST_LOCATION}
            properties:
                environmentId: {containerapp_env["id"]}
                configuration:
                    dapr: null
                    eventTriggerConfig: null
                    manualTriggerConfig:
                        parallelism: 1
                        replicaCompletionCount: 1
                    registries: null
                    replicaRetryLimit: 1
                    replicaTimeout: 100
                    scheduleTriggerConfig: null
                    secrets: null
                    triggerType: Manual
                template:
                    containers:
                    - env:
                        - name: MY_ENV_VAR
                          value: hello
                      image: mcr.microsoft.com/k8se/quickstart-jobs:latest
                      name: anfranci-azclitest-acaj1
                      resources:
                        cpu: 0.5
                        ephemeralStorage: 1Gi
                        memory: 1Gi
                      volumeMounts:
                        - mountPath: /mnt/data
                          volumeName: azure-files-volume
                          subPath: sub
                    initContainers:
                    - command:
                        - /bin/sh
                        - -c
                        - sleep 150
                      image: k8seteste2e.azurecr.io/e2e-apps/kuar:green
                      name: simple-sleep-container
                      probes:
                      - type: liveness
                        httpGet:
                            path: "/health"
                            port: 8080
                            httpHeaders:
                                - name: "Custom-Header"
                                  value: "liveness probe"
                        initialDelaySeconds: 7
                        periodSeconds: 3
                        resources:
                            cpu: "0.25"
                            memory: 0.5Gi
                    volumes:
                    - name: azure-files-volume
                      storageType: AzureFile
                      storageName: {share}
                      mountOptions: uid=999,gid=999
                workloadProfileName: null
            identity:
              type: UserAssigned
              userAssignedIdentities:
                {user_identity_id}: {{}}
            """
        containerappjob_file_name = f"{self._testMethodName}_containerappjob.yml"

        write_test_file(containerappjob_file_name, containerappjob_yaml_text)
        self.cmd(f'containerapp job create -n {job} -g {resource_group} --environment {env} --yaml {containerappjob_file_name}')

        self.cmd(f'containerapp job show -g {resource_group} -n {job}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.triggerType", "Manual", case_sensitive=False),
            JMESPathCheck('properties.configuration.replicaTimeout', 100),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
            JMESPathCheck('identity.type', "UserAssigned"),
            JMESPathCheck('properties.template.volumes[0].storageType', 'AzureFile'),
            JMESPathCheck('properties.template.volumes[0].storageName', share),
            JMESPathCheck('properties.template.volumes[0].name', 'azure-files-volume'),
            JMESPathCheck('properties.template.volumes[0].mountOptions', 'uid=999,gid=999'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].subPath', 'sub'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].mountPath', '/mnt/data'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].volumeName', 'azure-files-volume')
        ])

        # wait for provisioning state of job to be succeeded before updating
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # test container app job update with yaml
        containerappjob_yaml_text = f"""
            location: {TEST_LOCATION}
            properties:
                environmentId: {containerapp_env["id"]}
                configuration:
                    dapr: null
                    eventTriggerConfig: null
                    manualTriggerConfig:
                        parallelism: 1
                        replicaCompletionCount: 1
                    registries: null
                    replicaRetryLimit: 1
                    replicaTimeout: 200
                    scheduleTriggerConfig: null
                    secrets: null
                    triggerType: Manual
                template:
                    containers:
                    - env:
                        - name: MY_ENV_VAR
                          value: hello
                      image: mcr.microsoft.com/k8se/quickstart-jobs:latest
                      name: anfranci-azclitest-acaj1
                      resources:
                        cpu: 0.75
                        ephemeralStorage: 1Gi
                        memory: 1.5Gi
                      volumeMounts:
                        - mountPath: /mnt/data
                          volumeName: azure-files-volume
                          subPath: sub2
                    initContainers:
                    - command:
                        - /bin/sh
                        - -c
                        - sleep 150
                      image: k8seteste2e.azurecr.io/e2e-apps/kuar:green
                      name: simple-sleep-container
                    probes:
                    - type: liveness
                      httpGet:
                        path: "/health"
                        port: 8080
                        httpHeaders:
                            - name: "Custom-Header"
                              value: "liveness probe"
                        initialDelaySeconds: 7
                        periodSeconds: 3
                        resources:
                            cpu: "0.25"
                            memory: 0.5Gi
                    volumes:
                    - name: azure-files-volume
                      storageType: AzureFile
                      storageName: {share}
                      mountOptions: uid=1000,gid=1000
            """
        write_test_file(containerappjob_file_name, containerappjob_yaml_text)

        self.cmd(f'containerapp job update -n {job} -g {resource_group} --yaml {containerappjob_file_name}')

        self.cmd(f'containerapp job show -g {resource_group} -n {job}', checks=[
            JMESPathCheck("properties.configuration.triggerType", "Manual", case_sensitive=False),
            JMESPathCheck('properties.configuration.replicaTimeout', 200),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.75"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1.5Gi"),
            JMESPathCheck('properties.template.volumes[0].storageType', 'AzureFile'),
            JMESPathCheck('properties.template.volumes[0].storageName', share),
            JMESPathCheck('properties.template.volumes[0].name', 'azure-files-volume'),
            JMESPathCheck('properties.template.volumes[0].mountOptions', 'uid=1000,gid=1000'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].subPath', 'sub2'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].mountPath', '/mnt/data'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].volumeName', 'azure-files-volume'),
        ])

        # wait for provisioning state of job to be succeeded before updating
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # test update for job with yaml not containing environmentId
        containerappjob_yaml_text = f"""
                            properties:
                              configuration:
                                replicaTimeout: 300
                            """
        write_test_file(containerappjob_file_name, containerappjob_yaml_text)

        self.cmd(f'containerapp job update -n {job} -g {resource_group} --yaml {containerappjob_file_name}')

        self.cmd(f'containerapp job show -g {resource_group} -n {job}', checks=[
            JMESPathCheck("properties.environmentId", containerapp_env["id"]),
            JMESPathCheck("properties.configuration.replicaTimeout", 300)
        ])
        clean_up_test_file(containerappjob_file_name)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    def test_containerappjob_eventtriggered_create_with_yaml(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        job = self.create_random_name(prefix='yaml', length=24)

        create_containerapp_env(self, env, resource_group)
        containerapp_env = self.cmd('containerapp env show -g {} -n {}'.format(resource_group, env)).get_output_in_json()

        user_identity_name = self.create_random_name(prefix='containerapp-user', length=24)
        user_identity = self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name)).get_output_in_json()
        user_identity_id = user_identity['id']

        # test job create with yaml
        containerappjob_yaml_text = f"""
            location: {TEST_LOCATION}
            properties:
                environmentId: {containerapp_env["id"]}
                configuration:
                    eventTriggerConfig:
                        replicaCompletionCount: 1
                        parallelism: 1
                        scale:
                            minExecutions: 0
                            maxExecutions: 10
                            rules:
                            - name: github-runner-test
                              type: github-runner
                              metadata:
                                github-runner: https://api.github.com
                                owner: test_org
                                runnerScope: repo
                                repos: test_repo
                                targetWorkflowQueueLength: "1"
                              auth:
                                - secretRef: personal-access-token
                                  triggerParameter: personalAccessToken
                    replicaRetryLimit: 1
                    replicaTimeout: 100
                    secrets:
                        - name: personal-access-token
                          value: test_personal_access_token
                    triggerType: Event
                template:
                    containers:
                    - env:
                        - name: ACCESS_TOKEN
                          secretRef: personal-access-token
                        - name: DISABLE_RUNNER_UPDATE
                          value: "true"
                        - name: RUNNER_SCOPE
                          value: repo
                        - name: ORG_NAME
                          value: test_org
                        - name: ORG_RUNNER
                          value: "false"
                        - name: RUNNER_WORKDIR
                          value: /tmp/runner
                        - name: REPO_URL
                          value: https://github.com/test_org/test_repo
                      image: mcr.microsoft.com/k8se/quickstart-jobs:latest
                      name: eventdriventjob
                      resources:
                        cpu: 0.5
                        ephemeralStorage: 1Gi
                        memory: 1Gi
                      volumeMounts:
                        - volumeName: workdir
                          mountPath: /tmp/github-runner-your-repo
                        - volumeName: dockersock
                          mountPath: /var/run/docker.sock
                    volumes:
                        - name: workdir
                          storageType: EmptyDir
                        - name: dockersock
                          storageType: EmptyDir
            identity:
              type: UserAssigned
              userAssignedIdentities:
                {user_identity_id}: {{}}
            """
        containerappjob_file_name = f"{self._testMethodName}_containerappjob.yml"

        write_test_file(containerappjob_file_name, containerappjob_yaml_text)
        self.cmd(f'containerapp job create -n {job} -g {resource_group} --environment {env} --yaml {containerappjob_file_name}')

        self.cmd(f'containerapp job show -g {resource_group} -n {job}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.triggerType", "Event", case_sensitive=False),
            JMESPathCheck('properties.configuration.replicaTimeout', 100),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.replicaCompletionCount', 1),
            JMESPathCheck('properties.configuration.eventTriggerConfig.parallelism', 1),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.minExecutions', 0),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 10),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].type', "github-runner"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.runnerScope', "repo"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].auth[0].secretRef', "personal-access-token"),
            JMESPathCheck('identity.type', "UserAssigned"),
        ])

        # wait for provisioning state of job to be succeeded before updating
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # test container app job update with yaml
        containerappjob_yaml_text = f"""
            location: {TEST_LOCATION}
            properties:
                environmentId: {containerapp_env["id"]}
                configuration:
                    eventTriggerConfig:
                        replicaCompletionCount: 2
                        parallelism: 2
                        scale:
                            minExecutions: 1
                            maxExecutions: 9
                            rules:
                            - name: github-runner-testv2
                              type: github-runner
                              metadata:
                                github-runner: https://api.github.com
                                owner: test_org_1
                                runnerScope: repo
                                repos: test_repo_1
                                targetWorkflowQueueLength: "1"
                              auth:
                                - secretRef: personal-access-token
                                  triggerParameter: personalAccessToken
                    replicaRetryLimit: 2
                    replicaTimeout: 200
                    secrets:
                        - name: personal-access-token
                          value: test_personal_access_token
                    triggerType: Event
            """
        write_test_file(containerappjob_file_name, containerappjob_yaml_text)

        self.cmd(f'containerapp job update -n {job} -g {resource_group} --yaml {containerappjob_file_name}')

        self.cmd(f'containerapp job show -g {resource_group} -n {job}', checks=[
            JMESPathCheck("properties.configuration.triggerType", "Event", case_sensitive=False),
            JMESPathCheck('properties.configuration.replicaTimeout', 200),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 2),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.replicaCompletionCount', 2),
            JMESPathCheck('properties.configuration.eventTriggerConfig.parallelism', 2),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.minExecutions', 1),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 9),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].name', "github-runner-testv2"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.runnerScope', "repo"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.owner', "test_org_1"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].auth[0].secretRef', "personal-access-token"),
        ])
        clean_up_test_file(containerappjob_file_name)