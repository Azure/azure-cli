# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest
import shutil
import hashlib
from unittest import mock
import sys

from azure.cli.core.util import CLIError
from azure.cli.core.extension import get_extension, build_extension_path
from azure.cli.core.extension.operations import (add_extension_to_path, list_extensions, add_extension,
                                                 show_extension, remove_extension, update_extension,
                                                 list_available_extensions, OUT_KEY_NAME, OUT_KEY_VERSION,
                                                 OUT_KEY_METADATA, OUT_KEY_PATH, _run_pip)
from azure.cli.core.extension._resolve import NoExtensionCandidatesError
from azure.cli.core.mock import DummyCli

from . import IndexPatch, mock_ext


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
        self.ext_sys_dir = tempfile.mkdtemp()
        self.patchers = [mock.patch('azure.cli.core.extension.EXTENSIONS_DIR', self.ext_dir),
                         mock.patch('azure.cli.core.extension.EXTENSIONS_SYS_DIR', self.ext_sys_dir)]
        for patcher in self.patchers:
            patcher.start()
        self.cmd = self._setup_cmd()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        shutil.rmtree(self.ext_dir, ignore_errors=True)
        shutil.rmtree(self.ext_sys_dir, ignore_errors=True)

    def test_no_extensions_dir(self):
        shutil.rmtree(self.ext_dir)
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_no_extensions_in_dir(self):
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_add_list_show_remove_extension(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        actual = list_extensions()
        self.assertEqual(len(actual), 1)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        remove_extension(MY_EXT_NAME)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 0)

    def test_add_list_show_remove_system_extension(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, system=True)
        actual = list_extensions()
        self.assertEqual(len(actual), 1)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        remove_extension(MY_EXT_NAME)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 0)

    def test_add_list_show_remove_user_system_extensions(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        add_extension(cmd=self.cmd, source=MY_SECOND_EXT_SOURCE_DASHES, system=True)
        actual = list_extensions()
        self.assertEqual(len(actual), 2)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_PATH], build_extension_path(MY_EXT_NAME))
        second_ext = show_extension(MY_SECOND_EXT_NAME_DASHES)
        self.assertEqual(second_ext[OUT_KEY_NAME], MY_SECOND_EXT_NAME_DASHES)
        self.assertEqual(second_ext[OUT_KEY_PATH], build_extension_path(MY_SECOND_EXT_NAME_DASHES, system=True))
        remove_extension(MY_EXT_NAME)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 1)
        remove_extension(MY_SECOND_EXT_NAME_DASHES)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 0)

    def test_add_list_show_remove_extension_with_dashes(self):
        add_extension(cmd=self.cmd, source=MY_SECOND_EXT_SOURCE_DASHES)
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
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 1)
        with self.assertRaises(CLIError):
            add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)

    def test_add_same_extension_user_system(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 1)
        with self.assertRaises(CLIError):
            add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, system=True)

    def test_add_extension_invalid(self):
        with self.assertRaises(ValueError):
            add_extension(cmd=self.cmd, source=MY_BAD_EXT_SOURCE)
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_add_extension_invalid_whl_name(self):
        with self.assertRaises(CLIError):
            add_extension(cmd=self.cmd, source=os.path.join('invalid', 'ext', 'path', 'file.whl'))
        actual = list_extensions()
        self.assertEqual(len(actual), 0)

    def test_add_extension_valid_whl_name_filenotfound(self):
        with self.assertRaises(CLIError):
            add_extension(cmd=self.cmd, source=_get_test_data_file('mywheel-0.0.3+dev-py2.py3-none-any.whl'))
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
            add_extension(cmd=self.cmd, extension_name=extension_name, pip_proxy=proxy_endpoint)
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
            add_extension(cmd=self.cmd, extension_name=extension_name)
            args = check_output.call_args
            pip_cmd = args[0][0]
            if '--proxy' in pip_cmd:
                raise AssertionError("proxy parameter in check_output args although no proxy specified")

    def test_add_extension_with_specific_version(self):
        extension_name = MY_EXT_NAME
        extension1 = 'myfirstcliextension-0.0.3+dev-py2.py3-none-any.whl'
        extension2 = 'myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl'

        mocked_index_data = {
            extension_name: [
                mock_ext(extension1, version='0.0.3+dev', download_url=_get_test_data_file(extension1)),
                mock_ext(extension2, version='0.0.4+dev', download_url=_get_test_data_file(extension2))
            ]
        }

        with IndexPatch(mocked_index_data):
            add_extension(self.cmd, extension_name=extension_name, version='0.0.3+dev')
            ext = show_extension(extension_name)
            self.assertEqual(ext['name'], extension_name)
            self.assertEqual(ext['version'], '0.0.3+dev')

    def test_add_extension_with_non_existing_version(self):
        extension_name = MY_EXT_NAME
        extension1 = 'myfirstcliextension-0.0.3+dev-py2.py3-none-any.whl'
        extension2 = 'myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl'

        mocked_index_data = {
            extension_name: [
                mock_ext(extension1, version='0.0.3+dev', download_url=_get_test_data_file(extension1)),
                mock_ext(extension2, version='0.0.4+dev', download_url=_get_test_data_file(extension2))
            ]
        }

        non_existing_version = '0.0.5'
        with IndexPatch(mocked_index_data):
            with self.assertRaisesRegex(CLIError, non_existing_version):
                add_extension(self.cmd, extension_name=extension_name, version=non_existing_version)

    def test_add_extension_with_name_valid_checksum(self):
        extension_name = MY_EXT_NAME
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)):
            add_extension(cmd=self.cmd, extension_name=extension_name)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)

    def test_add_extension_with_name_invalid_checksum(self):
        extension_name = MY_EXT_NAME
        bad_sha256 = 'thishashisclearlywrong'
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, bad_sha256)):
            with self.assertRaises(CLIError) as err:
                add_extension(cmd=self.cmd, extension_name=extension_name)
            self.assertTrue('The checksum of the extension does not match the expected value.' in str(err.exception))

    def test_add_extension_with_name_source_not_whl(self):
        extension_name = 'myextension'
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=('{}.notwhl'.format(extension_name), None)):
            with self.assertRaises(ValueError) as err:
                add_extension(cmd=self.cmd, extension_name=extension_name)
            self.assertTrue('Unknown extension type. Only Python wheels are supported.' in str(err.exception))

    def test_add_extension_with_name_but_it_already_exists(self):
        # Add extension without name first
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
        # Now add using name
        computed_extension_sha256 = _compute_file_hash(MY_EXT_SOURCE)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)):
            with mock.patch('azure.cli.core.extension.operations.logger') as mock_logger:
                add_extension(cmd=self.cmd, extension_name=MY_EXT_NAME)
                call_args = mock_logger.warning.call_args
                self.assertEqual("Extension '%s' is already installed.", call_args[0][0])
                self.assertEqual(MY_EXT_NAME, call_args[0][1])
                self.assertEqual(mock_logger.warning.call_count, 1)

    def test_update_extension(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            update_extension(self.cmd, MY_EXT_NAME)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')

    def test_update_extension_with_pip_proxy(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
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

            update_extension(self.cmd, MY_EXT_NAME, pip_proxy=proxy_endpoint)
            args = check_output.call_args
            pip_cmd = args[0][0]
            proxy_index = pip_cmd.index(proxy_param)
            assert pip_cmd[proxy_index + 1] == proxy_endpoint

    def test_update_extension_verify_no_pip_proxy(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)

        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(MY_EXT_SOURCE, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.shutil'), \
                mock.patch('azure.cli.core.extension.operations.is_valid_sha256sum', return_value=(True, computed_extension_sha256)), \
                mock.patch('azure.cli.core.extension.operations.extension_exists', return_value=None), \
                mock.patch('azure.cli.core.extension.operations.check_output') as check_output:

            update_extension(self.cmd, MY_EXT_NAME)
            args = check_output.call_args
            pip_cmd = args[0][0]
            if '--proxy' in pip_cmd:
                raise AssertionError("proxy parameter in check_output args although no proxy specified")

    def test_update_extension_not_found(self):
        with self.assertRaises(CLIError) as err:
            update_extension(self.cmd, MY_EXT_NAME)
        self.assertEqual(str(err.exception), 'The extension {} is not installed.'.format(MY_EXT_NAME))

    def test_update_extension_no_updates(self):
        logger_msgs = []

        def mock_log_warning(_, msg):
            logger_msgs.append(msg)

        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', side_effect=NoExtensionCandidatesError()), \
                mock.patch('logging.Logger.warning', mock_log_warning):
            update_extension(self.cmd, MY_EXT_NAME)
        self.assertTrue("No updates available for '{}'.".format(MY_EXT_NAME) in logger_msgs[0])

    def test_update_extension_exception_in_update_and_rolled_back(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        bad_sha256 = 'thishashisclearlywrong'
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, bad_sha256)):
            with self.assertRaises(CLIError) as err:
                update_extension(self.cmd, MY_EXT_NAME)
            self.assertTrue('Failed to update. Rolled {} back to {}.'.format(ext['name'], ext[OUT_KEY_VERSION]) in str(err.exception))
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')

    def test_list_available_extensions_default(self):
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', autospec=True) as c:
            list_available_extensions(cli_ctx=self.cmd.cli_ctx)
            c.assert_called_once_with(None, self.cmd.cli_ctx)

    def test_list_available_extensions_operations_index_url(self):
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', autospec=True) as c:
            index_url = 'http://contoso.com'
            list_available_extensions(index_url=index_url, cli_ctx=self.cmd.cli_ctx)
            c.assert_called_once_with(index_url, self.cmd.cli_ctx)

    def test_list_available_extensions_show_details(self):
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', autospec=True) as c:
            list_available_extensions(show_details=True, cli_ctx=self.cmd.cli_ctx)
            c.assert_called_once_with(None, self.cmd.cli_ctx)

    def test_list_available_extensions_no_show_details(self):
        sample_index_extensions = {
            'test_sample_extension1': [{
                'metadata': {
                    'name': 'test_sample_extension1',
                    'summary': 'my summary',
                    'version': '0.1.0'
                }}],
            'test_sample_extension2': [{
                'metadata': {
                    'name': 'test_sample_extension2',
                    'summary': 'my summary',
                    'version': '0.1.0',
                    'azext.isPreview': True,
                    'azext.isExperimental': True
                }}]
        }
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', return_value=sample_index_extensions):
            res = list_available_extensions(cli_ctx=self.cmd.cli_ctx)
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), len(sample_index_extensions))
            self.assertEqual(res[0]['name'], 'test_sample_extension1')
            self.assertEqual(res[0]['summary'], 'my summary')
            self.assertEqual(res[0]['version'], '0.1.0')
            self.assertEqual(res[0]['preview'], False)
            self.assertEqual(res[0]['experimental'], False)
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions', return_value=sample_index_extensions):
            res = list_available_extensions(cli_ctx=self.cmd.cli_ctx)
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), len(sample_index_extensions))
            self.assertEqual(res[1]['name'], 'test_sample_extension2')
            self.assertEqual(res[1]['summary'], 'my summary')
            self.assertEqual(res[1]['version'], '0.1.0')
            self.assertEqual(res[1]['preview'], True)
            self.assertEqual(res[1]['experimental'], True)

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
            res = list_available_extensions(cli_ctx=self.cmd.cli_ctx)
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), 0)

    def test_add_extension_install_setup_extras(self):
        """
        Tests extension addition while specifying --install-setup-extras parameter.
        :return:
        """
        setup_extras = ['BAR', 'FOO']

        # Without mocking extension should not be added
        with self.assertRaises(CLIError):
            add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, install_setup_extras=setup_extras)

        # Mock so the first extension is valid. Extension will still not be added
        with mock.patch("azure.cli.core.extension.operations.WheelExtension.get_metadata_extras", return_value=setup_extras[:1]), \
                self.assertRaises(CLIError):
            add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, install_setup_extras=setup_extras)

        # Mock so the both extensions are valid. Extension will be added
        with mock.patch("azure.cli.core.extension.operations.WheelExtension.get_metadata_extras", return_value=setup_extras[:]), \
                mock.patch("azure.cli.core.extension.operations._run_pip", wraps=_run_pip) as check_output:
            add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, install_setup_extras=setup_extras)
            pip_file = check_output.call_args[0][0][3]
            assert pip_file.endswith('[BAR,FOO]')

            actual = list_extensions()
            self.assertEqual(len(actual), 1)
            ext = show_extension(MY_EXT_NAME)
            self.assertEqual(ext[OUT_KEY_NAME], MY_EXT_NAME)
            remove_extension(MY_EXT_NAME)
            num_exts = len(list_extensions())
            self.assertEqual(num_exts, 0)

    def test_update_extension_install_setup_extras(self):
        """
        Tests extension update while specifying --install-setup-extras parameter.
        :return:
        """
        setup_extras = ['BAR', 'FOO']

        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)

        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            # Without mocking extension should not be added
            with self.assertRaises(CLIError):
                update_extension(self.cmd, MY_EXT_NAME, install_setup_extras=setup_extras)

            # Mock so the first extension is valid. Extension will still not be added
            with mock.patch("azure.cli.core.extension.operations.WheelExtension.get_metadata_extras", return_value=setup_extras[:1]), \
                    self.assertRaises(CLIError):
                update_extension(self.cmd, MY_EXT_NAME, install_setup_extras=setup_extras)

            # Mock so the both extensions are valid. Extension will be added
            with mock.patch("azure.cli.core.extension.operations.WheelExtension.get_metadata_extras", return_value=setup_extras[:]), \
                    mock.patch("azure.cli.core.extension.operations._run_pip", wraps=_run_pip) as check_output:
                update_extension(self.cmd, MY_EXT_NAME, install_setup_extras=setup_extras)
                pip_file = check_output.call_args[0][0][3]
                assert pip_file.endswith('[BAR,FOO]')
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')

    def test_add_list_show_remove_extension_extra_index_url(self):
        """
        Tests extension addition while specifying --extra-index-url parameter.
        :return:
        """
        extra_index_urls = ['https://testpypi.python.org/simple', 'https://pypi.python.org/simple']

        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, pip_extra_index_urls=extra_index_urls)
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

        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE, pip_extra_index_urls=extra_index_urls)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.3+dev')
        newer_extension = _get_test_data_file('myfirstcliextension-0.0.4+dev-py2.py3-none-any.whl')
        computed_extension_sha256 = _compute_file_hash(newer_extension)
        with mock.patch('azure.cli.core.extension.operations.resolve_from_index', return_value=(newer_extension, computed_extension_sha256)):
            update_extension(self.cmd, MY_EXT_NAME, pip_extra_index_urls=extra_index_urls)
        ext = show_extension(MY_EXT_NAME)
        self.assertEqual(ext[OUT_KEY_VERSION], '0.0.4+dev')

    def test_add_extension_to_path(self):
        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        num_exts = len(list_extensions())
        self.assertEqual(num_exts, 1)
        ext = get_extension('myfirstcliextension')
        old_path = sys.path[:]
        try:
            add_extension_to_path(ext.name)
            self.assertSequenceEqual(old_path, sys.path[:-1])
            self.assertEqual(ext.path, sys.path[-1])
        finally:
            sys.path[:] = old_path

    def test_add_extension_azure_to_path(self):
        import azure
        import azure.mgmt
        old_path_0 = list(sys.path)
        old_path_1 = list(azure.__path__)
        old_path_2 = list(azure.mgmt.__path__)

        add_extension(cmd=self.cmd, source=MY_EXT_SOURCE)
        ext = get_extension('myfirstcliextension')
        azure_dir = os.path.join(ext.path, "azure")
        azure_mgmt_dir = os.path.join(azure_dir, "mgmt")
        os.mkdir(azure_dir)
        os.mkdir(azure_mgmt_dir)

        try:
            add_extension_to_path(ext.name)
            new_path_1 = list(azure.__path__)
            new_path_2 = list(azure.mgmt.__path__)
        finally:
            sys.path.remove(ext.path)
            remove_extension(ext.name)
            if isinstance(azure.__path__, list):
                azure.__path__[:] = old_path_1
            else:
                list(azure.__path__)
            if isinstance(azure.mgmt.__path__, list):
                azure.mgmt.__path__[:] = old_path_2
            else:
                list(azure.mgmt.__path__)
        self.assertSequenceEqual(old_path_1, new_path_1[:-1])
        self.assertSequenceEqual(old_path_2, new_path_2[:-1])
        self.assertEqual(azure_dir, new_path_1[-1])
        self.assertEqual(azure_mgmt_dir, new_path_2[-1])
        self.assertSequenceEqual(old_path_0, list(sys.path))
        self.assertSequenceEqual(old_path_1, list(azure.__path__))
        self.assertSequenceEqual(old_path_2, list(azure.mgmt.__path__))

    def _setup_cmd(self):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        return cmd


if __name__ == '__main__':
    unittest.main()
