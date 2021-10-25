# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import LocalContextScenarioTest


@unittest.skip("Conflict with ConfigTest")
class ParamPersistScenarioTest(LocalContextScenarioTest):

    def test_param_persist_commands(self):
        self.cmd('config param-persist show')
        self.cmd('config param-persist show resource_group_name vnet_name')
        self.cmd('config param-persist delete resource_group_name vnet_name')
        self.cmd('config param-persist delete --all -y')
        self.cmd('config param-persist delete --all --purge -y')
        self.cmd('config param-persist delete --all --purge -y --recursive')

        from knack.util import CLIError
        with self.assertRaises(CLIError):
            self.cmd('config param-persist delete resource_group_name --all')


if __name__ == '__main__':
    unittest.main()
