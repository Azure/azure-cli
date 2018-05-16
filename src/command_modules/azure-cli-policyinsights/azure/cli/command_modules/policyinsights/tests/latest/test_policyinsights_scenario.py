# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

class PolicyInsightsTests(ScenarioTest):

    def test_policy_insights(self):
        events = self.cmd('az policy event list --top 2').get_output_in_json()
        assert len(events) >= 0

        states = self.cmd('az policy state list --top 2').get_output_in_json()
        assert len(states) >= 0

        summary = self.cmd('az policy state summarize --top 2').get_output_in_json()
        assert summary["results"] is not None
        assert len(summary["policyAssignments"]) >= 0
        assert summary["policyAssignments"][0]["results"] is not None
        assert len(summary["policyAssignments"][0]["policyDefinitions"]) >= 0
        assert summary["policyAssignments"][0]["policyDefinitions"][0]["results"] is not None
