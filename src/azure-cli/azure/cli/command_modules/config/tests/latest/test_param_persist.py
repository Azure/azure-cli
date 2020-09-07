# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import LocalContextScenarioTest


class ParamPersistScenarioTest(LocalContextScenarioTest):

    def test_param_persist_commands(self):
        self.cmd('config parampersist show')
        self.cmd('config parampersist show resource_group_name vnet_name')
        self.cmd('config parampersist delete resource_group_name vnet_name')
        self.cmd('config parampersist delete --all -y')
        self.cmd('config parampersist delete --all --purge -y')
        self.cmd('config parampersist delete --all --purge -y --recursive')

        from knack.util import CLIError
        with self.assertRaises(CLIError):
            self.cmd('config parampersist delete resource_group_name --all')


if __name__ == '__main__':
    unittest.main()
