# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestConfigure(unittest.TestCase):
    def test_configure_output_options(self):
        from azure.cli.core._output import AzOutputProducer
        from azure.cli.core.mock import DummyCli
        from azure.cli.command_modules.configure._consts import OUTPUT_LIST

        output_producer = AzOutputProducer(DummyCli())
        cli_output_options = set(output_producer._FORMAT_DICT.keys())
        configure_output_options = set(item["name"] for item in OUTPUT_LIST)

        self.assertEqual(cli_output_options, configure_output_options,
                         "\n{}'s output options: {}\ndon't match az configure's output options ({})."
                         .format(AzOutputProducer.__name__, cli_output_options, configure_output_options))


if __name__ == '__main__':
    unittest.main()
