# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse


class SecurityCenterIotTests(ScenarioTest):

    @AllowLargeResponse()
    def test_security_iot(self):
        if(self.cmd('az security iot-solution list --resource-group "AzureCLI"').get_output_in_json() == 0):
            return

        azure_cli_iot_security_solution = self.cmd('az security iot-solution show --solution-name "azurecli-hub" --resource-group "AzureCLI"').get_output_in_json()
        assert len(azure_cli_iot_security_solution) >= 1

        self.cmd('az security iot-solution delete --solution-name "azurecli-hub" --resource-group "AzureCLI"')

        azure_cli_no_iot_security_solution = self.cmd('az security iot-solution list --resource-group "AzureCLI"').get_output_in_json()
        assert len(azure_cli_no_iot_security_solution) == 0

        self.cmd('az security iot-solution create --solution-name "azurecli-hub" --resource-group "AzureCLI" --iot-hubs /subscriptions/ba3e71a7-6385-4944-9f01-d611121199bb/resourcegroups/AzureCLI/providers/Microsoft.Devices/IotHubs/azurecli-hub --display-name "Solution Default" --location "east us"')
        azure_cli_new_iot_security_solution = self.cmd('az security iot-solution list --resource-group "AzureCLI"').get_output_in_json()
        assert len(azure_cli_new_iot_security_solution) == 1

        self.cmd('az security iot-solution update --solution-name "azurecli-hub" --resource-group "AzureCLI" --iot-hubs /subscriptions/ba3e71a7-6385-4944-9f01-d611121199bb/resourcegroups/AzureCLI/providers/Microsoft.Devices/IotHubs/azurecli-hub --display-name "Solution Default"')
        azure_cli_new_iot_security_solution = self.cmd('az security iot-solution list --resource-group "AzureCLI"').get_output_in_json()
        assert len(azure_cli_new_iot_security_solution) == 1
