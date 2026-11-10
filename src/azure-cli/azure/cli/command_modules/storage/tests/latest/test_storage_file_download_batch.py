# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ntpath
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from azure.cli.core.azclierror import FileOperationError
from azure.cli.command_modules.storage.operations.file import download_file, storage_file_download_batch

FILE_MODULE = 'azure.cli.command_modules.storage.operations.file'
UTIL_MODULE = 'azure.cli.command_modules.storage.util'


class _FakeDownloader:
    def readinto(self, stream):
        stream.write(b'content')


class _FakeFileClient:
    def __init__(self, path, name=None):
        self.path = path
        self.name = path if name is None else name
        self.url = 'https://account.file.core.windows.net/share/' + path

    def download_file(self, **_kwargs):
        return _FakeDownloader()

    def get_file_properties(self, **_kwargs):
        return SimpleNamespace(name=self.name)


class _FakeShareClient:
    """Serves a fixed listing: {directory: [(name, is_directory), ...]}."""
    account_name = 'account'

    def __init__(self, listing):
        self.listing = listing
        self.requested_files = []

    def list_directories_and_files(self, directory_name=None, **_kwargs):
        return [{'name': name, 'is_directory': is_dir} for name, is_dir in self.listing.get(directory_name or '', [])]

    def get_file_client(self, path):
        self.requested_files.append(path)
        return _FakeFileClient(path)


class TestStorageFileDownloadBatch(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._root.name)
        self.destination = os.path.join(self.root, 'a', 'b', 'destination')
        os.makedirs(self.destination)

    def tearDown(self):
        self._root.cleanup()

    def _run(self, listing, **kwargs):
        client = _FakeShareClient(listing)
        result = storage_file_download_batch(client, source='share', destination=self.destination, **kwargs)
        return client, result

    def _files_written(self):
        return sorted(os.path.relpath(os.path.join(d, f), self.root)
                      for d, _, files in os.walk(self.root) for f in files)

    def _assert_rejected(self, listing, **kwargs):
        client = _FakeShareClient(listing)
        with self.assertRaisesRegex(FileOperationError, 'outside the destination directory'):
            storage_file_download_batch(client, source='share', destination=self.destination, **kwargs)
        self.assertEqual(client.requested_files, [])
        self.assertEqual(self._files_written(), [])

    def test_download_batch_writes_nested_files_inside_destination(self):
        client, result = self._run({
            '': [('top.txt', False), ('dir', True)],
            'dir': [('a.txt', False), ('sub', True)],
            'dir/sub': [('b.txt', False)],
        })

        self.assertEqual(sorted(client.requested_files), ['dir/a.txt', 'dir/sub/b.txt', 'top.txt'])
        self.assertEqual(sorted(result), ['https://account.file.core.windows.net/share/' + p
                                          for p in ('dir/a.txt', 'dir/sub/b.txt', 'top.txt')])
        expected = [os.path.join('a', 'b', 'destination', *p.split('/'))
                    for p in ('dir/a.txt', 'dir/sub/b.txt', 'top.txt')]
        self.assertEqual(self._files_written(), sorted(expected))

    def test_download_batch_rejects_traversal_file_names(self):
        for name in ('../evil.txt', '../../evil.txt', '../../../evil.txt', 'x/../../evil.txt', '..'):
            with self.subTest(name=name):
                self._assert_rejected({'': [(name, False)]})

    def test_download_batch_rejects_traversal_directory_names(self):
        for listing in ({'': [('..', True)], '..': [('evil.txt', False)]},
                        {'': [('../..', True)], '../..': [('evil.txt', False)]},
                        {'': [('dir', True)], 'dir': [('../..', True)], '..': [('evil.txt', False)]}):
            with self.subTest(listing=listing):
                self._assert_rejected(listing)

    def test_download_batch_rejects_before_downloading_any_file(self):
        self._assert_rejected({'': [('good.txt', False), ('dir', True)], 'dir': [('../../evil.txt', False)]})

    def test_download_batch_dryrun_rejects_traversal_names(self):
        self._assert_rejected({'': [('../../evil.txt', False)]}, dryrun=True)

    def test_download_batch_dryrun_logs_validated_paths(self):
        with mock.patch(FILE_MODULE + '.logger') as logger:
            client, result = self._run({'': [('dir', True)], 'dir': [('a.txt', False)]}, dryrun=True)

        self.assertEqual(result, [])
        self.assertEqual(client.requested_files, [])
        self.assertEqual(self._files_written(), [])
        self.assertIn(mock.call('  - %s/%s => %s', 'dir', 'a.txt', os.path.join(self.destination, 'dir', 'a.txt')),
                      logger.warning.call_args_list)

    def test_download_batch_contains_absolute_names(self):
        outside = os.path.join(self.root, 'evil.txt')
        for listing in ({'': [(outside, False)]},
                        {'': [(os.path.dirname(outside), True)],
                         os.path.dirname(outside).replace('\\', '/').strip('/'): [('evil.txt', False)]}):
            with self.subTest(listing=listing):
                if sys.platform == 'win32':
                    # drive-absolute names are rejected
                    self._assert_rejected(listing)
                else:
                    # a leading '/' is stripped, so the name lands inside the destination
                    self._run(listing)
                    self.assertTrue(os.path.isfile(os.path.join(self.destination, outside.lstrip('/'))))
                self.assertFalse(os.path.exists(outside))

    def test_download_batch_contains_windows_traversal_names(self):
        for listing in ({'': [('..\\..\\evil.txt', False)]},
                        {'': [('dir\\..\\..\\evil.txt', False)]},
                        {'': [('..\\..', True)], '../..': [('evil.txt', False)]},
                        {'': [(os.path.join(self.root, 'evil.txt').replace('\\', '/'), False)]}):
            with self.subTest(listing=listing):
                if sys.platform == 'win32':
                    self._assert_rejected(listing)
                else:
                    # '\' is not a separator here, so these are ordinary names that must stay inside the destination
                    self._run(listing)
                    outside = [f for f in self._files_written()
                               if not f.startswith(os.path.join('a', 'b', 'destination') + os.sep)]
                    self.assertEqual(outside, [])
                    shutil.rmtree(self.destination)
                    os.makedirs(self.destination)

    def test_download_batch_rejects_windows_names_with_simulated_windows_paths(self):
        # Exercise Windows path semantics on any platform by swapping os.path for ntpath in the code under test
        windows_os = SimpleNamespace(path=ntpath)
        destination = 'C:\\Users\\victim\\downloads'
        with mock.patch(FILE_MODULE + '.os', windows_os), mock.patch(UTIL_MODULE + '.os', windows_os):
            for listing in ({'': [('..\\..\\evil.txt', False)]},
                            {'': [('dir\\..\\..\\evil.txt', False)]},
                            {'': [('C:\\Users\\Public\\evil.txt', False)]},
                            {'': [('C:/Users/Public/evil.txt', False)]},
                            {'': [('D:evil.txt', False)]},
                            {'': [('..\\..', True)], '../..': [('evil.txt', False)]}):
                with self.subTest(listing=listing):
                    client = _FakeShareClient(listing)
                    with self.assertRaisesRegex(FileOperationError, 'outside the destination directory'):
                        storage_file_download_batch(client, source='share', destination=destination, dryrun=True)

            client = _FakeShareClient({'': [('dir\\file.txt', False)]})
            self.assertEqual(storage_file_download_batch(client, source='share', destination=destination,
                                                         dryrun=True), [])


class TestStorageFileDownload(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._root.name)
        self.destination = os.path.join(self.root, 'destination')
        os.makedirs(self.destination)

    def tearDown(self):
        self._root.cleanup()

    def test_download_to_directory_uses_service_file_name(self):
        download_file(_FakeFileClient('dir/file.txt'), destination_path=self.destination)
        self.assertTrue(os.path.isfile(os.path.join(self.destination, 'file.txt')))

    def test_download_to_directory_rejects_traversal_service_file_name(self):
        names = ['dir/..']
        if sys.platform == 'win32':
            names += ['..\\evil.txt', 'dir/..\\..\\evil.txt', 'C:evil.txt']
        for name in names:
            with self.subTest(name=name):
                with self.assertRaisesRegex(FileOperationError, 'outside the destination directory'):
                    download_file(_FakeFileClient('file.txt', name=name), destination_path=self.destination)
                self.assertEqual(os.listdir(self.root), ['destination'])
                self.assertEqual(os.listdir(self.destination), [])


if __name__ == '__main__':
    unittest.main()
