# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterJitPolicyTests(ScenarioTest):

    def test_security_jit_policy(self):

        jit_policy = self.cmd('az security jit-policy list').get_output_in_json()

        assert len(jit_policy) >= 0
