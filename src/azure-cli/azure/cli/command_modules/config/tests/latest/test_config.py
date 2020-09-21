# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from azure.cli.testsdk import ScenarioTest, LocalContextScenarioTest
from knack.util import CLIError


class ConfigTest(ScenarioTest):

    def test_config(self):

        # [core]
        # core_option1 = core_value1
        # core_option2 = core_value2
        #
        # [test_section1]
        # test_option1 = test_value1
        #
        # [test_section2]
        # test_option21 = test_value21
        # test_option22 = test_value22

        # C:\Users\{username}\AppData\Local\Temp
        tempdir = os.path.realpath(tempfile.gettempdir())  # call realpath to handle soft link problem on MAC
        original_path = os.getcwd()
        os.chdir(tempdir)
        print("Using temp dir: {}".format(tempdir))

        global_test_args = {"source": os.path.expanduser(os.path.join('~', '.azure', 'config')), "flag": ""}
        local_test_args = {"source": os.path.join(tempdir, '.azure', 'config'), "flag": " --local"}

        for args in (global_test_args, local_test_args):
            core_option1_expected = {'name': 'core_option1', 'source': args["source"], 'value': 'core_value1'}
            core_option2_expected = {'name': 'core_option2', 'source': args["source"], 'value': 'core_value2'}
            test_option1_expected = {'name': 'test_option1', 'source': args["source"], 'value': 'test_value1'}
            test_option21_expected = {'name': 'test_option21', 'source': args["source"], 'value': 'test_value21'}
            test_option22_expected = {'name': 'test_option22', 'source': args["source"], 'value': 'test_value22'}

            test_section1_expected = [test_option1_expected]
            test_section2_expected = [test_option21_expected, test_option22_expected]

            # 1. set
            # Set `core` section without explicitly specifying `core`
            self.cmd('config set core_option1=core_value1' + args['flag'])
            # Set `core` section by explicitly specifying `core`
            self.cmd('config set core.core_option2=core_value2' + args['flag'])
            # Set one option
            self.cmd('config set test_section1.test_option1=test_value1' + args['flag'])
            # Set multiple options
            self.cmd('config set test_section2.test_option21=test_value21 test_section2.test_option22=test_value22' + args['flag'])

            # 2. get
            # 2.1 Get all sections
            output = self.cmd('config get' + args['flag']).get_output_in_json()
            self.assertIn(core_option1_expected, output['core'])
            self.assertIn(core_option2_expected, output['core'])
            self.assertListEqual(output['test_section1'], test_section1_expected)
            self.assertListEqual(output['test_section2'], test_section2_expected)

            # 2.2 Get one section
            output = self.cmd('config get test_section1.' + args['flag']).get_output_in_json()
            self.assertListEqual(output, test_section1_expected)
            output = self.cmd('config get test_section2.' + args['flag']).get_output_in_json()
            self.assertListEqual(output, test_section2_expected)

            # 2.3 Get one item
            output = self.cmd('config get core_option1' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, core_option1_expected)
            output = self.cmd('config get core.core_option2' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, core_option2_expected)
            output = self.cmd('config get test_section1.test_option1' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, test_option1_expected)
            output = self.cmd('config get test_section2.test_option21' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, test_option21_expected)
            output = self.cmd('config get test_section2.test_option22' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, test_option22_expected)

            with self.assertRaises(CLIError):
                self.cmd('config get test_section1.non_exist' + args['flag'])

            # 3. unset
            # Set `core` section without explicitly specifying `core`
            self.cmd('config unset core_option1' + args['flag'])
            with self.assertRaises(CLIError):
                self.cmd('config get core_option1' + args['flag'])

            # Unset `core` section by explicitly specifying `core`
            self.cmd('config unset core.core_option2' + args['flag'])
            with self.assertRaises(CLIError):
                self.cmd('config get core.core_option2' + args['flag'])

            # Unset one option
            self.cmd('config unset test_section1.test_option1' + args['flag'])
            with self.assertRaises(CLIError):
                self.cmd('config get test_section1.test_option1' + args['flag'])

            # Unset multiple options
            self.cmd('config unset test_section2.test_option21 test_section2.test_option22' + args['flag'])
            with self.assertRaises(CLIError):
                self.cmd('config get test_section2.test_option21' + args['flag'])
            with self.assertRaises(CLIError):
                self.cmd('config get test_section2.test_option22' + args['flag'])

        os.chdir(original_path)

    def test_parse_key(self):
        from azure.cli.command_modules.config.custom import _parse_key
        # Test section defaults to core
        self.assertEqual(_parse_key("test_option"), ('core', 'test_option'))
        # Test explicitly specifying section as core
        self.assertEqual(_parse_key("core.test_option"), ('core', 'test_option'))
        # Test specifying only section for get operation
        self.assertEqual(_parse_key("core."), ('core', ''))
        # Test empty key raises a ValueError
        with self.assertRaises(ValueError):
            _parse_key("")


if __name__ == '__main__':
    unittest.main()
