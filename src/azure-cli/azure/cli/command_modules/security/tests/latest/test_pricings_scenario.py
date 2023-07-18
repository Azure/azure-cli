# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterPricingsTests(ScenarioTest):

    def test_security_pricings(self):

        pricings = self.cmd('az security pricing list').get_output_in_json()

        assert len(pricings) >= 0

        self.cmd('az security pricing create -n VirtualMachines --tier free')

        pricing = self.cmd('az security pricing show -n VirtualMachines').get_output_in_json()

        assert pricing["pricingTier"] == "Free"

        self.cmd('az security pricing create -n VirtualMachines --tier standard')

        pricing = self.cmd('az security pricing show -n VirtualMachines').get_output_in_json()

        assert pricing["pricingTier"] == "Standard"
