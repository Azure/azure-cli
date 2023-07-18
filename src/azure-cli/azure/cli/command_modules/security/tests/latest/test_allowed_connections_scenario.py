# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterAllowedConnectionsTests(ScenarioTest):

    @AllowLargeResponse()
    def test_allowed_connections(self):

        allowed_connections = self.cmd('az security allowed_connections list').get_output_in_json()

        assert len(allowed_connections) >= 0
