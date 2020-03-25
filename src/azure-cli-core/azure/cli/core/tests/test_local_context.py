# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import shutil

from knack.util import CLIError
from azure.cli.core.local_context import AzCLILocalContext, GLOBAL


class TestLocalContext(unittest.TestCase):

    def setUp(self):
        self.dir_name = '.azure'
        self.file_name = 'local_context'
        if os.path.exists(os.path.join(os.getcwd(), self.dir_name, self.file_name)):
            shutil.rmtree(os.path.join(os.getcwd(), self.dir_name))

        self.local_context = AzCLILocalContext(self.dir_name, self.file_name)
        self.local_context.turn_on()
        self.local_context._load_file_chain()

    def tearDown(self):
        if self.local_context.is_on():
            self.local_context.turn_off()

    def test_local_context(self):
        self.assertTrue(self.local_context.is_on())
        self.local_context.set([GLOBAL], 'resource_group_name', 'test_rg')
        self.assertEqual('test_rg', self.local_context.get('vm create', 'resource_group_name'))
        with self.assertRaises(CLIError):
            self.local_context.turn_on()
        current_path = os.getcwd()
        self.assertEqual(current_path, self.local_context.first_dir_path())


if __name__ == '__main__':
    unittest.main()
