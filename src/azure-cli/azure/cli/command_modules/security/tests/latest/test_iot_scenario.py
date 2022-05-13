# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterIotTests(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus')
    def test_security_iot(self):
        self.kwargs.update({
            'iot_hub_name': self.create_random_name(prefix='azurecli-hub', length=24)
        })
        iot_hub_id = self.cmd('az iot hub create -n {iot_hub_name} -g {rg}').get_output_in_json()['id']
        self.kwargs.update({
            'iot_hub_id': iot_hub_id
        })

        self.cmd('az security iot-solution create --solution-name "azurecli-hub" --resource-group {rg} --iot-hubs {iot_hub_id} --display-name "Solution Default" --location "east us"')
        azure_cli_new_iot_security_solution = self.cmd('az security iot-solution list --resource-group {rg}').get_output_in_json()
        assert len(azure_cli_new_iot_security_solution) == 1

        self.cmd('az security iot-solution update --solution-name "azurecli-hub" --resource-group {rg} --iot-hubs {iot_hub_id} --display-name "Solution Default"')
        azure_cli_new_iot_security_solution = self.cmd('az security iot-solution list --resource-group {rg}').get_output_in_json()
        assert len(azure_cli_new_iot_security_solution) == 1

        azure_cli_iot_security_solution = self.cmd('az security iot-solution show --solution-name "azurecli-hub" --resource-group {rg}').get_output_in_json()
        assert len(azure_cli_iot_security_solution) >= 1

        self.cmd('az security iot-solution delete --solution-name "azurecli-hub" --resource-group {rg}')

        azure_cli_no_iot_security_solution = self.cmd('az security iot-solution list --resource-group {rg}').get_output_in_json()
        assert len(azure_cli_no_iot_security_solution) == 0
