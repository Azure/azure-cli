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
    def test_containerapp_job_executionstest_e2e(self, resource_group):
        import requests
        
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        job = self.create_random_name(prefix='job2', length=24)

        create_containerapp_env(self, env, resource_group)

        # create a container app environment for a Container App Job resource
        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)            
        ])

        # create a Container App Job resource
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 1 --trigger-type manual --replica-completion-count 1 --parallelism 1 --image mcr.microsoft.com/k8se/quickstart:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job, env))

        # wait for 60s for the job to be provisioned
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # start the job execution
        execution = self.cmd("az containerapp job start --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()
        if "id" in execution:
            # check if the job execution id is in the response
            self.assertEqual(job in execution['id'], True)
        if "name" in execution:
            # check if the job execution name is in the response
            self.assertEqual(job in execution['name'], True)

        # get list of all executions for the job
        executionList = self.cmd("az containerapp job execution list --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()
        self.assertTrue(len(executionList) == 1)
        
        # get single execution for the job
        singleExecution = self.cmd("az containerapp job execution show --resource-group {} --name {} --job-execution-name {}".format(resource_group, job, execution['name'])).get_output_in_json()
        self.assertEqual(job in singleExecution['name'], True)
        
        # start a job execution and stop it
        execution = self.cmd("az containerapp job start --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()
        if "id" in execution:
            # check if the job execution id is in the response
            self.assertEqual(job in execution['id'], True)
        if "name" in execution:
            # check if the job execution name is in the response
            self.assertEqual(job in execution['name'], True)

        # stop the most recently started execution
        self.cmd("az containerapp job stop --resource-group {} --name {} --job-execution-name {}".format(resource_group, job, execution['name'])).get_output_in_json()
        
        # get stopped execution for the job and check status
        singleExecution = self.cmd("az containerapp job execution show --resource-group {} --name {} --job-execution-name {}".format(resource_group, job, execution['name'])).get_output_in_json()
        self.assertEqual(job in singleExecution['name'], True)
        self.assertEqual(singleExecution['properties']['status'], "Stopped")

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    def test_containerapp_job_custom_executionstest_e2e(self, resource_group):
        import requests

        TEST_LOCATION = "northcentralusstage"
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        job = self.create_random_name(prefix='job3', length=24)

        create_containerapp_env(self, env, resource_group)

        # create a container app environment for a Container App Job resource
        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)            
        ])

        # create a Container App Job resource
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 1 --trigger-type manual --replica-completion-count 1 --parallelism 1 --image mcr.microsoft.com/k8se/quickstart:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job, env))

        # wait for 60s for the job to be provisioned
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # start an execution with custom container information
        customContainerImage = "mcr.microsoft.com/k8se/quickstart:latest"
        customContainerName = "job3-custom-exec"
        execution = self.cmd("az containerapp job start --resource-group {} --name {} --image {} --container-name {} --cpu '0.5' --memory '1Gi'".format(resource_group, job, customContainerImage, customContainerName)).get_output_in_json()
        if "id" in execution:
            # check if the job execution id is in the response
            self.assertEqual(job in execution['id'], True)
        if "name" in execution:
            # check if the job execution name is in the response
            self.assertEqual(job in execution['name'], True)

        # get the execution and check if the custom container information is present
        self.cmd("az containerapp job execution show --resource-group {} --name {} --job-execution-name {}".format(resource_group, job, execution['name']), checks=[
            JMESPathCheck('properties.template.containers[0].name', customContainerName),
            JMESPathCheck('properties.template.containers[0].image', customContainerImage),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi')
        ])

        # yaml file to start a job execution
        containerappjobexecution_yaml_text = f"""
            containers:
                - env:
                    - name: MY_ENV_VAR
                      value: hello
                  image: mcr.microsoft.com/k8se/quickstart-jobs:latest
                  name: test-yaml-execution
                  resources:
                    cpu: 0.5
                    memory: 1Gi
            initContainers:
                - command:
                    - /bin/sh
                    - -c
                    - sleep 10
                  image: k8seteste2e.azurecr.io/e2e-apps/kuar:green
                  name: simple-sleep-container
                  resources:
                    cpu: "0.25"
                    memory: 0.5Gi
            """
        containerappjob_file_name = f"{self._testMethodName}_containerappjob.yml"
        write_test_file(containerappjob_file_name, containerappjobexecution_yaml_text)

        # start job execution with yaml file
        execution = self.cmd("az containerapp job start --resource-group {} --name {} --yaml {}".format(resource_group, job, containerappjob_file_name)).get_output_in_json()
        self.assertEqual(job in execution['id'], True)
        self.assertEqual(job in execution['name'], True)            

        # get the execution and check if the custom container information is present
        self.cmd("az containerapp job execution show --resource-group {} --name {} --job-execution-name {}".format(resource_group, job, execution['name']), checks=[
            JMESPathCheck('properties.template.containers[0].name', "test-yaml-execution"),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', '0.5'),
            JMESPathCheck('properties.template.containers[0].resources.memory', '1Gi'),
            JMESPathCheck('properties.template.initContainers[0].name', "simple-sleep-container"),
            JMESPathCheck('properties.template.initContainers[0].image', "k8seteste2e.azurecr.io/e2e-apps/kuar:green"),
            JMESPathCheck('properties.template.initContainers[0].resources.cpu', '0.25'),
            JMESPathCheck('properties.template.initContainers[0].resources.memory', '0.5Gi')
        ])
        clean_up_test_file(containerappjob_file_name)