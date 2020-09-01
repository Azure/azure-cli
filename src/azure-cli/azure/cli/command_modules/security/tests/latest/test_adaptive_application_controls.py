# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse


class SecurityCenterAdaptiveadaptiveApplicationControlsTests(ScenarioTest):

    @AllowLargeResponse()
    def test_adaptive_application_controls(self):

        adaptive_application_controls = self.cmd('az security adaptive-application-controls list').get_output_in_json()

        assert len(adaptive_application_controls) >= 0

        adaptive_application_controls = self.cmd('az security adaptive-application-controls show --group-name GROUP1').get_output_in_json()

        assert len(adaptive_application_controls) >= 0
