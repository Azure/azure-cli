# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterAdaptiveadaptiveApplicationControlsTests(ScenarioTest):

    @record_only()  # This test makes use of existing resources
    @AllowLargeResponse()
    def test_adaptive_application_controls(self):

        adaptive_application_controls = self.cmd('az security adaptive-application-controls list').get_output_in_json()

        assert len(adaptive_application_controls) >= 0
        group_name = adaptive_application_controls['value'][0]['name']
        self.kwargs.update({
            'group_name': group_name
        })

        adaptive_application_controls = self.cmd('az security adaptive-application-controls show --group-name {group_name}').get_output_in_json()

        assert len(adaptive_application_controls) >= 0
