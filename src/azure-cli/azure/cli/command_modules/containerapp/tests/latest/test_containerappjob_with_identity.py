# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.mgmt.core.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, JMESPathCheckExists,
                               JMESPathCheckNotExists)

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION
from .utils import prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppJobsIdentityOperationsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="northcentralus")
    # test for CRUD operations on Container App Job resource with trigger type as manual
    def test_containerapp_manualjob_withidentity_crudoperations_e2e(self, resource_group):
        import requests

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
        # create a Container App Job resource with trigger type as manual and with a system assigned identity
        self.cmd("az containerapp job create --resource-group {} --name {} --environment {} --secrets 'testsecret=testsecretvalue' --replica-timeout 200 --replica-retry-limit 2 --trigger-type manual --parallelism 1 --replica-completion-count 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi' --system-assigned".format(resource_group, job, env_id))

        # verify the container app job resource contains system identity
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('name', job),
            JMESPathCheck('properties.configuration.replicaTimeout', 200),
            JMESPathCheck('properties.configuration.replicaRetryLimit', 2),
            JMESPathCheck('properties.configuration.triggerType', "manual", case_sensitive=False),
            JMESPathCheck('identity.type', "SystemAssigned", case_sensitive=False),
            JMESPathCheckExists('identity.principalId'),
            JMESPathCheckExists('identity.tenantId'),
        ])

        # get list of Container App Jobs secrets
        self.cmd("az containerapp job identity show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('type', "SystemAssigned", case_sensitive=False),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('tenantId'),
        ])

        # create a user assigned identity
        user_identity_name = self.create_random_name(prefix='containerappjob-user', length=24)
        user_identity = self.cmd('identity create -g {} -n {}'.format(resource_group, user_identity_name)).get_output_in_json()
        user_identity_id = user_identity['id']

        # assign user identity to container app job
        self.cmd("az containerapp job identity assign --resource-group {} --name {} --user-assigned '{}'".format(resource_group, job, user_identity_id), checks=[
            JMESPathCheck('type', "SystemAssigned, UserAssigned", case_sensitive=False),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('tenantId'),
            JMESPathCheckExists('userAssignedIdentities'),
        ])

        # Remove user assigned identity from container app job
        self.cmd("az containerapp job identity remove --resource-group {} --name {} --user-assigned '{}' --yes".format(resource_group, job, user_identity_id), checks=[
            JMESPathCheck('type', "SystemAssigned", case_sensitive=False),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('tenantId'),
            JMESPathCheckNotExists('userAssignedIdentities'),
        ])

        # Remove system assigned identity from container app job
        self.cmd("az containerapp job identity remove --resource-group {} --name {} --system-assigned --yes".format(resource_group, job), checks=[
            JMESPathCheck('type', "None", case_sensitive=False)
        ])

        # confirm no identity is assigned to container app job
        self.cmd("az containerapp job identity show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('type', "None", case_sensitive=False)
        ])

        # check container app job resource does not have any identity
        self.cmd("az containerapp job show --resource-group {} --name {}".format(resource_group, job), checks=[
            JMESPathCheck('identity.type', "None", case_sensitive=False)
        ])