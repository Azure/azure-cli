# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import shutil
import tempfile

from knack.util import CLIError
from azure.cli.core.local_context import AzCLILocalContext, ALL


class TestLocalContext(unittest.TestCase):

    def setUp(self):
        self.original_working_dir = os.getcwd()
        self.working_dir = tempfile.mkdtemp()
        os.chdir(self.working_dir)
        self.dir_name = '.azure'
        self.file_name = 'local_context'
        if os.path.exists(os.path.join(self.working_dir, self.dir_name, self.file_name)):
            shutil.rmtree(os.path.join(self.working_dir, self.dir_name))

        self.local_context = AzCLILocalContext(self.dir_name, self.file_name)
        self.local_context.turn_on()

    def tearDown(self):
        if self.local_context.is_on():
            self.local_context.turn_off()
        os.chdir(self.original_working_dir)

    def test_local_context(self):
        self.assertTrue(self.local_context.is_on())
        self.local_context.set([ALL], 'resource_group_name', 'test_rg')
        self.assertEqual('test_rg', self.local_context.get('vm create', 'resource_group_name'))
        with self.assertRaises(CLIError):
            self.local_context.turn_on()
        self.assertEqual(self.working_dir, self.local_context.current_turn_on_dir())


if __name__ == '__main__':
    unittest.main()
