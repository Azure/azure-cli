# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, LogAnalyticsWorkspacePreparer)

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION
from .utils import create_containerapp_env

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppJobsCRUDOperationsTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    @LogAnalyticsWorkspacePreparer(location="eastus")
    # test for CRUD operations on Container App Job resource with trigger type as manual
    def test_containerapp_manualjob_crudoperations_e2e(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        import requests
        
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        job = self.create_random_name(prefix='job1', length=24)

        create_containerapp_env(self, env, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)

        # create a container app environment for a Container App Job resource
        self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)            
        ])

        ## test for CRUD operations on Container App Job resource with trigger type as manual
        # create a Container App Job resource with trigger type as manual
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 2 --trigger-type manual --parallelism 1 --replica-completion-count 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job, env))

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
        self.cmd("az containerapp job update --resource-group {} --name {} --replica-timeout 300 --replica-retry-limit 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.5' --memory '1.0Gi'".format(resource_group, job))

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
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 2 --trigger-type schedule --parallelism 1 --replica-completion-count 1 --cron-expression '*/5 * * * *' --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job2, env))

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
        self.cmd("az containerapp job update --resource-group {} --name {} --replica-timeout 300 --replica-retry-limit 1 --cron-expression '*/10 * * * *' --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.5' --memory '1.0Gi'".format(resource_group, job2))

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
    @LogAnalyticsWorkspacePreparer(location="eastus")
    def test_containerapp_manualjob_private_registry_port(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='env', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"

        create_containerapp_env(self, env, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')
        password = self.cmd(f'acr credential show -n {acr} --query passwords[0].value').get_output_in_json()

        app = self.create_random_name(prefix='aca1', length=24)
        image_name = f"{acr}.azurecr.io:443/k8se/quickstart:latest"

        self.cmd(
            f"containerapp job create -g {resource_group} -n {app} --image {image_name} --environment {env} --registry-server {acr}.azurecr.io:443 --registry-username {acr} --registry-password {password} --replica-timeout 200 --replica-retry-limit 2 --trigger-type schedule --parallelism 1 --replica-completion-count 1 --cron-expression '*/10 * * * *' ")

        self.cmd(f'containerapp job show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.registries[0].server", f"{acr}.azurecr.io:443"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
            JMESPathCheck("properties.configuration.secrets[0].name", f"{acr}azurecrio-443-{acr}")
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="westeurope")
    @LogAnalyticsWorkspacePreparer(location="eastus")
    def test_containerapp_manualjob_registry_acr_look_up_credentical(self, resource_group, laworkspace_customer_id, laworkspace_shared_key):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='aca', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        image_source = "mcr.microsoft.com/k8se/quickstart:latest"

        create_containerapp_env(self, env, resource_group, logs_workspace=laworkspace_customer_id, logs_workspace_shared_key=laworkspace_shared_key)

        self.cmd(f'acr create --sku basic -n {acr} -g {resource_group} --admin-enabled')
        self.cmd(f'acr import -n {acr} --source {image_source}')

        app = self.create_random_name(prefix='aca1', length=24)
        image_name = f"{acr}.azurecr.io/k8se/quickstart:latest"

        self.cmd(
            f"containerapp job create -g {resource_group} -n {app} --image {image_name} --environment {env} --registry-server {acr}.azurecr.io --replica-timeout 200 --replica-retry-limit 2 --trigger-type schedule --parallelism 1 --replica-completion-count 1 --cron-expression '*/10 * * * *' ")

        self.cmd(f'containerapp job show -g {resource_group} -n {app}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
            JMESPathCheck("properties.configuration.registries[0].server", f"{acr}.azurecr.io"),
            JMESPathCheck("properties.template.containers[0].image", image_name),
            JMESPathCheck("properties.configuration.secrets[0].name", f"{acr}azurecrio-{acr}")
        ])
