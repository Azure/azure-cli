# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import unittest
from datetime import datetime, timedelta
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck)
from azure.cli.core.util import CLIError
from azure.cli.command_modules.storage._factory import NO_CREDENTIALS_ERROR_MESSAGE
from .storage_test_util import StorageScenarioMixin


class StorageBlobUploadTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='source_account')
    @StorageAccountPreparer(parameter_name='target_account')
    def test_storage_blob_incremental_copy(self, resource_group, source_account, target_account):
        source_file = self.create_temp_file(16, full_random=True)
        source_account_info = self.get_account_info(resource_group, source_account)
        source_container = self.create_container(source_account_info)
        self.storage_cmd('storage blob upload -c {} -n src -f {} -t page', source_account_info,
                         source_container, source_file)

        snapshot = self.storage_cmd('storage blob snapshot -c {} -n src', source_account_info,
                                    source_container).get_output_in_json()['snapshot']

        target_account_info = self.get_account_info(resource_group, target_account)
        target_container = self.create_container(target_account_info)
        self.storage_cmd('storage blob incremental-copy start --source-container {} --source-blob '
                         'src --source-account-name {} --source-account-key {} --source-snapshot '
                         '{} --destination-container {} --destination-blob backup',
                         target_account_info, source_container, source_account,
                         source_account_info[1], snapshot, target_container)

    def test_storage_blob_no_credentials_scenario(self):
        source_file = self.create_temp_file(1)
        with self.assertRaisesRegexp(CLIError, re.escape(NO_CREDENTIALS_ERROR_MESSAGE)):
            self.cmd('storage blob upload -c foo -n bar -f ' + source_file)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_small_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 1, 'block', 0)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_midsize_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 4096, 'block', 0)

    def verify_blob_upload_and_download(self, group, account, file_size_kb, blob_type,
                                        block_count=0, skip_download=False):
        local_dir = self.create_temp_dir()
        local_file = self.create_temp_file(file_size_kb)
        blob_name = self.create_random_name(prefix='blob', length=24)
        account_info = self.get_account_info(group, account)

        container = self.create_container(account_info)

        self.storage_cmd('storage blob exists -n {} -c {}', account_info, blob_name, container) \
            .assert_with_checks(JMESPathCheck('exists', False))

        self.storage_cmd('storage blob upload -c {} -f {} -n {} --type {}', account_info,
                         container, local_file, blob_name, blob_type)
        self.storage_cmd('storage blob exists -n {} -c {}', account_info, blob_name, container) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage blob show -n {} -c {}', account_info, blob_name, container) \
            .assert_with_checks(JMESPathCheck('name', blob_name))

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage blob generate-sas -n {} -c {} --expiry {} --permissions '
                               'r --https-only', account_info, blob_name, container, expiry).output
        self.assertTrue(sas)
        self.assertIn('sig', sas)

        self.storage_cmd('storage blob update -n {} -c {} --content-type application/test-content',
                         account_info, blob_name, container)

        self.storage_cmd('storage blob show -n {} -c {}', account_info, blob_name, container) \
            .assert_with_checks([JMESPathCheck('properties.contentSettings.contentType', 'application/test-content'),
                                 JMESPathCheck('properties.contentLength', file_size_kb * 1024)])

        self.storage_cmd('storage blob service-properties show', account_info) \
            .assert_with_checks(JMESPathCheck('hourMetrics.enabled', True))

        if not skip_download:
            downloaded = os.path.join(local_dir, 'test.file')

            self.storage_cmd('storage blob download -n {} -c {} --file {}',
                             account_info, blob_name, container, downloaded)
            self.assertTrue(os.path.isfile(downloaded), 'The file is not downloaded.')
            self.assertEqual(file_size_kb * 1024, os.stat(downloaded).st_size,
                             'The download file size is not right.')

        # Verify the requests in cassette to ensure the count of the block requests is expected
        # This portion of validation doesn't verify anything during playback because the recording
        # is fixed.

        def is_block_put_req(request):
            if request.method != 'PUT':
                return False

            if not re.search('/cont[0-9]+/blob[0-9]+', request.path):
                return False

            comp_block = False
            has_blockid = False
            for key, value in request.query:
                if key == 'comp' and value == 'block':
                    comp_block = True
                elif key == 'blockid':
                    has_blockid = True

            return comp_block and has_blockid

        requests = self.cassette.requests
        put_blocks = [request for request in requests if is_block_put_req(request)]
        self.assertEqual(block_count, len(put_blocks),
                         'The expected number of block put requests is {} but the actual '
                         'number is {}.'.format(block_count, len(put_blocks)))


if __name__ == '__main__':
    unittest.main()
