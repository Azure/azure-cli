# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterAssessmentsTests(ScenarioTest):

    @AllowLargeResponse()
    def test_security_assessments(self):

        assessments = self.cmd('az security assessment list').get_output_in_json()
        assert len(assessments) >= 0

        assessment_metadata = self.cmd('az security assessment-metadata list').get_output_in_json()
        assert len(assessment_metadata) >= 0

        self.cmd('az security assessment-metadata create -n "8f211ea8-777b-45c4-8631-776d535afd62" --display-name "test assessment" --severity "High" --description "hello world"')

        assessment_metadata = self.cmd('az security assessment-metadata list').get_output_in_json()
        assert any(x["name"] == '8f211ea8-777b-45c4-8631-776d535afd62' for x in assessment_metadata)

        self.cmd('az security assessment create -n 8f211ea8-777b-45c4-8631-776d535afd62 --status-code Healthy')

        assessments = self.cmd('az security assessment list').get_output_in_json()
        assert any(x["name"] == '8f211ea8-777b-45c4-8631-776d535afd62' for x in assessments)

        self.cmd('az security assessment-metadata delete -n "8f211ea8-777b-45c4-8631-776d535afd62"')

        assessment_metadata = self.cmd('az security assessment-metadata list').get_output_in_json()
        assert any(x["name"] == '8f211ea8-777b-45c4-8631-776d535afd62' for x in assessment_metadata) is False

        assessments = self.cmd('az security assessment list').get_output_in_json()
        assert any(x["name"] == '8f211ea8-777b-45c4-8631-776d535afd62' for x in assessments) is False
