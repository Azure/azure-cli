# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest


class ApplicationGatewayDeploymentTierScenarioTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_rg_deployment_tier', location='westus')
    def test_deployment_tier_standard_roundtrip(self, resource_group):
        self.kwargs['rg'] = resource_group
        self.cmd(
            'network public-ip create -g {rg} -n test-pip --sku Standard '
            '--ip-tags FirstPartyUsage=/NonProd'
        )
        self.cmd(
            'network application-gateway create -g {rg} -n test-gateway '
            '--location westus --sku Standard_v2 --capacity 1 --priority 100 '
            '--public-ip-address test-pip --vnet-name test-vnet --subnet appgw '
            '--deployment-tier Standard',
            checks=self.check('applicationGateway.deploymentTier', 'Standard'),
        )
        self.cmd(
            'network application-gateway show -g {rg} -n test-gateway',
            checks=self.check('deploymentTier', 'Standard'),
        )
        self.cmd(
            'network application-gateway update -g {rg} -n test-gateway '
            '--tags validation=unrelated-update',
            checks=self.check('deploymentTier', 'Standard'),
        )
        self.cmd(
            'network application-gateway show -g {rg} -n test-gateway',
            checks=[
                self.check('deploymentTier', 'Standard'),
                self.check('tags.validation', 'unrelated-update'),
            ],
        )
