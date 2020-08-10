# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime, timedelta

import pytest
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, JMESPathCheckExists, NoneCheck, api_version_constraint)
from azure.cli.core.profiles import ResourceType


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageBlobUploadLiveTests(LiveScenarioTest):

    @pytest.mark.serial()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_128mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 128 * 1024, 'block')

    @pytest.mark.serial()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_64mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 64 * 1024, 'block')

    @pytest.mark.serial()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_256mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 256 * 1024, 'block')

    @pytest.mark.serial()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_1G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 1024 * 1024, 'block')

    @pytest.mark.serial()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_2G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 2 * 1024 * 1024,
                                             'block')

    @pytest.mark.serial()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_10G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 10 * 1024 * 1024,
                                             'block', skip_download=True)

    @pytest.mark.serial()
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
                 checks=[JMESPathCheck('properties.contentLength', file_size_kb * 1024),
                         JMESPathCheckExists('properties.pageRanges') if blob_type == 'page' else
                         JMESPathCheck('properties.pageRanges', None)])

        if not skip_download:
            downloaded = os.path.join(local_dir, 'test.file')
            self.cmd('storage blob download -n {} -c {} --file "{}"'
                     .format(blob_name, container, downloaded))
            self.assertTrue(os.path.isfile(downloaded), 'The file is not downloaded.')
            self.assertEqual(file_size_kb * 1024, os.stat(downloaded).st_size,
                             'The download file size is not right.')

    @ResourceGroupPreparer(name_prefix="storage_blob_restore", location="centraluseuap")
    @StorageAccountPreparer(name_prefix="restore", kind="StorageV2", sku='Standard_LRS', location="centraluseuap")
    def test_storage_blob_restore(self, resource_group, storage_account):
        import time
        self.cmd('storage account blob-service-properties update --enable-change-feed --enable-delete-retention --delete-retention-days 2 --enable-versioning -n {sa}')\
            .assert_with_checks(JMESPathCheck('changeFeed.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.enabled', True),
                                JMESPathCheck('deleteRetentionPolicy.days', 2))
        time.sleep(60)
        # Enable Restore Policy
        self.cmd('storage account blob-service-properties update --enable-restore-policy --restore-days 1 -n {sa}')\
            .assert_with_checks(JMESPathCheck('restorePolicy.enabled', True),
                                JMESPathCheck('restorePolicy.days', 1))

        c1 = self.create_random_name(prefix='containera', length=24)
        c2 = self.create_random_name(prefix='containerb', length=24)
        b1 = self.create_random_name(prefix='blob1', length=24)
        b2 = self.create_random_name(prefix='blob2', length=24)
        b3 = self.create_random_name(prefix='blob3', length=24)
        b4 = self.create_random_name(prefix='blob4', length=24)

        local_file = self.create_temp_file(256)

        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                               .format(storage_account, resource_group)).output

        # Prepare containers and blobs
        for container in [c1, c2]:
            self.cmd('storage container create -n {} --account-name {} --account-key {}'.format(
                container, storage_account, account_key)) \
                .assert_with_checks(JMESPathCheck('created', True))
            for blob in [b1, b2, b3, b4]:
                self.cmd('storage blob upload -c {} -f "{}" -n {} --account-name {} --account-key {}'.format(
                    container, local_file, blob, storage_account, account_key))
            self.cmd('storage blob list -c {} --account-name {} --account-key {}'.format(
                container, storage_account, account_key)) \
                .assert_with_checks(JMESPathCheck('length(@)', 4))

            self.cmd('storage container delete -n {} --account-name {} --account-key {}'.format(
                container, storage_account, account_key)) \
                .assert_with_checks(JMESPathCheck('deleted', True))

        time.sleep(30)

        # Restore blobs, with specific ranges
        time_to_restore = (datetime.utcnow() + timedelta(seconds=-5)).strftime('%Y-%m-%dT%H:%MZ')

        # c1/b1 -> c1/b2
        start_range = '/'.join([c1, b1])
        end_range = '/'.join([c1, b2])
        self.cmd('storage blob restore -t {} -r {} {} --account-name {} -g {}'.format(
            time_to_restore, start_range, end_range, storage_account, resource_group), checks=[
            JMESPathCheck('status', 'Complete'),
            JMESPathCheck('parameters.blobRanges[0].startRange', start_range),
            JMESPathCheck('parameters.blobRanges[0].endRange', end_range)])

        self.cmd('storage blob restore -t {} -r {} {} --account-name {} -g {} --no-wait'.format(
            time_to_restore, start_range, end_range, storage_account, resource_group))

        time.sleep(90)

        time_to_restore = (datetime.utcnow() + timedelta(seconds=-5)).strftime('%Y-%m-%dT%H:%MZ')
        # c1/b2 -> c2/b3
        start_range = '/'.join([c1, b2])
        end_range = '/'.join([c2, b3])
        self.cmd('storage blob restore -t {} -r {} {} --account-name {} -g {}'.format(
            time_to_restore, start_range, end_range, storage_account, resource_group), checks=[
            JMESPathCheck('status', 'Complete'),
            JMESPathCheck('parameters.blobRanges[0].startRange', start_range),
            JMESPathCheck('parameters.blobRanges[0].endRange', end_range)])

        time.sleep(120)
        self.cmd('storage blob restore -t {} --account-name {} -g {} --no-wait'.format(
            time_to_restore, storage_account, resource_group))
