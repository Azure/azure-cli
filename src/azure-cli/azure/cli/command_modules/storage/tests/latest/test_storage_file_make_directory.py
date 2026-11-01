# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ntpath
import unittest
from unittest import mock

from azure.cli.command_modules.storage.operations.file import _make_directory_in_files_share


class TestMakeDirectoryInFilesShare(unittest.TestCase):
    def test_absolute_windows_path_terminates_and_skips_root(self):
        file_service = mock.Mock()
        # Force ntpath semantics so this test is deterministic on any CI host OS
        # (os.path is posixpath on Linux, where 'C:' isn't recognized as a drive root).
        with mock.patch('azure.cli.command_modules.storage.operations.file.os.path', ntpath):
            _make_directory_in_files_share(file_service, 'C:/Program Files/Git/some/path')

        created = [c.kwargs['directory_name'] for c in file_service.create_directory.call_args_list]
        self.assertEqual(created, [
            'C:/Program Files',
            'C:/Program Files/Git',
            'C:/Program Files/Git/some',
            'C:/Program Files/Git/some/path',
        ])
        # The share root itself must never be queued for creation (it already exists).
        self.assertNotIn('C:/', created)

    def test_absolute_posix_path_terminates_and_skips_root(self):
        file_service = mock.Mock()
        _make_directory_in_files_share(file_service, '/NewFolder/NewFolder/xxx')

        created = [c.kwargs['directory_name'] for c in file_service.create_directory.call_args_list]
        self.assertEqual(created, ['/NewFolder', '/NewFolder/NewFolder', '/NewFolder/NewFolder/xxx'])
        self.assertNotIn('/', created)

    def test_relative_path_unaffected(self):
        file_service = mock.Mock()
        _make_directory_in_files_share(file_service, 'some/path')

        created = [c.kwargs['directory_name'] for c in file_service.create_directory.call_args_list]
        self.assertEqual(created, ['some', 'some/path'])


if __name__ == '__main__':
    unittest.main()
