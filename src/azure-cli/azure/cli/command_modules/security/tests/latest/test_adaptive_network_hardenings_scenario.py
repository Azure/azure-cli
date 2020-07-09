# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse


class SecurityCenterAdaptiveNetworkHardeningsTests(ScenarioTest):

    @AllowLargeResponse()
    def test_adaptive_network_hardenings(self):

        adaptive_network_hardenings = self.cmd('az security adaptive_network_hardenings list --resource-group MSI-GLStandard_A1 --resource-type virtualMachines --resource-namespace Microsoft.Compute --resource-name MSI-22122').get_output_in_json()

        assert len(adaptive_network_hardenings) >= 0
