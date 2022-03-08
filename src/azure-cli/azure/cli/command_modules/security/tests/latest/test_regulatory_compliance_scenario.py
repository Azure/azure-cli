# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterRegulatoryComplianceTests(ScenarioTest):

    @AllowLargeResponse()
    def test_security_compliance(self):

        standards_list = self.cmd('az security regulatory-compliance-standards list').get_output_in_json()
        assert len(standards_list) > 0

        standard = self.cmd('az security regulatory-compliance-standards show -n "Azure-CIS-1.1.0"').get_output_in_json()
        assert len(standard) > 0

        controls_list = self.cmd('az security regulatory-compliance-standards show -n "Azure-CIS-1.1.0"').get_output_in_json()
        assert len(controls_list) > 0

        control = self.cmd('az security regulatory-compliance-controls show --standard-name "Azure-CIS-1.1.0" -n "1.1"').get_output_in_json()
        assert len(control) > 0

        assessments_list = self.cmd('az security regulatory-compliance-assessments list --standard-name "Azure-CIS-1.1.0" --control-name "1.1"').get_output_in_json()
        assert len(assessments_list) > 0

        assessment = self.cmd('az security regulatory-compliance-assessments show --standard-name "Azure-CIS-1.1.0" --control-name "1.1" -n "94290b00-4d0c-d7b4-7cea-064a9554e681"').get_output_in_json()
        assert len(assessment) > 0
