# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime, timedelta
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, JMESPathCheckExists, NoneCheck, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk.decorators import serial_test
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageBlobUploadLiveTests(LiveScenarioTest):
    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_128mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 128 * 1024, 'block')

    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_64mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 64 * 1024, 'block')

    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_256mb_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 256 * 1024, 'block')

    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_1G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 1024 * 1024, 'block')

    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_2G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 2 * 1024 * 1024,
                                             'block')

    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload_10G_file(self, resource_group, storage_account):
        self.verify_blob_upload_and_download(resource_group, storage_account, 10 * 1024 * 1024,
                                             'block', skip_download=True)

    @serial_test()
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


    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_upload(self, resource_group, storage_account):
        from azure.cli.core.azclierror import AzureResponseError
        file_size_kb = 128
        local_file = self.create_temp_file(file_size_kb, full_random=True)

        container = self.create_random_name(prefix='cont', length=10)
        blob_name = self.create_random_name(prefix='blob', length=24)
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                               .format(storage_account, resource_group)).output

        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)

        self.cmd('storage container create -n {}'.format(container))
        # test upload through file path
        self.cmd('storage blob upload -c {} -f "{}" -n {}'.format(container, local_file, blob_name))

        self.cmd('storage blob exists -n {} -c {}'.format(blob_name, container), checks=JMESPathCheck('exists', True))

        self.cmd('storage blob show -n {} -c {}'.format(blob_name, container), checks=[
            JMESPathCheck('properties.contentLength', file_size_kb * 1024),
            JMESPathCheck('name', blob_name)])

        # test upload from data
        self.cmd('storage blob upload -c {} --data {} --length 4 -n {} --overwrite'.format(
            container, "test", blob_name))
        self.cmd('storage blob show -n {} -c {}'.format(blob_name, container), checks=[
            JMESPathCheck('properties.contentLength', 4),
            JMESPathCheck('name', blob_name)])


@api_version_constraint(ResourceType.DATA_STORAGE_BLOB, min_api='2019-12-12')
class StorageBlobQueryTests(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2')
    def test_storage_blob_query_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(group=resource_group, name=storage_account)
        container = self.create_container(account_info)
        csv_blob = self.create_random_name(prefix='csvblob', length=12)
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        csv_file = os.path.join(curr_dir, 'quick_query.csv').replace('\\', '\\\\')

        # test csv input
        self.storage_cmd('storage blob upload -f "{}" -c {} -n {}', account_info, csv_file, container, csv_blob)
        query_string = "SELECT _2 from BlobStorage"
        result = self.storage_cmd('storage blob query -c {} -n {} --query-expression "{}"',
                                  account_info, container, csv_blob, query_string).output
        self.assertIsNotNone(result)

        # test csv output
        temp_dir = self.create_temp_dir()
        result_file = os.path.join(temp_dir, 'result.csv')
        self.assertFalse(os.path.exists(result_file))
        self.storage_cmd('storage blob query -c {} -n {} --query-expression "{}" --result-file "{}"',
                         account_info, container, csv_blob, query_string, result_file)
        self.assertTrue(os.path.exists(result_file))

        json_blob = self.create_random_name(prefix='jsonblob', length=12)
        json_file = os.path.join(curr_dir, 'quick_query.json').replace('\\', '\\\\')

        # test json input
        self.storage_cmd('storage blob upload -f "{}" -c {} -n {}', account_info, json_file, container, json_blob)
        query_string = "SELECT latitude FROM BlobStorage[*].warehouses[*]"
        result = self.storage_cmd('storage blob query -c {} -n {} --query-expression "{}" --input-format json',
                                  account_info, container, json_blob, query_string).output
        self.assertIsNotNone(result)
