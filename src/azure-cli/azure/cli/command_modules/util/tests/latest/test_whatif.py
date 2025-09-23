# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os
from unittest.mock import patch, Mock
from azure.cli.testsdk import ScenarioTest

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


class WhatIfTest(ScenarioTest):

    def setUp(self):
        super().setUp()
        self.test_script_path = os.path.join(TEST_DIR, 'test_whatif_script.sh')

    @patch('azure.cli.core.commands.client_factory.get_subscription_id')
    @patch('azure.cli.core.what_if._get_auth_headers')
    @patch('azure.cli.core.what_if._make_what_if_request')
    def test_what_if_command(self, mock_make_request, mock_get_headers, mock_get_subscription_id):
        mock_get_subscription_id.return_value = 'test-subscription-id'
        mock_get_headers.return_value = {'Authorization': 'Bearer test-token'}
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "what_if_result": {
                "changes": [
                    {
                        "changeType": "Create",
                        "resourceId": "/subscriptions/test/resourceGroups/myrg/providers/Microsoft.Compute/virtualMachines/MyVM_01",
                        "before": None,
                        "after": {
                            "name": "MyVM_01",
                            "type": "Microsoft.Compute/virtualMachines",
                            "location": "eastus"
                        },
                        "delta": []
                    }
                ],
                "potential_changes": [],
                "diagnostics": []
            }
        }
        mock_make_request.return_value = mock_response

        result = self.cmd('az what-if --script-path "{}" --no-pretty-print'.format(self.test_script_path))
        output = result.get_output_in_json()

        self.assertIsInstance(output, dict)
        self.assertIn("changes", output)
        self.assertEqual(len(output["changes"]), 1)
        self.assertEqual(output["changes"][0]["changeType"], "Create")

        mock_get_subscription_id.assert_called_once()
        mock_get_headers.assert_called_once()
        mock_make_request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
