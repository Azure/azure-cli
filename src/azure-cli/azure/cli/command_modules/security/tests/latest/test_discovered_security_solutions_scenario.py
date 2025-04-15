# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterDiscoveredSecuritySoluytionsTests(ScenarioTest):

    def test_security_discovered_security_solutions(self):

        discovered_security_solutions = self.cmd('az security discovered-security-solution list').get_output_in_json()

        assert len(discovered_security_solutions) >= 0
