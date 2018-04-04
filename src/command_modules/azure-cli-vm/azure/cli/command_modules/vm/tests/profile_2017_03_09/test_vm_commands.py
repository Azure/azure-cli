# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer)


class VMSSCreateBalancerOptionsTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_stack_vmss_create_default_app_gateway(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })

        res = self.cmd("vmss create -g {rg} --name {vmss} --validate --image UbuntuLTS --instance-count 101 --admin-username ubuntuadmin --generate-ssh-keys").get_output_in_json()
        # ensure we default to app-gateway
        dependencies = res['properties']['dependencies']
        self.assertTrue(next((x for x in dependencies if x['resourceType'] == 'Microsoft.Network/applicationGateways' and x['resourceName'] == '{}AG'.format(self.kwargs['vmss'])), None))
