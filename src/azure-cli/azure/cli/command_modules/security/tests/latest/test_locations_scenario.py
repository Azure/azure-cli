# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterLocationsTests(ScenarioTest):

    def test_security_locations(self):

        locations = self.cmd('az security location list').get_output_in_json()

        assert len(locations) == 1

        self.cmd('az security location show -n ' + locations[0]["name"]).get_output_in_json()
