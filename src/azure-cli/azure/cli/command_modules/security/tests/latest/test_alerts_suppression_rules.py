# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pytest
from azure.cli.testsdk import ScenarioTest


class SecurityCenterAlertsSuppressionRuleTests(ScenarioTest):


    def test_security_alerts_suppression_rule(self):
            self.kwargs.update({
                'rule_name': self.create_random_name(prefix='azurecli-test', length=24)
            })

            azure_cli_new_suppression_rule = self.cmd('az security alerts-suppression-rule update --rule-name {rule_name} --alert-type "Test" --reason "Other" --comment "Test comment" --state "Enabled" --all-of "[{{\\"contains\\": \\"testContains\\", \\"field\\": \\"entities.host.dnsdomain\\"}}]"').get_output_in_json()
            assert len(azure_cli_new_suppression_rule) > 0

            azure_cli_get_suppression_rule = self.cmd('az security alerts-suppression-rule show --rule-name {rule_name}').get_output_in_json()
            assert len(azure_cli_get_suppression_rule) > 0

            azure_cli_list_suppression_rule = self.cmd('az security alerts-suppression-rule list').get_output_in_json()
            assert len(azure_cli_list_suppression_rule) > 0

            self.cmd('az security alerts-suppression-rule delete --rule-name {rule_name}')