# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Integration test for blob upload

The tests require environment variable 'test_connection_string' to set to the connection
string of the storage account they will be run on.
"""

import os
import os.path
import shutil
from unittest import TestCase
from .integration_test_base import StorageIntegrationTestBase
from azure.cli.main import main as cli_main


class StorageBlobDownloadPlainTests(TestCase):
    def test_blob_download_help(self):
        with self.assertRaises(SystemExit):
            cli_main('storage blob upload-batch -h'.split())


class StorageBlobDownloadIntegrationTests(StorageIntegrationTestBase):
    @classmethod
    def setUpClass(cls):
        StorageIntegrationTestBase.setUpClass()
        # set up sample container
        cls._test_source_container = cls.generate_new_container_name()
        assert cls._blob_service.create_container(cls._test_source_container)

        cli_main('storage blob upload-batch -s {} -d {} --connection-string {}'
                 .format(cls._resource_folder, cls._test_source_container,
                         cls._test_connection_string)
                 .split())

        test_blobs = [b.name for b in cls._blob_service.list_blobs(cls._test_source_container)]
        assert len(test_blobs) == 41

    @classmethod
    def tearDownClass(cls):
        cls._blob_service.delete_container(cls._test_source_container)

    def setUp(self):
        self._test_folder = os.path.join(os.getcwd(), 'test_temp')
        if os.path.exists(self._test_folder):
            shutil.rmtree(self._test_folder)

        os.mkdir(self._test_folder)

    def test_blob_download_recursively_without_pattern(self):
        cmd = 'storage blob download-batch -s {} -d {} --account-name {} --account-key {}'\
            .format(self._test_source_container, self._test_folder,
                    self._blob_service.account_name, self._blob_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 41

    def test_blob_download_recursively_with_pattern_1(self):
        cmd = 'storage blob download-batch -s https://{}/{} -d {} --pattern {} --account-key {}'\
            .format(self._blob_service.primary_endpoint, self._test_source_container,
                    self._test_folder, '*', self._blob_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 41

    def test_blob_download_recursively_with_pattern_2(self):
        cmd = 'storage blob download-batch -s https://{}/{} -d {} --pattern {} --account-key {}'\
            .format(self._blob_service.primary_endpoint, self._test_source_container,
                    self._test_folder, 'apple/*', self._blob_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 10

    def test_blob_download_recursively_with_pattern_3(self):
        cmd = 'storage blob download-batch -s https://{}/{} -d {} --pattern {} --account-key {}'\
            .format(self._blob_service.primary_endpoint, self._test_source_container,
                    self._test_folder, '*/file_0', self._blob_service.account_key)

        cli_main(cmd.split())
        assert sum(len(f) for r, d, f in os.walk(self._test_folder)) == 4
