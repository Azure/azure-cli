# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
import re


class SecurityCenterTopologiesTests(ScenarioTest):

    def test_security_topology(self):

        topology = self.cmd('az security topology list').get_output_in_json()

        assert len(topology) >= 0
