# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.mgmt.core.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, LogAnalyticsWorkspacePreparer)

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION
from .utils import prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppJobsSecretsOperationsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    # test for CRUD operations on Container App Job resource with trigger type as manual
    def test_containerapp_manualjob_withsecret_crudoperations_e2e(self, resource_group):

        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        job = self.create_random_name(prefix='job1', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)
        env_rg = parse_resource_id(env_id).get('resource_group')
        env_name = parse_resource_id(env_id).get('name')

        # create a container app environment for a Container App Job resource
        self.cmd('containerapp env show -n {} -g {}'.format(env_name, env_rg), checks=[
            JMESPathCheck('name', env_name)
        ])

        ## test for CRUD operations on Container App Job resource with trigger type as manual
        # create a Container App Job resource with trigger type as manual
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --secrets 'testsecret=testsecretvalue' --replica-timeout 200 --replica-retry-limit 2 --trigger-type manual --parallelism 1 --replica-completion-count 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi'".format(resource_group, job, env_id))

        # verify the container app job resource contains the secret
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 200),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 2),
            JMESPathCheck('properties.configuration.triggerType', "manual", case_sensitive=False),
            JMESPathCheck('properties.configuration.secrets[0].name', "testsecret"),
        ])

        # get list of Container App Jobs secrets
        job_secret_list = self.cmd("az containerapp job secret list --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('[0].name', "testsecret"),
            ]).get_output_in_json()
        self.assertTrue(len(job_secret_list) == 1)

        # get list of Container App Jobs secrets with secret value
        job_secret_list = self.cmd("az containerapp job secret list --resource-group {} --name {} --show-values".format(resource_group, job), checks=[
            JMESPathCheck('[0].name', "testsecret"),
            JMESPathCheck('[0].value', "testsecretvalue"),
            ]).get_output_in_json()
        self.assertTrue(len(job_secret_list) == 1)

        # Show value of specified secret in a Container App Job
        self.cmd("az containerapp job secret show --resource-group {} --name {} --secret-name testsecret".format(resource_group, job), checks=[
            JMESPathCheck('name', "testsecret"),
            JMESPathCheck('value', "testsecretvalue"),
            ])

        # Update value of existing secret in a Container App Job
        self.cmd("az containerapp job secret set --resource-group {} --name {} --secret 'testsecret=testsecretvaluev2'".format(resource_group, job))

        # check for updated value of existing secret in a Container App Job
        self.cmd("az containerapp job secret show --resource-group {} --name {} --secret-name testsecret".format(resource_group, job), checks=[
            JMESPathCheck('name', "testsecret"),
            JMESPathCheck('value', "testsecretvaluev2"),
        ])

        # add secret for a Container App Job
        job_secret_list_updated = self.cmd("az containerapp job secret set --resource-group {} --name {} --secret 'testsecret2=testsecretvalue2'".format(resource_group, job)).get_output_in_json()
        self.assertTrue(len(job_secret_list_updated) == 2)

        # check for added secret in a Container App Job
        self.cmd("az containerapp job secret show --resource-group {} --name {} --secret-name testsecret2".format(resource_group, job), checks=[
            JMESPathCheck('name', "testsecret2"),
            JMESPathCheck('value', "testsecretvalue2"),
        ])

        # delete secret from a Container App Job
        self.cmd("az containerapp job secret remove --resource-group {} --name {} --secret-name testsecret2 --yes".format(resource_group, job))

        # confirm secret is deleted in a Container App Job, leaving only one secret
        job_secret_list = self.cmd("az containerapp job secret list --resource-group {} --name {} --show-values".format(resource_group, job), checks=[
            JMESPathCheck('[0].name', "testsecret"),
            JMESPathCheck('[0].value', "testsecretvaluev2"),
            ]).get_output_in_json()
        self.assertTrue(len(job_secret_list) == 1)
