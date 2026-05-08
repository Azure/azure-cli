# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test


class CognitiveServicesManagedComputeDeploymentTests(ScenarioTest):
    @serial_test()
    @ResourceGroupPreparer()
    def test_cognitiveservices_managed_compute_deployment(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'deployment_name': 'test-mcd',
            'model': 'azureml://registries/azureml-openai-oss/models/gpt-oss-120b/versions/4',
            'deployment_template': 'azureml://registries/azureml-openai-oss/deploymenttemplates/'
                                   'gpt-oss-120b-short-context/versions/1',
            'accelerator_type': 'H100_80GB',
            'sku_name': 'GlobalManagedCompute',
            'sku_capacity': '1',
        })

        # create cognitive services account
        self.cmd(
            'az cognitiveservices account create -n {sname} -g {rg} '
            '--kind {kind} --sku {sku} -l {location} --yes',
            checks=[
                self.check('name', '{sname}'),
                self.check('properties.provisioningState', 'Succeeded'),
            ])

        # list should be empty initially
        self.cmd(
            'az cognitiveservices account managed-compute-deployment list '
            '-n {sname} -g {rg}',
            checks=[self.check('length(@)', 0)])

        # create managed compute deployment
        self.cmd(
            'az cognitiveservices account managed-compute-deployment create '
            '-n {sname} -g {rg} '
            '--deployment-name {deployment_name} '
            '--model "{model}" '
            '--deployment-template "{deployment_template}" '
            '--accelerator-type {accelerator_type} '
            '--sku-name {sku_name} '
            '--sku-capacity {sku_capacity} '
            '--tags environment=test')

        # show the deployment
        self.cmd(
            'az cognitiveservices account managed-compute-deployment show '
            '-n {sname} -g {rg} '
            '--deployment-name {deployment_name}',
            checks=[
                self.check('name', '{deployment_name}'),
                self.check('properties.model', '{model}'),
                self.check('sku.name', '{sku_name}'),
            ])

        # list should contain the deployment
        self.cmd(
            'az cognitiveservices account managed-compute-deployment list '
            '-n {sname} -g {rg}',
            checks=[self.check('length(@)', 1)])

        # update sku capacity
        self.cmd(
            'az cognitiveservices account managed-compute-deployment update '
            '-n {sname} -g {rg} '
            '--deployment-name {deployment_name} '
            '--sku-capacity 2')

        # delete the deployment
        self.cmd(
            'az cognitiveservices account managed-compute-deployment delete '
            '-n {sname} -g {rg} '
            '--deployment-name {deployment_name}')

        # verify deletion
        self.cmd(
            'az cognitiveservices account managed-compute-deployment list '
            '-n {sname} -g {rg}',
            checks=[self.check('length(@)', 0)])

        # cleanup
        self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')


if __name__ == '__main__':
    unittest.main()
