# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Integration test for file upload

The tests require environment variable 'test_connection_string' to set to the connection string of
the storage account they will be run on.
"""

import os
import shutil
from unittest import TestCase
from azure.cli.main import main as cli_main
from .integration_test_base import StorageIntegrationTestBase


class StorageFileDownloadPlainTests(TestCase):
    def test_file_download_batch_help(self):
        with self.assertRaises(SystemExit):
            cli_main('storage file download-batch -h'.split())


class StorageFileDownloadIntegrationTests(StorageIntegrationTestBase):
    @classmethod
    def setUpClass(cls):
        StorageIntegrationTestBase.setUpClass()
        # set up sample file share
        cls._test_source_share = cls.generate_new_share_name()
        assert cls._file_service.create_share(cls._test_source_share)

        cli_main('storage file upload-batch -s {} -d {} --connection-string {}'
                 .format(cls._resource_folder, cls._test_source_share,
                         cls._test_connection_string)
                 .split())

        from ..util import glob_files_remotely
        test_files = [f for f in glob_files_remotely(cls._file_service, cls._test_source_share,
                                                     pattern=None)]
        assert len(test_files) == 41

    @classmethod
    def tearDownClass(cls):
        cls._file_service.delete_share(cls._test_source_share)

    def setUp(self):
        self._test_folder = os.path.join(os.getcwd(), 'test_temp')
        if os.path.exists(self._test_folder):
            shutil.rmtree(self._test_folder)

        os.mkdir(self._test_folder)

    def test_file_download_recursively_without_pattern(self):
        cmd = 'storage file download-batch -s {} -d {} --account-name {} --account-key {}'\
            .format(self._test_source_share, self._test_folder,
                    self._file_service.account_name, self._file_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 41

    def test_file_download_recursively_with_pattern_1(self):
        cmd = 'storage file download-batch -s https://{}/{} -d {} --pattern {} --account-key {}'\
            .format(self._file_service.primary_endpoint, self._test_source_share,
                    self._test_folder, '*', self._file_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 41

    def test_file_download_recursively_with_pattern_2(self):
        cmd = 'storage file download-batch -s https://{}/{} -d {} --pattern {} --account-key {}'\
            .format(self._file_service.primary_endpoint, self._test_source_share,
                    self._test_folder, 'apple/*', self._file_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 10

    def test_file_download_recursively_with_pattern_3(self):
        cmd = 'storage file download-batch -s https://{}/{} -d {} --pattern {} --account-key {}'\
            .format(self._file_service.primary_endpoint, self._test_source_share,
                    self._test_folder, '*/file_0', self._file_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 4
