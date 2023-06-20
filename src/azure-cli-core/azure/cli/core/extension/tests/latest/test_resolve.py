# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
from azure.cli.core.extension._resolve import (resolve_from_index, resolve_project_url_from_index,
                                               NoExtensionCandidatesError, _is_not_platform_specific,
                                               _is_greater_than_cur_version)
from . import IndexPatch, mock_ext


class TestResolveFromIndex(unittest.TestCase):

    def test_no_exts_in_index(self):
        name = 'myext'
        with IndexPatch({}), self.assertRaises(NoExtensionCandidatesError) as err:
            resolve_from_index(name)
        self.assertEqual(str(err.exception), "No matching extensions for '{}'.".format(name))

    def test_ext_not_in_index(self):
        name = 'an_extension_b'
        with IndexPatch({'an_extension_a': []}), self.assertRaises(NoExtensionCandidatesError) as err:
            resolve_from_index(name)
        self.assertEqual(str(err.exception), "No matching extensions for '{}'.".format(name))

    def test_ext_resolved(self):
        name = 'myext'
        index_data = {name: [mock_ext('myext-0.0.1-py2.py3-none-any.whl', '0.0.1')]}
        with IndexPatch(index_data):
            self.assertEqual(resolve_from_index(name)[0], index_data[name][0]['downloadUrl'])

    def test_ext_py3_resolved(self):
        name = 'myext'
        index_data = {'myext': [mock_ext('myext-0.0.1-py3-none-any.whl', '0.0.1')]}
        with IndexPatch(index_data):
            self.assertEqual(resolve_from_index(name)[0], index_data[name][0]['downloadUrl'])

    def test_filter_platform_wrong_abi(self):
        name = 'myext'
        # Should raise as wrong abi of cp33d
        with IndexPatch({'myext': [mock_ext('myext-0.0.1-py2.py3-cp33d-any.whl', '0.0.1')]}), self.assertRaises(NoExtensionCandidatesError):
            resolve_from_index(name)

    def test_filter_platform_wrong_platform(self):
        name = 'myext'
        # Should raise as we don't support platform specific whls in index
        with IndexPatch({'myext': [mock_ext('myext-0.0.1-py2.py3-none-x86_64.whl', '0.0.1')]}), self.assertRaises(NoExtensionCandidatesError):
            resolve_from_index(name)

    def test_filter_platform(self):
        name = 'myext'
        index_data = {'myext': [mock_ext('myext-0.0.1-py2.py3-none-any.whl', '0.0.1'), mock_ext('myext-0.0.2-py3-none-any.whl', '0.0.2')]}
        with IndexPatch(index_data):
            # Should choose the second one as py version is not considered platform specific.
            self.assertEqual(resolve_from_index(name)[0], index_data[name][1]['downloadUrl'])

    def test_filter_target_version(self):
        ext_name = 'hello'
        index_data = {
            ext_name: [
                mock_ext('hello-0.1.0-py3-none-any.whl', '0.1.0'),
                mock_ext('hello-0.2.0-py3-none-any.whl', '0.2.0')
            ]
        }

        # resolve okay
        with IndexPatch(index_data):
            self.assertEqual(resolve_from_index(ext_name, target_version='0.1.0')[0], index_data[ext_name][0]['downloadUrl'])
            self.assertEqual(resolve_from_index(ext_name, target_version='0.2.0')[0], index_data[ext_name][1]['downloadUrl'])

        with IndexPatch(index_data):
            with self.assertRaisesRegex(NoExtensionCandidatesError, "Version '0.3.0' not found for extension 'hello'"):
                resolve_from_index(ext_name, target_version='0.3.0')

    def test_ext_has_available_update(self):
        ext_name = 'myext'
        index_data = {
            ext_name: [
                mock_ext(f'{ext_name}-0.1.0-py3-none-any.whl', '0.1.0'),
                mock_ext(f'{ext_name}-0.2.0-py3-none-any.whl', '0.2.0')
            ]
        }

        with IndexPatch(index_data):
            self.assertEqual(resolve_from_index(ext_name, cur_version='0.1.0')[0], index_data[ext_name][1]['downloadUrl'])


    def test_ext_has_no_available_updates(self):
        ext_name = 'myext'
        index_data = {
            ext_name: [
                mock_ext(f'{ext_name}-0.1.0-py3-none-any.whl', '0.1.0'),
                mock_ext(f'{ext_name}-0.2.0-py3-none-any.whl', '0.2.0')
            ]
        }

        with IndexPatch(index_data):
            with self.assertRaisesRegex(NoExtensionCandidatesError, f"Latest version of '{ext_name}' is already installed."):
                resolve_from_index(ext_name, cur_version='0.2.0')

    @mock.patch("azure.cli.core.__version__", "2.15.0")
    def test_ext_requires_later_version_of_cli_core(self):
        ext_name = 'myext'
        min_cli_version="2.16.0"
        index_data = {
            ext_name: [
                mock_ext(f'{ext_name}-0.1.0-py3-none-any.whl', '0.1.0', name=ext_name, min_cli_version=min_cli_version),
                mock_ext(f'{ext_name}-0.2.0-py3-none-any.whl', '0.2.0', name=ext_name, min_cli_version=min_cli_version)
            ]
        }

        exception_regex = '\n'.join([
            f'This extension requires a min of {min_cli_version} CLI core.',
            "Please run 'az upgrade' to upgrade to a compatible version."
        ])
        with IndexPatch(index_data):
            with self.assertRaisesRegex(NoExtensionCandidatesError, exception_regex):
                resolve_from_index(ext_name)


    @mock.patch("azure.cli.core.__version__", "2.15.0")
    def test_ext_requires_earlier_version_of_cli_core(self):
        ext_name = 'myext'
        max_cli_version="2.14.0"
        index_data = {
            ext_name: [
                mock_ext(f'{ext_name}-0.1.0-py3-none-any.whl', '0.1.0', name=ext_name, max_cli_version=max_cli_version),
                mock_ext(f'{ext_name}-0.2.0-py3-none-any.whl', '0.2.0', name=ext_name, max_cli_version=max_cli_version)
            ]
        }
        exception_regex = '\n'.join([
            f'This extension requires a max of {max_cli_version} CLI core.',
            f"Please run 'az extension update -n {ext_name}' to update the extension."
        ])

        with IndexPatch(index_data):
            with self.assertRaisesRegex(NoExtensionCandidatesError, exception_regex):
                resolve_from_index(ext_name)


class TestResolveFilters(unittest.TestCase):

    def test_platform_specific(self):
        self.assertTrue(_is_not_platform_specific(mock_ext('myext-0.0.1-py2.py3-none-any.whl')))

        self.assertTrue(_is_not_platform_specific(mock_ext('myext-0.0.1-py2-none-any.whl')))
        self.assertFalse(_is_not_platform_specific(mock_ext('myext-0.0.1-py3-cp33d-any.whl')))
        self.assertFalse(_is_not_platform_specific(mock_ext('myext-0.0.1-py3-none-x86_64.whl')))
        self.assertFalse(_is_not_platform_specific(mock_ext('myext-1.1.26.0-py2-none-linux_armv7l.whl')))

    def test_greater_than_current(self):
        self.assertIsNone(_is_greater_than_cur_version(None))
        self.assertIsNotNone(_is_greater_than_cur_version('0.0.1'))
        filter_func = _is_greater_than_cur_version('0.0.1')
        filter_func
        self.assertTrue(filter_func(mock_ext('myext-0.0.2-py2.py3-none-any.whl', '0.0.2')))
        self.assertTrue(filter_func(mock_ext('myext-0.0.1+dev-py2.py3-none-any.whl', '0.0.1+dev')))
        self.assertTrue(filter_func(mock_ext('myext-0.0.1.post1-py2.py3-none-any.whl', '0.0.1.post1')))

        self.assertFalse(filter_func(mock_ext('myext-0.0.1.pre1-py2.py3-none-any.whl', '0.0.1.pre1')))
        self.assertFalse(filter_func(mock_ext('myext-0.0.1-py2.py3-none-any.whl', '0.0.1')))


class TestResolveProjectUrlFromIndex(unittest.TestCase):

    def test_project_url_for_no_exts_in_index(self):
        name = 'myext'
        with IndexPatch({}), self.assertRaises(NoExtensionCandidatesError) as err:
            resolve_project_url_from_index(name)
        self.assertEqual(str(err.exception), "No extension found with name '{}'".format(name))

    def test_project_url_for_no_matching_ext_in_index(self):
        name = 'an_extension_b'
        with IndexPatch({'an_extension_a': []}), self.assertRaises(NoExtensionCandidatesError) as err:
            resolve_project_url_from_index(name)
        self.assertEqual(str(err.exception), "No extension found with name '{}'".format(name))

    def test_project_url_for_ext_resolved(self):
        name = 'myext'
        index_data = {name: [mock_ext('myext-0.0.1-py2.py3-none-any.whl', '0.0.1')]}
        with IndexPatch(index_data):
            self.assertEqual(resolve_project_url_from_index(name), index_data[name][0]['metadata']['extensions']['python.details']['project_urls']['Home'])


if __name__ == '__main__':
    unittest.main()
