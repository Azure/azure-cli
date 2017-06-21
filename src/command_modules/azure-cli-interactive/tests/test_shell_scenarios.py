# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import tempfile
import os
import unittest

import azclishell._dump_commands as dump


class DumpCommandsTest(unittest.TestCase):
    """ tests whether dump commands works """
    def __init__(self, *args, **kwargs):
        super(DumpCommandsTest, self).__init__(*args, **kwargs)
        self.config_dir = tempfile.mkdtemp()

        self.path = os.path.join(
            os.path.expanduser(os.path.join('~', '.azure-shell')),
            'cache')
        self.command_file_name = 'help_dump.json'

    def test_install_modules(self):
        """ tests the running """
        dump.install_modules()

    def test_cache_dir(self):
        """ tests the cache dir is in the right place """
        path = dump.get_cache_dir()
        self.assertEqual(path, self.path)

    def test_dump_commands(self):
        """ tests dumping the command table"""
        dump.dump_command_table()
        self.assertTrue(os.path.exists(os.path.join(self.path, self.command_file_name)))


if __name__ == '__main__':
    unittest.main()
