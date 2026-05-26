# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
import unittest


class AzureSearchOfferingTests(ScenarioTest):

    # https://vcrpy.readthedocs.io/en/latest/configuration.html#request-matching
    def setUp(self):
        self.vcr.match_on = ['scheme', 'method', 'path', 'query']  # not 'host', 'port'
        super().setUp()

    def test_offering_list(self):
        offerings = self.cmd('az search offering list').get_output_in_json()
        self.assertTrue(len(offerings) > 0)
        self.assertIn('regionName', offerings[0])
        self.assertIn('skus', offerings[0])


if __name__ == '__main__':
    unittest.main()
