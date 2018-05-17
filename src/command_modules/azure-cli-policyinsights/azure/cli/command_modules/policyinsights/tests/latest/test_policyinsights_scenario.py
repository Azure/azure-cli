# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

class PolicyInsightsTests(ScenarioTest):

    def test_policy_insights(self):
        top_clause = '--top 2'
        filter_clause = '--filter "policyDefinitionAction eq \'audit\'"'
        apply_clause = '--apply "groupby((policyAssignmentId, resourceId), aggregate($count as numRecords))"'
        select_clause = '--select "policyAssignmentId, resourceId, numRecords"'
        order_by_clause = '--order-by "numRecords desc"'
        
        events = self.cmd('az policy event list {} {} {} {} {}'.format(
            filter_clause, 
            apply_clause, 
            select_clause, 
            order_by_clause, 
            top_clause)).get_output_in_json()
        assert len(events) >= 0

        states = self.cmd('az policy state list {} {} {} {} {}'.format(
            filter_clause, 
            apply_clause, 
            select_clause, 
            order_by_clause, 
            top_clause)).get_output_in_json()
        assert len(states) >= 0

        summary = self.cmd('az policy state summarize {} {}'.format(
            filter_clause, 
            top_clause)).get_output_in_json()
        assert summary["results"] is not None
        assert len(summary["policyAssignments"]) >= 0
        assert summary["policyAssignments"][0]["results"] is not None
        assert len(summary["policyAssignments"][0]["policyDefinitions"]) >= 0
        assert summary["policyAssignments"][0]["policyDefinitions"][0]["results"] is not None
