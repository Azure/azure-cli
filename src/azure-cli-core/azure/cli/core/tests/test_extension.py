# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import unittest
import shutil
import zipfile

from unittest import mock
from azure.cli.core.mock import DummyCli

from azure.cli.core.extension import (get_extensions, build_extension_path, extension_exists,
                                      get_extension, get_extension_names, get_extension_modname, ext_compat_with_cli,
                                      ExtensionNotInstalledException, WheelExtension,
                                      EXTENSIONS_MOD_PREFIX, EXT_METADATA_MINCLICOREVERSION, EXT_METADATA_MAXCLICOREVERSION)

from azure.cli.core.extension.operations import list_available_extensions, add_extension, show_extension, remove_extension, list_extensions, update_extension

# The test extension name
EXT_NAME = 'myfirstcliextension'
EXT_VERSION = '0.0.3+dev'
SECOND_EXT_NAME = 'my_second_cli_extension'


def _get_test_data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


def _install_test_extension1(system=None):  # pylint: disable=no-self-use
    # We extract the extension into place as we aren't testing install here
    zip_file = _get_test_data_file('{}.zip'.format(EXT_NAME))
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(build_extension_path(EXT_NAME, system=system))
    zip_ref.close()


def _install_test_extension2(system=None):  # pylint: disable=no-self-use
    # We extract the extension into place as we aren't testing install here
    zip_file = _get_test_data_file('myfirstcliextension_az_extmetadata.zip')
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(build_extension_path(EXT_NAME, system=system))
    zip_ref.close()


def _install_test_extension3(system=None):  # pylint: disable=no-self-use
    # We extract the extension into place as we aren't testing install here
    zip_file = _get_test_data_file('{}.zip'.format(SECOND_EXT_NAME))
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(build_extension_path(SECOND_EXT_NAME, system=system))
    zip_ref.close()


def mock_ext(filename, version=None, download_url=None, digest=None, project_url=None, name=None, min_cli_version=None, max_cli_version=None):
    d = {
        'filename': filename,
        'metadata': {
            'name': name,
            'version': version,
            'extensions': {
                'python.details': {
                    'project_urls': {
                        'Home': project_url or 'https://github.com/azure/some-extension'
                    }
                }
            },
            EXT_METADATA_MINCLICOREVERSION: min_cli_version,
            EXT_METADATA_MAXCLICOREVERSION: max_cli_version,
        },
        'downloadUrl': download_url or 'http://contoso.com/{}'.format(filename),
        'sha256Digest': digest
    }
    return d


class TestExtensionsBase(unittest.TestCase):

    def setUp(self):
        self.ext_dir = tempfile.mkdtemp()
        self.ext_sys_dir = tempfile.mkdtemp()
        self.patchers = [mock.patch('azure.cli.core.extension.EXTENSIONS_DIR', self.ext_dir),
                         mock.patch('azure.cli.core.extension.EXTENSIONS_SYS_DIR', self.ext_sys_dir)]
        for patcher in self.patchers:
            patcher.start()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        self.cmd = cmd

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        shutil.rmtree(self.ext_dir, ignore_errors=True)
        shutil.rmtree(self.ext_sys_dir, ignore_errors=True)


class TestExtensions(TestExtensionsBase):

    def test_no_extensions_dir(self):
        """ Extensions directory doesn't exist """
        shutil.rmtree(self.ext_dir)
        actual = get_extensions(ext_type=WheelExtension)
        self.assertEqual(len(actual), 0)

    def test_no_extensions_in_dir(self):
        """ Directory exists but there are no extensions """
        actual = get_extensions(ext_type=WheelExtension)
        self.assertEqual(len(actual), 0)

    def test_other_files_in_extensions_dir(self):
        tempfile.mkstemp(dir=self.ext_dir)
        actual = get_extensions(ext_type=WheelExtension)
        self.assertEqual(len(actual), 0)

    def test_extension_list(self):
        _install_test_extension1()
        actual = get_extensions(ext_type=WheelExtension)
        self.assertEqual(len(actual), 1)

    def test_extension_exists(self):
        _install_test_extension1()
        actual = extension_exists(EXT_NAME, ext_type=WheelExtension)
        self.assertTrue(actual)

    def test_extension_not_exists(self):
        actual = extension_exists(EXT_NAME, ext_type=WheelExtension)
        self.assertFalse(actual)

    def test_extension_not_exists_2(self):
        _install_test_extension1()
        actual = extension_exists('notanextension', ext_type=WheelExtension)
        self.assertFalse(actual)

    def test_get_extension(self):
        _install_test_extension1()
        actual = get_extension(EXT_NAME, ext_type=WheelExtension)
        self.assertEqual(actual.name, EXT_NAME)

    def test_get_extension_not_installed(self):
        with self.assertRaises(ExtensionNotInstalledException):
            get_extension(EXT_NAME, ext_type=WheelExtension)

    def test_get_extension_names(self):
        _install_test_extension1()
        actual = get_extension_names(ext_type=WheelExtension)
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0], EXT_NAME)

    def test_get_extension_modname_no_mods_with_prefix(self):
        tmp_dir = tempfile.mkdtemp()
        with self.assertRaises(AssertionError):
            get_extension_modname(ext_dir=tmp_dir)

    def test_get_extension_modname_okay(self):
        tmp_dir = tempfile.mkdtemp()
        expected_modname = EXTENSIONS_MOD_PREFIX + 'helloworldmod'
        os.makedirs(os.path.join(tmp_dir, expected_modname))
        actual_modname = get_extension_modname(ext_dir=tmp_dir)
        self.assertEqual(expected_modname, actual_modname)

    def test_get_extension_modname_too_many_mods_with_prefix(self):
        tmp_dir = tempfile.mkdtemp()
        modname1 = EXTENSIONS_MOD_PREFIX + 'helloworldmod1'
        modname2 = EXTENSIONS_MOD_PREFIX + 'helloworldmod2'
        os.makedirs(os.path.join(tmp_dir, modname1))
        os.makedirs(os.path.join(tmp_dir, modname2))
        with self.assertRaises(AssertionError):
            get_extension_modname(ext_dir=tmp_dir)

    def test_get_extension_modname_file_with_prefix(self):
        # We should only file a module if it's a directory and not a file even if it has the prefix
        tmp_dir = tempfile.mkdtemp()
        filename = EXTENSIONS_MOD_PREFIX + 'helloworld'
        open(os.path.join(tmp_dir, filename), 'a').close()
        with self.assertRaises(AssertionError):
            get_extension_modname(ext_dir=tmp_dir)

    def test_ext_compat_with_cli_no_v_constraint(self):
        # An extension that does not specify any version constraint on the CLI
        expected_cli_version = '0.0.1'
        azext_metadata = None
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, cli_version, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertTrue(is_compatible)
            self.assertEqual(cli_version, expected_cli_version)

    def test_ext_compat_with_cli_single_v_constraint(self):
        # An extension that only works with a specific version of the CLI
        expected_cli_version = '0.0.1'
        expected_min_required = '0.0.1'
        expected_max_required = '0.0.1'
        azext_metadata = {EXT_METADATA_MINCLICOREVERSION: expected_min_required,
                          EXT_METADATA_MAXCLICOREVERSION: expected_max_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, cli_version, min_required, max_required, _ = ext_compat_with_cli(azext_metadata)
            self.assertTrue(is_compatible)
            self.assertEqual(cli_version, expected_cli_version)
            self.assertEqual(min_required, expected_min_required)
            self.assertEqual(max_required, expected_max_required)

    def test_ext_compat_with_cli_only_min_v_constraint(self):
        expected_cli_version = '0.0.5'
        expected_min_required = '0.0.1'
        azext_metadata = {EXT_METADATA_MINCLICOREVERSION: expected_min_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, _, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertTrue(is_compatible)

    def test_ext_compat_with_cli_failed_bad_min_v_constraint(self):
        expected_cli_version = '0.0.5'
        expected_min_required = '0.0.7'
        azext_metadata = {EXT_METADATA_MINCLICOREVERSION: expected_min_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, _, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertFalse(is_compatible)

    def test_ext_compat_with_cli_failed_bad_min_but_close_v_constraint(self):
        expected_cli_version = '0.0.5'
        expected_min_required = '0.0.5+dev'
        azext_metadata = {EXT_METADATA_MINCLICOREVERSION: expected_min_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, _, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertFalse(is_compatible)

    def test_ext_compat_with_cli_only_max_v_constraint(self):
        expected_cli_version = '0.0.5'
        expected_max_required = '0.0.10'
        azext_metadata = {EXT_METADATA_MAXCLICOREVERSION: expected_max_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, _, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertTrue(is_compatible)

    def test_ext_compat_with_cli_failed_bad_max_v_constraint(self):
        expected_cli_version = '0.0.5'
        expected_max_required = '0.0.3'
        azext_metadata = {EXT_METADATA_MAXCLICOREVERSION: expected_max_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, _, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertFalse(is_compatible)

    def test_ext_compat_with_cli_failed_bad_max_but_close_v_constraint(self):
        expected_cli_version = '0.0.5'
        expected_max_required = '0.0.5b1'
        azext_metadata = {EXT_METADATA_MAXCLICOREVERSION: expected_max_required}
        with mock.patch('azure.cli.core.__version__', expected_cli_version):
            is_compatible, _, _, _, _ = ext_compat_with_cli(azext_metadata)
            self.assertFalse(is_compatible)

    def test_ext_compat_with_cli_require_ext_min_version(self):
        expected_cli_version = '0.0.5'
        expected_min_ext_required = '0.2.0'
        azext_metadata = {'name': 'myext', 'version': '0.1.0'}
        with mock.patch('azure.cli.core.__version__', expected_cli_version), \
            mock.patch('azure.cli.core.extension.EXTENSION_VERSION_REQUIREMENTS',
                       {'myext': {'minExtVersion': expected_min_ext_required}}):
            is_compatible, _, _, _, min_ext_required = ext_compat_with_cli(azext_metadata)
            self.assertFalse(is_compatible)
            self.assertEqual(min_ext_required, expected_min_ext_required)

    def test_list_available_extensions_preview_details(self):
        sample_index_extensions = {
            'ml': [{
                'metadata': {
                    'name': 'ml',
                    'summary': 'AzureMachineLearningWorkspaces Extension',
                    'version': '2.0.0a1',
                    'azext.isExperimental': True
                }
            }],
            'test_sample_extension1': [{
                'metadata': {
                    'name': 'test_sample_extension1',
                    'summary': 'my summary',
                    'version': '1.15.0',
                    'azext.isPreview': True,
                }
            }],
            'test_sample_extension2': [{
                'metadata': {
                    'name': 'test_sample_extension2',
                    'summary': 'my summary',
                    'version': '1.1.0b1'
                }
            }],
            'test_sample_extension3': [{
                'metadata': {
                    'name': 'test_sample_extension3',
                    'summary': 'my summary',
                    'version': '2.15.0'
                }
            }]
        }
        with mock.patch('azure.cli.core.extension.operations.get_index_extensions',
                        return_value=sample_index_extensions):
            res = list_available_extensions(cli_ctx=self.cmd.cli_ctx)
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), len(sample_index_extensions))
            self.assertEqual(res[0]['name'], 'ml')
            self.assertEqual(res[0]['summary'], 'AzureMachineLearningWorkspaces Extension')
            self.assertEqual(res[0]['version'], '2.0.0a1')
            self.assertEqual(res[0]['preview'], True)
            self.assertEqual(res[0]['experimental'], False)
            self.assertEqual(res[1]['name'], 'test_sample_extension1')
            self.assertEqual(res[1]['version'], '1.15.0')
            self.assertEqual(res[1]['preview'], True)
            self.assertEqual(res[2]['name'], 'test_sample_extension2')
            self.assertEqual(res[2]['version'], '1.1.0b1')
            self.assertEqual(res[2]['preview'], True)
            self.assertEqual(res[3]['name'], 'test_sample_extension3')
            self.assertEqual(res[3]['version'], '2.15.0')
            self.assertEqual(res[3]['preview'], False)

    def test_add_list_show_preview_extension(self):
        test_ext_source = _get_test_data_file('ml-2.0.0a1-py3-none-any.whl')
        with mock.patch('azure.cli.core.extension.operations.logger') as mock_logger:
            add_extension(cmd=self.cmd, source=test_ext_source, allow_preview=True)
            call_args = mock_logger.warning.call_args
            self.assertEqual("The installed extension '%s' is in preview.", call_args[0][0])
            self.assertEqual("ml", call_args[0][1])
            self.assertEqual(mock_logger.warning.call_count, 1)
        ext = show_extension("ml")
        self.assertEqual(ext["name"], "ml")
        self.assertEqual(ext["version"], "2.0.0a1")
        remove_extension("ml")

    def test_add_preview_extension_by_default(self):
        test_ext_source = _get_test_data_file('extension_test_pkg-1.2.3-py3-none-any.whl')
        with mock.patch('azure.cli.core.extension.operations.logger') as mock_logger:
            add_extension(cmd=self.cmd, source=test_ext_source)
        ext = show_extension("extension-test-pkg")
        self.assertEqual(ext["name"], "extension-test-pkg")
        self.assertEqual(ext["version"], "1.2.3")
        remove_extension("extension-test-pkg")

    def test_add_extension_without_preview(self):
        extension_name = "extension-test-pkg"
        extension1 = 'extension_test_pkg-1.0.0b1-py3-none-any.whl'
        extension2 = 'extension_test_pkg-1.2.3-py3-none-any.whl'
        extension3 = 'extension_test_pkg-1.4.1a1-py3-none-any.whl'

        mocked_index_data = {
            extension_name: [
                mock_ext(extension1, version='1.0.0b1', download_url=_get_test_data_file(extension1)),
                mock_ext(extension2, version='1.2.3', download_url=_get_test_data_file(extension2)),
                mock_ext(extension3, version='1.4.1a1', download_url=_get_test_data_file(extension3))
            ]
        }
        with mock.patch('azure.cli.core.extension._resolve.get_index_extensions',
                        return_value=mocked_index_data):
            add_extension(self.cmd, extension_name=extension_name, allow_preview=False)
            ext = show_extension(extension_name)
            self.assertEqual(ext['name'], extension_name)
            self.assertEqual(ext['version'], '1.2.3')
            remove_extension(extension_name)

    def test_add_extension_with_preview(self):
        extension_name = "extension-test-pkg"
        extension1 = 'extension_test_pkg-1.0.0b1-py3-none-any.whl'
        extension2 = 'extension_test_pkg-1.2.3-py3-none-any.whl'
        extension3 = 'extension_test_pkg-1.4.1a1-py3-none-any.whl'

        mocked_index_data = {
            extension_name: [
                mock_ext(extension1, version='1.0.0b1', download_url=_get_test_data_file(extension1)),
                mock_ext(extension2, version='1.2.3', download_url=_get_test_data_file(extension2)),
                mock_ext(extension3, version='1.4.1a1', download_url=_get_test_data_file(extension3))
            ]
        }

        with mock.patch('azure.cli.core.extension._resolve.get_index_extensions',
                        return_value=mocked_index_data):
            add_extension(self.cmd, extension_name=extension_name, allow_preview=True)
            ext = show_extension(extension_name)
            self.assertEqual(ext['name'], extension_name)
            self.assertEqual(ext['version'], '1.4.1a1')
            remove_extension(extension_name)

    @unittest.skip("No break in preview only modules")
    def test_add_extension_preview_inavailable(self):
        extension_name = "extension-test-pkg"
        extension1 = 'extension_test_pkg-1.0.0b1-py3-none-any.whl'
        extension2 = 'extension_test_pkg-1.2.3-py3-none-any.whl'
        extension3 = 'extension_test_pkg-1.4.1a1-py3-none-any.whl'

        mocked_index_data = {
            extension_name: [
                mock_ext(extension1, version='1.0.0b1', download_url=_get_test_data_file(extension1)),
                mock_ext(extension3, version='1.4.1a1', download_url=_get_test_data_file(extension3))
            ]
        }
        from knack.util import CLIError
        with mock.patch('azure.cli.core.extension._resolve.get_index_extensions',
                        return_value=mocked_index_data):
            with self.assertRaisesRegex(CLIError, "No suitable stable version of 'extension-test-pkg' to install. Add `--allow-preview` to try preview versions"):
                add_extension(cmd=self.cmd, extension_name=extension_name, allow_preview=False)

    def test_update_extension_with_preview(self):
        extension_name = "extension-test-pkg"
        extension1 = 'extension_test_pkg-1.0.0b1-py3-none-any.whl'
        extension2 = 'extension_test_pkg-1.2.3-py3-none-any.whl'
        extension3 = 'extension_test_pkg-1.4.1a1-py3-none-any.whl'

        mocked_index_data = {
            extension_name: [
                mock_ext(extension1, version='1.0.0b1', download_url=_get_test_data_file(extension1)),
                mock_ext(extension2, version='1.2.3', download_url=_get_test_data_file(extension2)),
                mock_ext(extension3, version='1.4.1a1', download_url=_get_test_data_file(extension3))
            ]
        }
        with mock.patch('azure.cli.core.extension._resolve.get_index_extensions',
                        return_value=mocked_index_data):
            add_extension(self.cmd, extension_name=extension_name, allow_preview=False)
            ext = show_extension(extension_name)
            self.assertEqual(ext['name'], extension_name)
            self.assertEqual(ext['version'], '1.2.3')

            update_extension(self.cmd, extension_name, allow_preview=True)
            ext = show_extension(extension_name)
            self.assertEqual(ext['name'], extension_name)
            self.assertEqual(ext['version'], '1.4.1a1')

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_ext_dynamic_install_config_tty(self, _):
        from azure.cli.core.extension.dynamic_install import _get_extension_use_dynamic_install_config
        self.assertEqual(_get_extension_use_dynamic_install_config(None), 'yes_prompt')

    @mock.patch('sys.stdin.isatty', return_value=False)
    def test_ext_dynamic_install_config_no_tty(self, _):
        from azure.cli.core.extension.dynamic_install import _get_extension_use_dynamic_install_config
        self.assertEqual(_get_extension_use_dynamic_install_config(None), 'yes_without_prompt')


class TestWheelExtension(TestExtensionsBase):

    def test_wheel_get_all(self):
        _install_test_extension1()
        whl_exts = WheelExtension.get_all()
        self.assertEqual(len(whl_exts), 1)

    def test_wheel_version(self):
        _install_test_extension1()
        ext = get_extension(EXT_NAME)
        self.assertEqual(ext.version, EXT_VERSION)

    def test_wheel_type(self):
        _install_test_extension1()
        ext = get_extension(EXT_NAME)
        self.assertEqual(ext.ext_type, 'whl')

    def test_wheel_metadata1(self):
        _install_test_extension1()
        ext = get_extension(EXT_NAME)
        # There should be no exceptions and metadata should have some value
        self.assertTrue(ext.metadata)

    def test_wheel_metadata2(self):
        _install_test_extension2()
        ext = get_extension(EXT_NAME)
        # There should be no exceptions and metadata should have some value
        self.assertTrue(ext.metadata)
        # We check that we can retrieve any one of the az extension metadata values
        self.assertTrue(ext.metadata.get(EXT_METADATA_MINCLICOREVERSION))


class TestWheelSystemExtension(TestExtensionsBase):

    def test_wheel_get_all(self):
        _install_test_extension1(system=True)
        whl_exts = WheelExtension.get_all()
        self.assertEqual(len(whl_exts), 1)

    def test_wheel_user_system_extensions(self):
        _install_test_extension1()
        _install_test_extension3(system=True)
        whl_exts = WheelExtension.get_all()
        self.assertEqual(len(whl_exts), 2)

    def test_wheel_user_system_same_extension(self):
        _install_test_extension1()
        _install_test_extension1(system=True)
        self.assertNotEqual(build_extension_path(EXT_NAME), build_extension_path(EXT_NAME, system=True))
        actual = get_extension(EXT_NAME, ext_type=WheelExtension)
        self.assertEqual(actual.name, EXT_NAME)
        self.assertEqual(actual.path, build_extension_path(EXT_NAME))
        shutil.rmtree(self.ext_dir)
        actual = get_extension(EXT_NAME, ext_type=WheelExtension)
        self.assertEqual(actual.name, EXT_NAME)
        self.assertEqual(actual.path, build_extension_path(EXT_NAME, system=True))

    def test_wheel_version(self):
        _install_test_extension1(system=True)
        ext = get_extension(EXT_NAME)
        self.assertEqual(ext.version, EXT_VERSION)

    def test_wheel_type(self):
        _install_test_extension1(system=True)
        ext = get_extension(EXT_NAME)
        self.assertEqual(ext.ext_type, 'whl')

    def test_wheel_metadata1(self):
        _install_test_extension1(system=True)
        ext = get_extension(EXT_NAME)
        # There should be no exceptions and metadata should have some value
        self.assertTrue(ext.metadata)

    def test_wheel_metadata2(self):
        _install_test_extension2(system=True)
        ext = get_extension(EXT_NAME)
        # There should be no exceptions and metadata should have some value
        self.assertTrue(ext.metadata)
        # We check that we can retrieve any one of the az extension metadata values
        self.assertTrue(ext.metadata.get(EXT_METADATA_MINCLICOREVERSION))


if __name__ == '__main__':
    unittest.main()
