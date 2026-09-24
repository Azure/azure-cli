# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ntpath
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from azure.cli.core.azclierror import FileOperationError
from azure.cli.command_modules.storage.operations.blob import storage_blob_download_batch

BLOB_MODULE = 'azure.cli.command_modules.storage.operations.blob'
UTIL_MODULE = 'azure.cli.command_modules.storage.util'


def _fake_download_blob(client, file_path=None, **kwargs):  # pylint: disable=unused-argument
    with open(file_path, 'wb') as stream:
        stream.write(b'content')
    return mock.Mock(name=file_path)


class TestStorageBlobDownloadBatch(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._root.name)
        self.destination = os.path.join(self.root, 'a', 'b', 'destination')
        os.makedirs(self.destination)

    def tearDown(self):
        self._root.cleanup()

    def _run(self, blob_names, dryrun=False):
        client = mock.Mock()
        with mock.patch(BLOB_MODULE + '.collect_blobs', return_value=list(blob_names)), \
                mock.patch(BLOB_MODULE + '.download_blob', side_effect=_fake_download_blob) as download:
            storage_blob_download_batch(client, source='container', destination=self.destination,
                                        source_container_name='container', dryrun=dryrun)
        return download

    def _files_written(self):
        return sorted(os.path.relpath(os.path.join(d, f), self.root)
                      for d, _, files in os.walk(self.root) for f in files)

    def test_download_batch_writes_blobs_inside_destination(self):
        download = self._run(['file.txt', 'dir/sub/nested.txt', '/leading/slash.txt', 'x/../normalized.txt'])

        self.assertEqual(download.call_count, 4)
        expected = [os.path.join('a', 'b', 'destination', p) for p in
                    ('dir/sub/nested.txt', 'file.txt', 'leading/slash.txt', 'normalized.txt')]
        self.assertEqual(self._files_written(), sorted(os.path.normpath(p) for p in expected))

    def test_download_batch_rejects_path_traversal_blob_names(self):
        for blob_name in ('../evil.txt', '../../evil.txt', '../../../evil.txt', 'dir/../../evil.txt',
                          'dir/../../destination-sibling/evil.txt', '..'):
            with self.subTest(blob_name=blob_name):
                with self.assertRaisesRegex(FileOperationError, 'outside the destination directory'):
                    self._run([blob_name])
                self.assertEqual(self._files_written(), [])

    def test_download_batch_rejects_before_downloading_any_blob(self):
        with mock.patch(BLOB_MODULE + '.download_blob', side_effect=_fake_download_blob) as download:
            with self.assertRaises(FileOperationError):
                with mock.patch(BLOB_MODULE + '.collect_blobs', return_value=['good.txt', '../../evil.txt']):
                    storage_blob_download_batch(mock.Mock(), source='container', destination=self.destination,
                                                source_container_name='container')
        download.assert_not_called()
        self.assertEqual(self._files_written(), [])

    def test_download_batch_dryrun_rejects_path_traversal_blob_names(self):
        with self.assertRaises(FileOperationError):
            self._run(['../../evil.txt'], dryrun=True)

    @unittest.skipIf(sys.platform == 'win32', 'Creating symlinks may require elevated privileges on Windows')
    def test_download_batch_rejects_symlink_escape(self):
        outside = os.path.join(self.root, 'outside')
        os.makedirs(outside)
        os.symlink(outside, os.path.join(self.destination, 'link'))

        with self.assertRaises(FileOperationError):
            self._run(['link/evil.txt'])
        self.assertEqual(os.listdir(outside), [])

    def test_download_batch_rejects_windows_blob_names_with_simulated_windows_paths(self):
        # Exercise Windows path semantics on any platform by swapping os.path for ntpath in the code under test
        windows_os = SimpleNamespace(path=ntpath)
        destination = 'C:\\Users\\victim\\downloads'
        with mock.patch(BLOB_MODULE + '.os', windows_os), mock.patch(UTIL_MODULE + '.os', windows_os):
            for blob_name in ('C:/Users/Public/evil.txt', 'C:\\Users\\Public\\evil.txt', 'D:/evil.txt',
                              '..\\..\\evil.txt', 'dir\\..\\..\\evil.txt', '../downloads2/evil.txt'):
                with self.subTest(blob_name=blob_name):
                    with mock.patch(BLOB_MODULE + '.collect_blobs', return_value=[blob_name]), \
                            self.assertRaisesRegex(FileOperationError, 'outside the destination directory'):
                        storage_blob_download_batch(mock.Mock(), source='container', destination=destination,
                                                    source_container_name='container', dryrun=True)

            for blob_name in ('dir/file.txt', 'dir\\file.txt', 'C:evil.txt', '\\\\server\\share\\file.txt'):
                with self.subTest(blob_name=blob_name):
                    with mock.patch(BLOB_MODULE + '.collect_blobs', return_value=[blob_name]):
                        self.assertEqual(storage_blob_download_batch(
                            mock.Mock(), source='container', destination=destination,
                            source_container_name='container', dryrun=True), [])

    @unittest.skipUnless(sys.platform == 'win32', 'Windows path semantics')
    def test_download_batch_rejects_windows_traversal_blob_names(self):
        drive = os.path.splitdrive(self.root)[0]
        for blob_name in ('..\\..\\evil.txt', 'dir\\..\\..\\evil.txt', drive + '/evil.txt', drive + '\\evil.txt'):
            with self.subTest(blob_name=blob_name):
                with self.assertRaises(FileOperationError):
                    self._run([blob_name])
                self.assertEqual(self._files_written(), [])


if __name__ == '__main__':
    unittest.main()
