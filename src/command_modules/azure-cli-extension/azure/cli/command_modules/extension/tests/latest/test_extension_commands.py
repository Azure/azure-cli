# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest
import shutil
import hashlib
import mock

from azure.cli.core.util import CLIError
from azure.cli.command_modules.extension.custom import (list_extensions, add_extension, show_extension,
                                                        remove_extension, update_extension,
                                                        list_available_extensions, OUT_KEY_NAME, OUT_KEY_VERSION, OUT_KEY_METADATA)
from azure.cli.command_modules.extension._resolve import NoExtensionCandidatesError


def _get_test_data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


def _compute_file_hash(filename):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


MY_EXT_NAME = 'myfirstcliextension'
MY_EXT_SOURCE = _get_test_data_file('myfirstcliextension-0.0.3+dev-py2.py3-none-any.whl')
MY_BAD_EXT_SOURCE = _get_test_data_file('notanextension.txt')
MY_SECOND_EXT_NAME_DASHES = 'my-second-cli-extension'
MY_SECOND_EXT_SOURCE_DASHES = _get_test_data_file('my_second_cli_extension-0.0.1+dev-py2.py3-none-any.whl')


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

    def test_add_list_show_remove_extension_with_dashes(self):
        add_extension(MY_SECOND_EXT_SOURCE_DASHES)
        actual = list_extensions()
        self.assertEqual(len(actual), 1)
        ext = show_extension(MY_SECOND_EXT_NAME_DASHES)
        self.assertEqual(ext[OUT_KEY_NAME], MY_SECOND_EXT_NAME_DASHES)
        self.assertIn(OUT_KEY_NAME, ext[OUT_KEY_METADATA], "Unable to get full metadata")
        self.assertEqual(ext[OUT_KEY_METADATA][OUT_KEY_NAME], MY_SECOND_EXT_NAME_DASHES)
        remove_extension(MY_SECOND_EXT_NAME_DASHES)
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

    def test_add_extension_with_name_valid_checksum(self):
        extension_name = 'myfirstcliextension'
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)):
            add_extension(extension_name=extension_name)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)

    def test_add_extension_with_name_invalid_checksum(self):
        extension_name = 'myfirstcliextension'
        bad_sha256 = 'thishashisclearlywrong'
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=(MY_EXT_SOURCE, bad_sha256)):
            with self.assertRaises(CLIError) as err:
                add_extension(extension_name=extension_name)
            self.assertTrue('The checksum of the extension does not match the expected value.' in str(err.exception))

    def test_add_extension_with_name_source_not_whl(self):
        extension_name = 'myextension'
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=('{}.notwhl'.format(extension_name), None)):
            with self.assertRaises(ValueError) as err:
                add_extension(extension_name=extension_name)
            self.assertTrue('Unknown extension type. Only Python wheels are supported.' in str(err.exception))

    def test_add_extension_with_name_but_it_already_exists(self):
        # Add extension without name first
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        # Now add using name
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)):
            with self.assertRaises(CLIError) as err:
                add_extension(extension_name=MY_EXT_NAME)
            self.assertTrue('The extension {} already exists.'.format(MY_EXT_NAME) in str(err.exception))

    def test_update_extension(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            update_extension(MY_EXT_NAME)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')

    def test_update_extension_not_found(self):
        with self.assertRaises(CLIError) as err:
            update_extension(MY_EXT_NAME)
        self.assertEqual(str(err.exception), 'The extension {} is not installed.'.format(MY_EXT_NAME))

    def test_update_extension_no_updates(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', side_effect=NoExtensionCandidatesError()):
            with self.assertRaises(CLIError) as err:
                update_extension(MY_EXT_NAME)
            self.assertTrue("No updates available for '{}'.".format(MY_EXT_NAME) in str(err.exception))

    def test_update_extension_exception_in_update_and_rolled_back(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        bad_sha256 = 'thishashisclearlywrong'
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=(newer_extension, bad_sha256)):
            with self.assertRaises(CLIError) as err:
                update_extension(MY_EXT_NAME)
            self.assertTrue('Failed to update. Rolled {} back to {}.'.format(ext['name'], ext[OUT_KEY_VERSION]) in str(err.exception))
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')

    def test_list_available_extensions_default(self):
        with mock.patch('azure.cli.command_modules.extension.custom.get_index_extensions', autospec=True) as c:
            list_available_extensions()
            c.assert_called_once_with(None)

    def test_list_available_extensions_custom_index_url(self):
        with mock.patch('azure.cli.command_modules.extension.custom.get_index_extensions', autospec=True) as c:
            index_url = 'http://contoso.com'
            list_available_extensions(index_url=index_url)
            c.assert_called_once_with(index_url)

    def test_add_list_show_remove_extension_extra_index_url(self):
        """
        Tests extension addition while specifying --extra-index-url parameter.
        :return:
        """
        test_index = 'https://testpypi.python.org/simple'

        add_extension(source=MY_EXT_SOURCE, extra_index_urls=[test_index])
        actual = list_extensions()
        self.assertEqual(len(actual), 1)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        remove_extension(MY_EXT_NAME)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 0)

    def test_update_extension_extra_index_url(self):
        """
        Tests extension update while specifying --extra-index-url parameter.
        :return:
        """
        test_index = 'https://testpypi.python.org/simple'
        add_extension(source=MY_EXT_SOURCE, extra_index_urls=[test_index])
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)
        with mock.patch('azure.cli.command_modules.extension.custom.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            update_extension(MY_EXT_NAME, extra_index_urls=[test_index])
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')


if __name__ == '__main__':
    unittest.main()
