# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import shutil
import datetime
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck)


class StorageBlobTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_small_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 1, 'block')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_midsize_file(self, resource_group, storage_account):
        # generate a 4MB file. the download test is skip for now to avoid huge recording file. the test harness will
        # be updated later to support recording file download.
        self.verify_blob_upload_and_download(resource_group, storage_account, 4096, 'block')

    def verify_blob_upload_and_download(self, group, account, file_size_kb, blob_type, skip_download=False):
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

        expiry = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.cmd('storage blob generate-sas -n {} -c {} --expiry {} '
                       '--permissions r --https-only'.format(blob_name, container, expiry)).output
        assert dict(pair.split('=') for pair in sas.split('&'))   # TODO: more checks

        self.cmd('storage blob update -n {} -c {} --content-type application/test-content'.format(blob_name, container))
        self.cmd('storage blob show -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('properties.contentSettings.contentType', 'application/test-content'))

        self.cmd('storage blob service-properties show', checks=JMESPathCheck('hourMetrics.enabled', True))

        if not skip_download:
            downloaded = os.path.join(local_dir, 'test.file')
            self.cmd('storage blob download -n {} -c {} --file {}'.format(blob_name, container, downloaded))
            assert os.path.isfile(downloaded)
            assert os.stat(downloaded).st_size == file_size_kb * 1024

    def get_account_key(self, group, name):
        return self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                        .format(name, group)).output

    def create_temp_file(self, size_kb):
        _, path = tempfile.mkstemp()
        self.addCleanup(lambda: os.remove(path))

        with open(path, mode='r+b') as file:
            chunk = bytearray([0] * 1024)
            for i in range(size_kb):
                file.write(chunk)

        return path

    def create_temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        return temp_dir
