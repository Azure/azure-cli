# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
from datetime import datetime, timedelta
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck)


class StorageBlobUploadTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_small_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 1, 'block', 0)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_midsize_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 4096, 'block', 0)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_101mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 101 * 1024, 'block',
                                             26, skip_download=True)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_100mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 100 * 1024, 'block',
                                             25, skip_download=True)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_99mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 99 * 1024, 'block',
                                             25, skip_download=True)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_64mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 64 * 1024, 'block',
                                             16, skip_download=True)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_63mb_file(self, resource_group, storage_account):
        # 64MB is the put request size limit
        self.verify_blob_upload_and_download(resource_group, storage_account, 63 * 1024, 'block',
                                             skip_download=True)

    def verify_blob_upload_and_download(self, group, account, file_size_kb, blob_type,
                                        block_count=0, skip_download=False):
        container = self.create_random_name(prefix='cont', length=24)
        local_dir = self.create_temp_dir()
        local_file = self.create_temp_file(file_size_kb)
        blob_name = self.create_random_name(prefix='blob', length=24)
        account_key = self.get_account_key(group, account)

        self.set_env('AZURE_STORAGE_ACCOUNT', account)
        self.set_env('AZURE_STORAGE_KEY', account_key)

        self.cmd('storage container create -n {}'.format(container))

        self.cmd('storage blob exists -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('exists', False))

        self.cmd('storage blob upload -c {} -f {} -n {} --type {}'
                 .format(container, local_file, blob_name, blob_type))

        self.cmd('storage blob exists -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('exists', True))

        self.cmd('storage blob show -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('name', blob_name))  # TODO: more checks

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.cmd('storage blob generate-sas -n {} -c {} --expiry {} '
                       '--permissions r --https-only'.format(blob_name, container, expiry)).output
        assert dict(pair.split('=') for pair in sas.split('&'))  # TODO: more checks

        self.cmd('storage blob update -n {} -c {} --content-type application/test-content'
                 .format(blob_name, container))

        self.cmd('storage blob show -n {} -c {}'.format(blob_name, container), checks=[
            JMESPathCheck('properties.contentSettings.contentType', 'application/test-content'),
            JMESPathCheck('properties.contentLength', file_size_kb * 1024)])

        self.cmd('storage blob service-properties show',
                 checks=JMESPathCheck('hourMetrics.enabled', True))

        if not skip_download:
            downloaded = os.path.join(local_dir, 'test.file')
            self.cmd('storage blob download -n {} -c {} --file {}'
                     .format(blob_name, container, downloaded))
            self.assertTrue(os.path.isfile(downloaded), 'The file is not downloaded.')
            self.assertEqual(file_size_kb * 1024, os.stat(downloaded).st_size,
                             'The download file size is not right.')

        # Verify the requests in cassette to ensure the count of the block requests is expeected
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

    def get_account_key(self, group, name):
        return self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                        .format(name, group)).output


if __name__ == '__main__':
    import unittest

    unittest.main()
