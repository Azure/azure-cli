# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest
import shutil

import mock

from azure.cli.core.util import CLIError
from azure.cli.command_modules.extension.custom import (list_extensions, add_extension, show_extension,
                                                        remove_extension, OUT_KEY_NAME)


def _get_test_data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


MY_EXT_NAME = 'myfirstcliextension'
MY_EXT_SOURCE = _get_test_data_file('myfirstcliextension-0.0.3+dev-py2.py3-none-any.whl')
MY_BAD_EXT_SOURCE = _get_test_data_file('notanextension.txt')


class TestExtensionCommands(unittest.TestCase):

    def setUp(self):
        self.ext_dir = tempfile.mkdtemp()
        self.patcher = mock.patch('azure.cli.core.extension.EXTENSIONS_DIR', self.ext_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.ext_dir, ignore_errors=True)

    def test_no_extensions_dir(self):
        shutil.rmtree(self.ext_dir)
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_no_extensions_in_dir(self):
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_add_list_show_remove_extension(self):
        add_extension(MY_EXT_SOURCE)
        actual = list_extensions()
        self.assertEqual(len(actual), 1)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        remove_extension(MY_EXT_NAME)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 0)

    def test_add_extension_twice(self):
        add_extension(MY_EXT_SOURCE)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 1)
        with self.assertRaises(CLIError):
            add_extension(MY_EXT_SOURCE)

    def test_add_extension_invalid(self):
        with self.assertRaises(ValueError):
            add_extension(MY_BAD_EXT_SOURCE)
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_add_extension_invalid_whl_name(self):
        with self.assertRaises(CLIError):
            add_extension(os.path.join('invalid', 'ext', 'path', 'file.whl'))
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_add_extension_valid_whl_name_filenotfound(self):
        with self.assertRaises(CLIError):
            add_extension(_get_test_data_file('mywheel-0.0.3+dev-py2.py3-none-any.whl'))
        actual = list_extensions()
        self.assertEqual(len(actual), 0)


if __name__ == '__main__':
    unittest.main()
