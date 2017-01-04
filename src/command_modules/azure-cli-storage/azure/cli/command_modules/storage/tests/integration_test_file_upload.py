# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Integration tests for file upload

The tests require environment variable 'test_connection_string' to be set to the connection string
of the storage account they will run on.
"""

from unittest import TestCase
from azure.cli.main import main as cli_main
from .integration_test_base import StorageIntegrationTestBase
from ..util import glob_files_remotely


class StorageFileUploadPlainTests(TestCase):
    def test_file_upload_help(self):
        with self.assertRaises(SystemExit):
            cli_main('storage file upload-batch -h'.split())


class StorageFileUploadIntegrationTests(StorageIntegrationTestBase):
    def setUp(self):
        self._keep_test_context = False
        self._test_share_name = self.generate_new_share_name()
        assert self._file_service.create_share(self._test_share_name)

    def tearDown(self):
        if self._keep_test_context:
            return

        self._file_service.delete_share(self._test_share_name)

    def test_file_upload_multiple_files_no_pattern(self):
        url = 'https://{}/{}'.format(self._file_service.primary_endpoint, self._test_share_name)
        cmd = 'storage file upload-batch -s {} -d {} --account-key {}'\
            .format(self._resource_folder, url, self._test_account_key)

        cli_main(cmd.split())

        files = list(glob_files_remotely(self._file_service, self._test_share_name, pattern=None))
        assert len(files) == 41

    def test_file_upload_multiple_files_dry_run(self):
        url = 'https://{}/{}'.format(self._file_service.primary_endpoint, self._test_share_name)
        cmd = 'storage file upload-batch -s {} -d {} --account-key {} --dryrun' \
            .format(self._resource_folder, url, self._test_account_key)

        from six import StringIO
        cli_main(cmd.split(), file=StringIO())

        files = list(glob_files_remotely(self._file_service, self._test_share_name, pattern=None))
        assert len(files) == 0

    def test_file_upload_multiple_files_patterns_1(self):
        self._test_file_upload_multiple_files_patterns('apple/*', 10)

    def test_file_upload_multiple_files_patterns_2(self):
        self._test_file_upload_multiple_files_patterns('*/file_0', 4)

    def test_file_upload_multiple_files_patterns_3(self):
        self._test_file_upload_multiple_files_patterns('nonexists/*', 0)

    def _test_file_upload_multiple_files_patterns(self, pattern, expected_count):
        url = 'http://{}/{}'.format(self._file_service.primary_endpoint, self._test_share_name)
        command = 'storage file upload-batch -s {} -d {} --account-key {} --pattern {}' \
            .format(self._resource_folder, url, self._test_account_key, pattern)

        cli_main(command.split())

        files = list(glob_files_remotely(self._file_service, self._test_share_name, pattern=None))
        assert len(files) == expected_count
