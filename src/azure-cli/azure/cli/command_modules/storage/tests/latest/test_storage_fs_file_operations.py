# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from azure.cli.command_modules.storage.operations.fs_file import download_file


class TestStorageFsFileOperations(unittest.TestCase):

    def test_download_file_streams_content_to_destination(self):
        download = mock.Mock()
        download.readinto.side_effect = lambda stream: stream.write(b'hello world')

        client = mock.Mock()
        client.get_file_properties.return_value = SimpleNamespace(name='dir/test.txt')
        client.download_file.return_value = download

        with tempfile.TemporaryDirectory() as temp_dir:
            download_file(client, destination_path=temp_dir)

            with open(os.path.join(temp_dir, 'test.txt'), 'rb') as stream:
                self.assertEqual(stream.read(), b'hello world')

        download.readinto.assert_called_once()
        download.readall.assert_not_called()
