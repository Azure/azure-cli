# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest

from azure.cli.testsdk import ScenarioTest, LocalContextScenarioTest


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


class ConfigureGlobalDefaultsTest(ScenarioTest):

    def setUp(self):
        self.local_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.cmd('configure --defaults global="" global2=""')
        self.cmd('configure --defaults local="" --scope local')

    def test_configure_global_defaults(self):
        # setiing the az configure defaults
        self.cmd('configure --defaults global=global1')
        self.cmd('configure --defaults global2=global2')

        # configure a local setting
        os.chdir(self.local_dir)
        self.cmd('configure --defaults local=local1 --scope local')

        # test listing defaults
        res = self.cmd('configure --list-defaults --scope local').get_output_in_json()
        self.assertTrue(len(res), 3)
        actual = set([(x['name'], x['value']) for x in res])
        expected = set([('local', 'local1'), ('global', 'global1'), ('global2', 'global2')])
        self.assertTrue(actual == expected)
        res = self.cmd('configure --list-defaults').get_output_in_json()
        self.assertEqual(len(res), 2)
        actual = set([(x['name'], x['value']) for x in res])
        expected = set([('global', 'global1'), ('global2', 'global2')])
        self.assertTrue(actual == expected)


if __name__ == '__main__':
    unittest.main()
