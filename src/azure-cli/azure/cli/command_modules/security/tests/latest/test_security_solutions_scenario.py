# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecuritySoluytionsTests(ScenarioTest):

    def test_security_security_solutions(self):

        security_solutions = self.cmd('az security security-solutions list').get_output_in_json()

        assert len(security_solutions) >= 0

        self.cmd('az security security-solutions list')
