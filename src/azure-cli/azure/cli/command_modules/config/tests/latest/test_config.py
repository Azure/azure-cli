# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest

from azure.cli.testsdk import ScenarioTest

from knack.util import CLIError


class ConfigTest(ScenarioTest):

    def test_config(self):

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
            print("Testing for {}".format(args))

            test_option1_expected = {'name': 'test_option1', 'source': args["source"], 'value': 'test_value1'}
            test_option21_expected = {'name': 'test_option21', 'source': args["source"], 'value': 'test_value21'}
            test_option22_expected = {'name': 'test_option22', 'source': args["source"], 'value': 'test_value22'}

            test_section1_expected = [test_option1_expected]
            test_section2_expected = [test_option21_expected, test_option22_expected]

            # 1. set
            # Test setting one option
            self.cmd('config set test_section1.test_option1=test_value1' + args['flag'])
            # Test setting multiple options
            self.cmd('config set test_section2.test_option21=test_value21 test_section2.test_option22=test_value22' + args['flag'])

            # 2. get
            # 2.1 Test get all sections
            output = self.cmd('config get' + args['flag']).get_output_in_json()
            self.assertListEqual(output['test_section1'], test_section1_expected)
            self.assertListEqual(output['test_section2'], test_section2_expected)

            # 2.2 Test get one section
            output = self.cmd('config get test_section1' + args['flag']).get_output_in_json()
            self.assertListEqual(output, test_section1_expected)
            output = self.cmd('config get test_section2' + args['flag']).get_output_in_json()
            self.assertListEqual(output, test_section2_expected)

            # 2.3 Test get one item
            output = self.cmd('config get test_section1.test_option1' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, test_option1_expected)
            output = self.cmd('config get test_section2.test_option21' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, test_option21_expected)
            output = self.cmd('config get test_section2.test_option22' + args['flag']).get_output_in_json()
            self.assertDictEqual(output, test_option22_expected)

            with self.assertRaises(CLIError):
                self.cmd('config get test_section1.test_option22' + args['flag'])

            # 3. unset
            # Test unsetting one option
            self.cmd('config unset test_section1.test_option1' + args['flag'])
            # Test unsetting multiple options
            self.cmd('config unset test_section2.test_option21 test_section2.test_option22' + args['flag'])

        os.chdir(original_path)


if __name__ == '__main__':
    unittest.main()
