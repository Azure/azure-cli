# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Integration test for blob upload

The tests require environment variable 'test_connection_string' to set to the connection string
of the storage account they will be run on.
"""

from unittest import TestCase
from azure.cli.main import main as cli_main
from .integration_test_base import StorageIntegrationTestBase


class StorageBlobUploadPlainTests(TestCase):
    def test_blob_upload_help(self):
        with self.assertRaises(SystemExit):
            cli_main('storage blob upload-batch -h'.split())


class StorageBlobUploadIntegrationTests(StorageIntegrationTestBase):
    def setUp(self):
        self._keep_test_context = False
        self._test_container_name = self.generate_new_container_name()
        assert self._blob_service.create_container(self._test_container_name)

    def tearDown(self):
        if self._keep_test_context:
            return

        self._blob_service.delete_container(self._test_container_name)

    def test_blob_upload_multiple_files_no_pattern(self):
        url = 'http://{}/{}'.format(self._blob_service.primary_endpoint, self._test_container_name)
        command = 'storage blob upload-batch -s {} -d {} --account-key {}'\
            .format(self._resource_folder, url, self._test_account_key)

        cli_main(command.split())

        blobs = [b.name for b in self._blob_service.list_blobs(self._test_container_name)]
        assert len(blobs) == 41

    def test_blob_upload_multiple_files_dry_run(self):
        url = 'http://{}/{}'.format(self._blob_service.primary_endpoint, self._test_container_name)
        command = 'storage blob upload-batch -s {} -d {} --account-key {} --dryrun' \
            .format(self._resource_folder, url, self._test_account_key)

        from six import StringIO
        buf = StringIO()
        cli_main(command.split(), file=buf)

        blobs = [b.name for b in self._blob_service.list_blobs(self._test_container_name)]
        assert len(blobs) == 0

        self._keep_test_context = True

    def test_blob_upload_multiple_files_patterns_1(self):
        self._test_blob_upload_multiple_files_patterns('apple/*', 10)

    def test_blob_upload_multiple_files_patterns_2(self):
        self._test_blob_upload_multiple_files_patterns('*/file_0', 4)

    def test_blob_upload_multiple_files_patterns_3(self):
        self._test_blob_upload_multiple_files_patterns('nonexists/*', 0)

    def _test_blob_upload_multiple_files_patterns(self, pattern, expected_count):
        url = 'http://{}/{}'.format(self._blob_service.primary_endpoint, self._test_container_name)
        command = 'storage blob upload-batch -s {} -d {} --account-key {} --pattern {}' \
            .format(self._resource_folder, url, self._test_account_key, pattern)

        cli_main(command.split())

        blobs = [b.name for b in self._blob_service.list_blobs(self._test_container_name)]
        assert len(blobs) == expected_count
