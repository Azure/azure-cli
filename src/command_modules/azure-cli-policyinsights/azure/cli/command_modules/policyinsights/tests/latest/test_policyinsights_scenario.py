# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only


@record_only()
class PolicyInsightsTests(ScenarioTest):

    def test_policy_insights(self):
        top_clause = '--top 2'
        filter_clause = '--filter "isCompliant eq false"'
        apply_clause = '--apply "groupby((policyAssignmentId, resourceId), aggregate($count as numRecords))"'
        select_clause = '--select "policyAssignmentId, resourceId, numRecords"'
        order_by_clause = '--order-by "numRecords desc"'
        from_clause = '--from "2018-04-04T00:00:00"'
        to_clause = '--to "2018-05-22T00:00:00"'
        scopes = [
            '-m "azgovtest4"',
            '',
            '-g "defaultresourcegroup-eus"',
            '--resource "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/eastusnsggroup/providers/microsoft.network/networksecuritygroups/eastusnsg/securityrules/allow-joba"',
            '--resource "omssecuritydevkeyvalut" --namespace "microsoft.keyvault" --resource-type "vaults" -g "omssecurityintresourcegroup"',
            '--resource "default" --namespace "microsoft.network" --resource-type "subnets" --parent "virtualnetworks/mms-wcus-vnet" -g "mms-wcus"',
            '-s "335cefd2-ab16-430f-b364-974a170eb1d5"',
            '-d "25bf1e2a-6004-47ad-9bd1-2a40dd6de016"',
            '-a "96e22f7846e94bb186ae3a01"',
            '-a "bc916e4f3ab54030822a11b3" -g "tipkeyvaultresourcegroup" '
        ]

        for scope in scopes:
            events = self.cmd('az policy event list {} {} {} {} {} {} {} {}'.format(
                scope,
                from_clause,
                to_clause,
                filter_clause,
                apply_clause,
                select_clause,
                order_by_clause,
                top_clause)).get_output_in_json()
            assert len(events) >= 0

            states = self.cmd('az policy state list {} {} {} {} {} {} {} {}'.format(
                scope,
                from_clause,
                to_clause,
                filter_clause,
                apply_clause,
                select_clause,
                order_by_clause,
                top_clause)).get_output_in_json()
            assert len(states) >= 0

            summary = self.cmd('az policy state summarize {} {} {} {} {}'.format(
                scope,
                from_clause,
                to_clause,
                filter_clause,
                top_clause)).get_output_in_json()
            assert summary["results"] is not None
            assert len(summary["policyAssignments"]) >= 0
            if len(summary["policyAssignments"]) > 0:
                assert summary["policyAssignments"][0]["results"] is not None
                assert len(summary["policyAssignments"][0]["policyDefinitions"]) >= 0
                if len(summary["policyAssignments"][0]["policyDefinitions"]) > 0:
                    assert summary["policyAssignments"][0]["policyDefinitions"][0]["results"] is not None
