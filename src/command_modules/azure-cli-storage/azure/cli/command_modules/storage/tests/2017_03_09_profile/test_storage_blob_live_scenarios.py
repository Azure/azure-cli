# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, api_version_constraint)
from azure.cli.core.profiles import ResourceType


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageBlobUploadLiveTests(LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_128mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 128 * 1024, 'block')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_64mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 64 * 1024, 'block')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_256mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 256 * 1024, 'block')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_1G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 1024 * 1024, 'block')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_2G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 2 * 1024 * 1024,
                                             'block')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_10G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 10 * 1024 * 1024,
                                             'block', skip_download=True)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_page_blob_upload_10G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 10 * 1024 * 1024,
                                             'page', skip_download=True)

    def verify_blob_upload_and_download(self, group, account, file_size_kb, blob_type,
                                        skip_download=False):
        container = self.create_random_name(prefix='cont', length=24)
        local_dir = self.create_temp_dir()
        local_file = self.create_temp_file(file_size_kb, full_random=True)
        blob_name = self.create_random_name(prefix='blob', length=24)
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                               .format(account, group)).output

        self.set_env('AZURE_STORAGE_ACCOUNT', account)
        self.set_env('AZURE_STORAGE_KEY', account_key)

        self.cmd('storage container create -n {}'.format(container))

        self.cmd('storage blob exists -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('exists', False))

        self.cmd('storage blob upload -c {} -f "{}" -n {} --type {}'
                 .format(container, local_file, blob_name, blob_type))

        self.cmd('storage blob exists -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('exists', True))

        self.cmd('storage blob show -n {} -c {}'.format(blob_name, container),
                 checks=JMESPathCheck('properties.contentLength', file_size_kb * 1024))

        if not skip_download:
            downloaded = os.path.join(local_dir, 'test.file')
            self.cmd('storage blob download -n {} -c {} --file "{}"'
                     .format(blob_name, container, downloaded))
            self.assertTrue(os.path.isfile(downloaded), 'The file is not downloaded.')
            self.assertEqual(file_size_kb * 1024, os.stat(downloaded).st_size,
                             'The download file size is not right.')
