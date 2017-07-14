# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest
import shutil
import zipfile

import mock

from azure.cli.core.extension import (get_extensions, get_extension_path, extension_exists,
                                      get_extension, get_extension_names, ExtensionNotInstalledException,
                                      WheelExtension)


# The test extension name
EXT_NAME = 'myfirstcliextension'
EXT_VERSION = '0.0.3+dev'


def _get_test_data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


def _install_test_extension():  # pylint: disable=no-self-use
    # We extract the extension into place as we aren't testing install here
    zip_file = _get_test_data_file('{}.zip'.format(EXT_NAME))
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(get_extension_path(EXT_NAME))
    zip_ref.close()


class TestExtensions(unittest.TestCase):

    def setUp(self):
        self.ext_dir = tempfile.mkdtemp()
        self.patcher = mock.patch('azure.cli.core.extension.EXTENSIONS_DIR', self.ext_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.ext_dir, ignore_errors=True)

    def test_no_extensions_dir(self):
        """ Extensions directory doesn't exist """
        shutil.rmtree(self.ext_dir)
        actual = get_extensions()
        self.assertEqual(len(actual), 0)

    def test_no_extensions_in_dir(self):
        """ Directory exists but there are no extensions """
        actual = get_extensions()
        self.assertEqual(len(actual), 0)

    def test_other_files_in_extensions_dir(self):
        tempfile.mkstemp(dir=self.ext_dir)
        actual = get_extensions()
        self.assertEqual(len(actual), 0)

    def test_extension_list(self):
        _install_test_extension()
        actual = get_extensions()
        self.assertEqual(len(actual), 1)

    def test_extension_exists(self):
        _install_test_extension()
        actual = extension_exists(EXT_NAME)
        self.assertTrue(actual)

    def test_extension_not_exists(self):
        actual = extension_exists(EXT_NAME)
        self.assertFalse(actual)

    def test_extension_not_exists_2(self):
        _install_test_extension()
        actual = extension_exists('notanextension')
        self.assertFalse(actual)

    def test_get_extension(self):
        _install_test_extension()
        actual = get_extension(EXT_NAME)
        self.assertEqual(actual.name, EXT_NAME)

    def test_get_extension_not_installed(self):
        with self.assertRaises(ExtensionNotInstalledException):
            get_extension(EXT_NAME)

    def test_get_extension_names(self):
        _install_test_extension()
        actual = get_extension_names()
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0], EXT_NAME)


class TestWheelExtension(TestExtensions):

    def test_wheel_get_all(self):
        _install_test_extension()
        whl_exts = WheelExtension.get_all()
        self.assertEqual(len(whl_exts), 1)

    def test_wheel_version(self):
        _install_test_extension()
        ext = get_extension(EXT_NAME)
        self.assertEqual(ext.version, EXT_VERSION)

    def test_wheel_type(self):
        _install_test_extension()
        ext = get_extension(EXT_NAME)
        self.assertEqual(ext.ext_type, WheelExtension.EXT_TYPE)

    def test_wheel_metadata(self):
        _install_test_extension()
        ext = get_extension(EXT_NAME)
        # There should be no exceptions and metadata should have some value
        self.assertTrue(ext.metadata)


if __name__ == '__main__':
    unittest.main()
