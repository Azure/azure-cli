# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import patch, MagicMock
import json

from azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.create import (
    create_rules,
    get_recording_rules_template
)
from azure.cli.core.util import send_raw_request


class TestCreateRulesFunction(unittest.TestCase):
    @patch('azure.cli.core.util.send_raw_request')
    def test_get_recording_rules_template_filters_valid_templates(self, mock_send):
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "value": [
                {
                    "name": "validRuleGroup",
                    "properties": {
                        "alertRuleType": "microsoft.alertsmanagement/prometheusrulegroups",
                        "rulesArmTemplate": {
                            "resources": [
                                {
                                    "type": "Microsoft.AlertsManagement/prometheusRuleGroups",
                                    "properties": {
                                        "rules": [
                                            {"record": "cpu_usage", "expression": "some_expr"}
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                },
                {
                    "name": "invalidRuleGroup",
                    "properties": {
                        "alertRuleType": "microsoft.alertsmanagement/somethingelse"
                    }
                }
            ]
        })
        mock_send.return_value = mock_response

        result = get_recording_rules_template(MagicMock(), "/dummy/resource/id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "validRuleGroup")


    @patch('azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.create.get_recording_rules_template')
    @patch('azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.create.put_rules')
    def test_create_rules_respects_windows_flag(self, mock_put_rules, mock_get_templates):
        mock_get_templates.return_value = [
            {
                "name": "NodeRecordingRulesRuleGroup-Win",
                "properties": {
                    "rulesArmTemplate": {
                        "resources": [
                            {
                                "type": "Microsoft.AlertsManagement/prometheusRuleGroups",
                                "properties": {
                                    "rules": [{"record": "win_cpu", "expression": "usage"}]
                                }
                            }
                        ]
                    }
                }
            },
            {
                "name": "KubernetesRecordingRulesRuleGroup",
                "properties": {
                    "rulesArmTemplate": {
                        "resources": [
                            {
                                "type": "Microsoft.AlertsManagement/prometheusRuleGroups",
                                "properties": {
                                    "rules": [{"record": "kube_cpu", "expression": "usage"}]
                                }
                            }
                        ]
                    }
                }
            }
        ]

        cmd = MagicMock()
        cmd.cli_ctx.cloud.endpoints.resource_manager = "https://management.azure.com/"
        raw_parameters = {"enable_windows_recording_rules": False}

        create_rules(
            cmd,
            cluster_subscription="sub123",
            cluster_resource_group_name="rg1",
            cluster_name="mycluster",
            azure_monitor_workspace_resource_id="/dummy/ampls",
            mac_region="eastus",
            raw_parameters=raw_parameters
        )

        # Check put_rules was called for both rule groups
        self.assertEqual(mock_put_rules.call_count, 2)

        for call in mock_put_rules.call_args_list:
            rule_group_name = call.args[2]  # 3rd positional argument
            enable_rules = call.args[9]     # 10th positional argument

            if "Win" in rule_group_name:
                self.assertFalse(enable_rules, f"Expected enable_rules=False for {rule_group_name}")
            else:
                self.assertTrue(enable_rules, f"Expected enable_rules=True for {rule_group_name}")


if __name__ == '__main__':
    unittest.main()
