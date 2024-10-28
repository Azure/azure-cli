# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.mgmt.core.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION
from .utils import prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppJobsEventTriggeredCRUDOperationsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    # test for CRUD operations on Container App Job resource with trigger type as event
    def test_containerapp_eventjob_crudoperations_e2e(self, resource_group):
        import requests
        
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')
        job = self.create_random_name(prefix='job1', length=24)

        # create a container app environment for a Container App Job resource
        self.cmd('containerapp env show -n {} -g {}'.format(env_name, env_rg), checks=[
            JMESPathCheck('name', env_name)
        ])

        ## test for CRUD operations on Container App Job resource with trigger type as event
        # create a Container App Job resource with trigger type as event
        self.cmd("az containerapp job create --name {} --resource-group {} --environment {} --trigger-type 'Event' --replica-timeout 60 --replica-retry-limit 1 --replica-completion-count 1 --parallelism 1 --min-executions 0 --max-executions 10 --polling-interval 60 --scale-rule-name 'queue' --scale-rule-type 'azure-queue' --scale-rule-metadata 'accountName=containerappextension' 'queueName=testeventdrivenjobs' 'queueLength=1' 'connectionFromEnv=AZURE_STORAGE_CONNECTION_STRING' --scale-rule-auth 'connection=connection-string-secret' --image 'mcr.microsoft.com/k8se/quickstart-jobs:latest' --cpu '0.5' --memory '1Gi' --secrets 'connection-string-secret=testConnString' --env-vars 'AZURE_STORAGE_QUEUE_NAME=testeventdrivenjobs' 'AZURE_STORAGE_CONNECTION_STRING=secretref:connection-string-secret'".format(job, resource_group, env_id), checks=[JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.queueLength', "")])

        # verify the container app job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 60),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "event", case_sensitive=False),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 10),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.queueLength', "1"),
        ])

        # get list of Container App Jobs
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 1)

        # update the Container App Job resource
        self.cmd("az containerapp job update --resource-group {} --name {} --replica-timeout 300 --replica-retry-limit 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --max-executions 9 --cpu '0.5' --memory '1.0Gi'".format(resource_group, job), checks=[
            JMESPathCheck('properties.provisioningState', "Succeeded"),
            JMESPathCheck('properties.configuration.replicaTimeout', 300),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "event", case_sensitive=False),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 9),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

        # verify the updated Container App Job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 300),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "event", case_sensitive=False),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 9),
            JMESPathCheck('properties.template.containers[0].image', "mcr.microsoft.com/k8se/quickstart-jobs:latest"),
            JMESPathCheck('properties.template.containers[0].resources.cpu', "0.5"),
            JMESPathCheck('properties.template.containers[0].resources.memory', "1Gi"),
        ])

        # wait for 60s for the job to be provisioned
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # update scale rules for event triggered job
        # scenario 1: update existing scale rule
        self.cmd("az containerapp job update --resource-group {} --name {} --scale-rule-name 'queue' --scale-rule-type 'azure-queue' --scale-rule-metadata 'accountName=containerappextension' 'queueName=testeventdrivenjobs' 'queueLength=2' 'connectionFromEnv=AZURE_STORAGE_CONNECTION_STRING' --scale-rule-auth 'connection=connection-string-secret'".format(resource_group, job), checks=[
            JMESPathCheck('properties.provisioningState', "Succeeded"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.queueLength', ""), # The transform_sensitive_values will remove the value for update command
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.pollingInterval', 60),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.minExecutions', 0),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 9),
        ])

        # verify the updated Container App Job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[0].metadata.queueLength', "2"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.pollingInterval', 60),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.minExecutions', 0),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 9),
        ])

        # check length of scale rules
        scale_rules_length = len(self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['configuration']['eventTriggerConfig']['scale']['rules'])
        self.assertTrue(scale_rules_length == 1)

        # wait for 60s for the job to be provisioned
        jobProvisioning = True
        timeout = time.time() + 60*1   # 1 minutes from now
        while(jobProvisioning):
            jobProvisioning = self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['provisioningState'] != "Succeeded"
            if(time.time() > timeout):
                break

        # scenario 2: add new scale rule
        self.cmd("az containerapp job update --resource-group {} --name {} --min-executions 1 --max-executions 5 --polling-interval 30 --scale-rule-name 'queue2' --scale-rule-type 'azure-queue' --scale-rule-metadata 'accountName=containerappextension' 'queueName=testeventdrivenjobs' 'queueLength=3' 'connectionFromEnv=AZURE_STORAGE_CONNECTION_STRING' --scale-rule-auth 'connection=connection-string-secret'".format(resource_group, job), checks=[
            JMESPathCheck('properties.provisioningState', "Succeeded"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[1].metadata.queueLength', ""), # The transform_sensitive_values will remove the value for update command
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.pollingInterval', 30),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.minExecutions', 1),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 5),
        ])

        # verify the updated Container App Job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.rules[1].metadata.queueLength', "3"),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.pollingInterval', 30),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.minExecutions', 1),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 5),
        ])

        # check length of scale rules
        scale_rules_length = len(self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job)).get_output_in_json()['properties']['configuration']['eventTriggerConfig']['scale']['rules'])
        self.assertTrue(scale_rules_length == 2)

        # delete the Container App Job resource
        self.cmd("az containerapp job delete --resource-group {} --name {} --yes".format(resource_group, job))

        # verify the Container App Job resource is deleted
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 0)
