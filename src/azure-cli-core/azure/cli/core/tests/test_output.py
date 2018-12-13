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
        self.assertEqual(5, len(output_producer._FORMAT_DICT))  # five types: json, jsonc, table, tsv, yaml
        self.assertIn('yaml', output_producer._FORMAT_DICT)


if __name__ == '__main__':
    unittest.main()
