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
from azure.cli.core.extension.operations import (list_extensions, add_extension, show_extension,
                                                 remove_extension, update_extension,
                                                 list_available_extensions, OUT_KEY_NAME, OUT_KEY_VERSION, OUT_KEY_METADATA)
from azure.cli.core.extension._resolve import NoExtensionCandidatesError


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

    def test_add_extension_with_pip_proxy(self):
        extension_name = MY_EXT_NAME
        proxy_param = '--proxy'
        proxy_endpoint = "https://user:pass@proxy.microsoft.com"
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.shutil'), \
                mock.patch('azure.cli.core.extension.operations.check_output') as check_output:
            add_extension(extension_name=extension_name, pip_proxy=proxy_endpoint)
            args = check_output.call_args
            pip_cmd = args[0][0]
            proxy_index = pip_cmd.index(proxy_param)
            assert pip_cmd[proxy_index + 1] == proxy_endpoint

    def test_add_extension_verify_no_pip_proxy(self):
        extension_name = MY_EXT_NAME
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.shutil'), \
                mock.patch('azure.cli.core.extension.operations.check_output') as check_output:
            add_extension(extension_name=extension_name)
            args = check_output.call_args
            pip_cmd = args[0][0]
            if '--proxy' in pip_cmd:
                raise AssertionError("proxy parameter in check_output args although no proxy specified")

    def test_add_extension_with_name_valid_checksum(self):
        extension_name = MY_EXT_NAME
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)):
            add_extension(extension_name=extension_name)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)

    def test_add_extension_with_name_invalid_checksum(self):
        extension_name = MY_EXT_NAME
        bad_sha256 = 'thishashisclearlywrong'
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, bad_sha256)):
            with self.assertRaises(CLIError) as err:
                add_extension(extension_name=extension_name)
            self.assertTrue('The checksum of the extension does not match the expected value.' in str(err.exception))

    def test_add_extension_with_name_source_not_whl(self):
        extension_name = 'myextension'
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=('{}.notwhl'.format(extension_name), None)):
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
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)):
            with mock.patch('azure.cli.core.extension.operations.logger') as mock_logger:
                add_extension(extension_name=MY_EXT_NAME)
                call_args = mock_logger.warning.call_args
                self.assertEqual("The extension '%s' already exists.", call_args[0][0])
                self.assertEqual(MY_EXT_NAME, call_args[0][1])
                self.assertEqual(mock_logger.warning.call_count, 1)

    def test_update_extension(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            update_extension(MY_EXT_NAME)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')

    def test_update_extension_with_pip_proxy(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)

        proxy_param = '--proxy'
        proxy_endpoint = "https://user:pass@proxy.microsoft.com"
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.shutil'), \
                mock.patch('azure.cli.core.extension.operations.is_valid_sha256sum', return_value=(True, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.extension_exists', return_value=None), \
                mock.patch('azure.cli.core.extension.operations.check_output') as check_output:

            update_extension(MY_EXT_NAME, pip_proxy=proxy_endpoint)
            args = check_output.call_args
            pip_cmd = args[0][0]
            proxy_index = pip_cmd.index(proxy_param)
            assert pip_cmd[proxy_index + 1] == proxy_endpoint

    def test_update_extension_verify_no_pip_proxy(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)

        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.shutil'), \
                mock.patch('azure.cli.core.extension.operations.is_valid_sha256sum', return_value=(True, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.extension_exists', return_value=None), \
                mock.patch('azure.cli.core.extension.operations.check_output') as check_output:

            update_extension(MY_EXT_NAME)
            args = check_output.call_args
            pip_cmd = args[0][0]
            if '--proxy' in pip_cmd:
                raise AssertionError("proxy parameter in check_output args although no proxy specified")

    def test_update_extension_not_found(self):
        with self.assertRaises(CLIError) as err:
            update_extension(MY_EXT_NAME)
        self.assertEqual(str(err.exception), 'The extension {} is not installed.'.format(MY_EXT_NAME))

    def test_update_extension_no_updates(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', side_effect=NoExtensionCandidatesError()):
            with self.assertRaises(CLIError) as err:
                update_extension(MY_EXT_NAME)
            self.assertTrue("No updates available for '{}'.".format(MY_EXT_NAME) in str(err.exception))

    def test_update_extension_exception_in_update_and_rolled_back(self):
        add_extension(source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        bad_sha256 = 'thishashisclearlywrong'
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, bad_sha256)):
            with self.assertRaises(CLIError) as err:
                update_extension(MY_EXT_NAME)
            self.assertTrue('Failed to update. Rolled {} back to {}.'.format(ext['name'], ext[OUT_KEY_VERSION]) in str(err.exception))
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')

    def test_list_available_extensions_default(self):
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', autospec=True) as c:
            list_available_extensions()
            c.assert_called_once_with(None)

    def test_list_available_extensions_operations_index_url(self):
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', autospec=True) as c:
            index_url = 'http://contoso.com'
            list_available_extensions(index_url=index_url)
            c.assert_called_once_with(index_url)

    def test_list_available_extensions_show_details(self):
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', autospec=True) as c:
            list_available_extensions(show_details=True)
            c.assert_called_once_with(None)

    def test_list_available_extensions_no_show_details(self):
        sample_index_extensions = {
            'test_sample_extension1': [{
                'metadata': {
                    'name': 'test_sample_extension1',
                    'summary': 'my summary',
                    'version': '0.1.0'
                }}]
        }
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', return_value=sample_index_extensions):
            res = list_available_extensions()
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), len(sample_index_extensions))
            self.assertEqual(res[0]['name'], 'test_sample_extension1')
            self.assertEqual(res[0]['summary'], 'my summary')
            self.assertEqual(res[0]['version'], '0.1.0')
            self.assertEqual(res[0]['preview'], False)

    def test_list_available_extensions_incompatible_cli_version(self):
        sample_index_extensions = {
            'test_sample_extension1': [{
                'metadata': {
                    "azext.maxCliCoreVersion": "0.0.0",
                    'name': 'test_sample_extension1',
                    'summary': 'my summary',
                    'version': '0.1.0'
                }}]
        }
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', return_value=sample_index_extensions):
            res = list_available_extensions()
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), 0)

    def test_add_list_show_remove_extension_extra_index_url(self):
        """
        Tests extension addition while specifying --extra-index-url parameter.
        :return:
        """
        extra_index_urls = ['https://testpypi.python.org/simple', 'https://pypi.python.org/simple']

        add_extension(source=MY_EXT_SOURCE, pip_extra_index_urls=extra_index_urls)
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
        extra_index_urls = ['https://testpypi.python.org/simple', 'https://pypi.python.org/simple']

        add_extension(source=MY_EXT_SOURCE, pip_extra_index_urls=extra_index_urls)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            update_extension(MY_EXT_NAME, pip_extra_index_urls=extra_index_urls)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')


if __name__ == '__main__':
    unittest.main()
