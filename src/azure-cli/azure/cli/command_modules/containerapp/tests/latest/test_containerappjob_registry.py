# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, JMESPathCheckExists,
                               JMESPathCheckNotExists)

from azure.cli.command_modules.containerapp.tests.latest.common import TEST_LOCATION
from .utils import prepare_containerapp_env_for_app_e2e_tests

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppJobsRegistryOperationsTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @ResourceGroupPreparer(location="northeurope")
    @AllowLargeResponse()
    def test_containerappjob_registry_crud(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        job = self.create_random_name(prefix='app', length=24)
        acr = self.create_random_name(prefix='acr', length=24)
        env = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(
            "az containerapp job create --resource-group {} --name {} --environment {} --replica-timeout 200 --replica-retry-limit 2 --trigger-type manual --parallelism 1 --replica-completion-count 1 --image mcr.microsoft.com/k8se/quickstart-jobs:latest --cpu '0.25' --memory '0.5Gi'".format(
                resource_group, job, env))
        acr_server = f'{acr}.azurecr.io'
        self.cmd(f'acr create -g {resource_group} -n {acr} --sku basic --admin-enabled')
        # self.cmd(f'acr credential renew -n {acr} ')
        self.cmd(f'containerapp job registry set --server {acr}.azurecr.io -g {resource_group} -n {job}', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].server', acr_server),
            JMESPathCheck('[0].passwordSecretRef', f'{acr}azurecrio-{acr}'),
            JMESPathCheck('[0].username', acr)
        ])
        registry_list = self.cmd(f'containerapp job registry list -g {resource_group} -n {job}', checks=[
            JMESPathCheck('length(@)', 1),
        ]).get_output_in_json()

        self.cmd(f'containerapp job registry show -g {resource_group} -n {job} --server {registry_list[0]["server"]}',
                 checks=[
                     JMESPathCheck('server', acr_server),
                     JMESPathCheck('passwordSecretRef', f'{acr}azurecrio-{acr}'),
                     JMESPathCheck('username', acr)
                 ])

        self.cmd(
            f'containerapp job registry set --server {acr}.azurecr.io -g {resource_group} -n {job} --identity system', checks=[
                JMESPathCheck('length(@)', 1),
                JMESPathCheck('[0].server', acr_server),
                JMESPathCheck('[0].identity', "system")
            ])

        self.cmd(f'containerapp job registry remove -g {resource_group} -n {job} --server {registry_list[0]["server"]}', expect_failure=False)
        self.cmd(f'containerapp job registry list -g {resource_group} -n {job}', checks=[
            JMESPathCheck('length(@)', 0),
        ])
