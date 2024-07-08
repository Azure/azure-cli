# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test


class CognitiveServicesTests(ScenarioTest):
    def test_cognitiveservices_list_models(self):
        models = self.cmd('az cognitiveservices model list -l westeurope').get_output_in_json()
        self.assertTrue(len(models) > 0)
        self.assertIsNotNone(models[0]['kind'])
        self.assertIsNotNone(models[0]['skuName'])
        self.assertIsNotNone(models[0]['model'])
        self.assertIsNotNone(models[0]['model']['name'])
        self.assertIsNotNone(models[0]['model']['skus'])
        self.assertIsNotNone(models[0]['model']['skus'][0]['name'])

    def test_cognitiveservices_list_usages(self):
        usages = self.cmd('az cognitiveservices usage list -l westeurope').get_output_in_json()
        self.assertTrue(len(usages) > 0)
        self.assertIsNotNone(usages[0]['currentValue'])
        self.assertIsNotNone(usages[0]['limit'])
        self.assertIsNotNone(usages[0]['name'])
        self.assertIsNotNone(usages[0]['name']['value'])


if __name__ == '__main__':
    unittest.main()
