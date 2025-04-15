# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.mgmt.core.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, LogAnalyticsWorkspacePreparer)

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION, write_test_file, \
    clean_up_test_file
from .utils import create_containerapp_env, prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppJobsCRUDOperationsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    # test for CRUD operations on Container App Job resource with trigger type as manual
    def test_containerapp_manualjob_crudoperations_e2e(self, resource_group):
        import requests
        
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')
        job = self.create_random_name(prefix='job1', length=24)

        ## test for CRUD operations on Container App Job resource with trigger type as manual
        # create a Container App Job resource with trigger type as manual
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 2 --trigger-type manual --parallelism 1 --replica-completion-count 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job, env_id))

        # verify the container app job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 200),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 2),
            JMESPathCheck('properties.configuration.triggerType', "manual", case_sensitive=False),
        ])

        # get list of Container App Jobs
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 1)

        # update the Container App Job resource
        self.cmd("az containerapp job update --resource-group {} --name {} --replica-timeout 300 --replica-retry-limit 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.5' --memory '1.0Gi'".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.provisioningState', "Succeeded"),
            JMESPathCheck('properties.configuration.replicaTimeout', 300),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "manual", case_sensitive=False),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

        # verify the updated Container App Job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 300),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "manual", case_sensitive=False),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

        # delete the Container App Job resource
        self.cmd("az containerapp job delete --resource-group {} --name {} --yes".format(resource_group, job))

        # verify the Container App Job resource is deleted
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 0)
        
        ## test for CRUD operations on Container App Job resource with trigger type as schedule
        job2 = self.create_random_name(prefix='job2', length=24)

        # create a Container App Job resource with trigger type as schedule
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 2 --trigger-type schedule --parallelism 1 --replica-completion-count 1 --cron-expression '*/5 * * * *' --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job2, env_id))

        # verify the container app job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job2), checks=[
            JMESPathCheck('name', job2),
            JMESPathCheck('properties.configuration.replicaTimeout', 200),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 2),
            JMESPathCheck('properties.configuration.triggerType', "schedule", case_sensitive=False),
            JMESPathCheck('properties.configuration.scheduleTriggerConfig.cronExpression', "*/5 * * * *"),
        ])

        # get list of Container App Jobs
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 1)

        # update the Container App Job resource
        self.cmd("az containerapp job update --resource-group {} --name {} --replica-timeout 300 --replica-retry-limit 1 --cron-expression '*/10 * * * *' --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.5' --memory '1.0Gi'".format(resource_group, job2), checks=[
            JMESPathCheck('properties.provisioningState', "Succeeded"),
            JMESPathCheck('properties.configuration.replicaTimeout', 300),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "schedule", case_sensitive=False),
            JMESPathCheck('properties.configuration.scheduleTriggerConfig.cronExpression', "*/10 * * * *"),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

        # verify the updated Container App Job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job2), checks=[
            JMESPathCheck('name', job2),
            JMESPathCheck('properties.configuration.replicaTimeout', 300),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "schedule", case_sensitive=False),
            JMESPathCheck('properties.configuration.scheduleTriggerConfig.cronExpression', "*/10 * * * *"),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_manualjob_private_registry_port(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')
        password = self.cmd(f'acr credential show -n {acr} --query passwords[0].value').get_output_in_json()

        app = self.create_random_name(prefix='aca1', length=24)
        image_name = f"{acr}.azurecr.io:443/k8se/quickstart:latest"

        self.cmd(
            f"containerapp job create -g {resource_group} -n {app} --image {image_name} --environment {env_id} --registry-server {acr}.azurecr.io:443 --registry-username {acr} --registry-password {password} --replica-timeout 200 --replica-retry-limit 2 --trigger-type schedule --parallelism 1 --replica-completion-count 1 --cron-expression '*/10 * * * *' ")

        self.cmd(f'containerapp job show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.registries[0].server", f"{acr}.azurecr.io:443"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
            JMESPathCheck("properties.configuration.secrets[0].name", f"{acr}azurecrio-443-{acr}")
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    def test_containerapp_manualjob_registry_acr_look_up_credentical(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        app = self.create_random_name(prefix='aca', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')

        app = self.create_random_name(prefix='aca1', length=24)
        image_name = f"{acr}.azurecr.io/k8se/quickstart:latest"

        self.cmd(
            f"containerapp job create -g {resource_group} -n {app} --image {image_name} --environment {env_id} --registry-server {acr}.azurecr.io --replica-timeout 200 --replica-retry-limit 2 --trigger-type schedule --parallelism 1 --replica-completion-count 1 --cron-expression '*/10 * * * *' ")

        self.cmd(f'containerapp job show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.registries[0].server", f"{acr}.azurecr.io"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
            JMESPathCheck("properties.configuration.secrets[0].name", f"{acr}azurecrio-{acr}")
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    @LogAnalyticsWorkspacePreparer(location="eastus", get_shared_key=True)
    def test_containerappjob_create_with_environment_id(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env1 = self.create_random_name(prefix='env1', length=24)
        env2 = self.create_random_name(prefix='env2', length=24)
        job1 = self.create_random_name(prefix='yaml1', length=24)

        create_containerapp_env(self, env1, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)
        containerapp_env1 = self.cmd(
            'containerapp env show -g {} -n {}'.format(resource_group, env1)).get_output_in_json()

        create_containerapp_env(self, env2, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)
        containerapp_env2 = self.cmd(
            'containerapp env show -g {} -n {}'.format(resource_group, env2)).get_output_in_json()

        # the value in --yaml is used, warning for different value in --environmentId
        containerappjob_yaml_text = f"""
                    location: {TEST_LOCATION}
                    properties:
                        environmentId: {containerapp_env1["id"]}
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
                        workloadProfileName: null
                    """
        containerappjob_file_name = f"{self._testMethodName}_containerappjob.yml"

        write_test_file(containerappjob_file_name, containerappjob_yaml_text)
        self.cmd(
            f'containerapp job create -n {job1} -g {resource_group} --environment {env2} --yaml {containerappjob_file_name}',
            checks=[
                JMESPathCheck("properties.provisioningState", "Succeeded"),
                JMESPathCheck("properties.environmentId", containerapp_env1["id"]),
                JMESPathCheck("properties.configuration.triggerType", "Manual", case_sensitive=False),
                JMESPathCheck('properties.configuration.replicaTimeout', 100),
                JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
                JMESPathCheck('properties.template.containers[0].image',
                              "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
                JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
                JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
            ])

        self.cmd(f'containerapp job show -g {resource_group} -n {job1}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.environmentId", containerapp_env1["id"]),
            JMESPathCheck("properties.configuration.triggerType", "Manual", case_sensitive=False),
            JMESPathCheck('properties.configuration.replicaTimeout', 100),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

        # test container app job update with yaml
        containerappjob_yaml_text = f"""
                    location: {TEST_LOCATION}
                    properties:
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
                    """
        write_test_file(containerappjob_file_name, containerappjob_yaml_text)
        job2 = self.create_random_name(prefix='yaml2', length=24)
        self.cmd(
            f'containerapp job create -n {job2} -g {resource_group} --environment {env2} --yaml {containerappjob_file_name}',
            checks=[
                JMESPathCheck("properties.provisioningState", "Succeeded"),
                JMESPathCheck("properties.environmentId", containerapp_env2["id"]),
                JMESPathCheck("properties.configuration.triggerType", "Manual", case_sensitive=False),
                JMESPathCheck('properties.configuration.replicaTimeout', 200),
                JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
                JMESPathCheck('properties.template.containers[0].image',
                              "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
                JMESPathCheck('properties.template.containers[0].resources.cpu', "0.75"),
                JMESPathCheck('properties.template.containers[0].resources.memory', "1.5Gi"),
            ])

        self.cmd(f'containerapp job list -g {resource_group}', checks=[
            JMESPathCheck("length(@)", 2),
        ])
        clean_up_test_file(containerappjob_file_name)