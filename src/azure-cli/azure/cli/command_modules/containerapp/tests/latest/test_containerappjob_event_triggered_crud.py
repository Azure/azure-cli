# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, StorageAccountPreparer)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

from azext_containerapp.tests.latest.common import TEST_LOCATION
from .utils import create_containerapp_env

class ContainerAppJobsCRUDOperationsTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    # test for CRUD operations on Container App Job resource with trigger type as event
    def test_containerapp_eventjob_crudoperations_e2e(self, resource_group):
        import requests
        
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        job = self.create_random_name(prefix='job1', length=24)

        create_containerapp_env(self, env, resource_group)

        # create a container app environment for a Container App Job resource
        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)            
        ])

        ## test for CRUD operations on Container App Job resource with trigger type as event
        # create a Container App Job resource with trigger type as event
        self.cmd("az containerapp job create --name {} --resource-group {} --environment {} --trigger-type 'Event' --replica-timeout 60 --replica-retry-limit 1 --replica-completion-count 1 --parallelism 1 --min-executions 0 --max-executions 10 --polling-interval 60 --scale-rule-name 'queue' --scale-rule-type 'azure-queue' --scale-rule-metadata 'accountName=containerappextension' 'queueName=testeventdrivenjobs' 'queueLength=1' 'connectionFromEnv=AZURE_STORAGE_CONNECTION_STRING' --scale-rule-auth 'connection=connection-string-secret' --image 'mcr.microsoft.com/k8se/quickstart-jobs:latest' --cpu '0.5' --memory '1Gi' --secrets 'connection-string-secret=testConnString' --env-vars 'AZURE_STORAGE_QUEUE_NAME=testeventdrivenjobs' 'AZURE_STORAGE_CONNECTION_STRING=secretref:connection-string-secret'".format(job, resource_group, env))

        # verify the container app job resource
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 60),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 1),
            JMESPathCheck('properties.configuration.triggerType', "event", case_sensitive=False),
            JMESPathCheck('properties.configuration.eventTriggerConfig.scale.maxExecutions', 10),
        ])

        # get list of Container App Jobs
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 1)

        # update the Container App Job resource
        self.cmd("az containerapp job update --resource-group {} --name {} --replica-timeout 300 --replica-retry-limit 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --max-executions 9 --cpu '0.5' --memory '1.0Gi'".format(resource_group, job))

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

        # delete the Container App Job resource
        self.cmd("az containerapp job delete --resource-group {} --name {} --yes".format(resource_group, job))

        # verify the Container App Job resource is deleted
        jobs_list = self.cmd("az containerapp job list --resource-group {}".format(resource_group)).get_output_in_json()
        self.assertTrue(len(jobs_list) == 0)