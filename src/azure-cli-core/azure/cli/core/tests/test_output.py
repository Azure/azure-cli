# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestCoreCLIOutput(unittest.TestCase):
    def test_create_AzOutputProducer(self):
        from azure.cli.core._output import AzOutputProducer
        from azure.cli.core.mock import DummyCli

        output_producer = AzOutputProducer(DummyCli())
        self.assertEqual(7, len(output_producer._FORMAT_DICT))  # six types: json, jsonc, table, tsv, yaml, yamlc, none
        self.assertIn('yaml', output_producer._FORMAT_DICT)
        self.assertIn('none', output_producer._FORMAT_DICT)

    # regression test for https://github.com/Azure/azure-cli/issues/9263
    def test_yaml_output_with_ordered_dict(self):
        from azure.cli.core._output import AzOutputProducer
        from azure.cli.core.mock import DummyCli
        from knack.util import CommandResultItem
        from collections import OrderedDict
        import yaml

        account_dict = {
            "environmentName": "AzureCloud",
            "id": "000000-000000",
            "isDefault": True,
            "name": "test_sub",
            "state": "Enabled",
            "tenantId": "000000-000000-000000",
            "user": {
                "name": "test@example.com",
                "type": "user"
            }
        }

        output_producer = AzOutputProducer(DummyCli())
        yaml_output = output_producer.get_formatter('yaml')(CommandResultItem(result=OrderedDict(account_dict)))
        self.assertEqual(account_dict, yaml.safe_load(yaml_output))


if __name__ == '__main__':
    unittest.main()
