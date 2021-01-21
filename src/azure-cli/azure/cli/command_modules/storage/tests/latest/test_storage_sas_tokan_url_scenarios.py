# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import requests
from datetime import datetime, timedelta
from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, NoneCheck, StringCheck, StringContainCheck)
from ..storage_test_util import StorageScenarioMixin


class StorageFileShareScenarios(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_file_url_sas_token_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        share = self.create_share(account_info)
        source_file = self.create_temp_file(128, full_random=False)
        filename = "sample_file.bin"
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        self.storage_cmd('storage share exists -n {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage file upload --share-name {} --source "{}" -p {}', account_info,
                         share, source_file, filename)
        self.storage_cmd('storage file exists -s {} -p {}', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', True))

        sas_token = self.cmd(
            'storage file generate-sas -s {} -p {} --permissions rw --https-only --expiry {} --account-name {} -otsv'.format(
                share, filename, expiry, storage_account)).output.strip()
        # print(sas_token
        file_url = self.cmd(
            'storage file url -s {} -p {} --account-name {} --sas-token "{}" -otsv'.format(
                share, filename, storage_account, sas_token)).output.strip()
        self.assertIn('?' + sas_token, file_url)
        self.assertEqual(requests.get(file_url).status_code, 200)


class StorageBlobShareScenarios(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_url_sas_token_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        container = self.create_container(account_info)
        source_file = self.create_temp_file(128, full_random=False)
        blob = "blob 1"
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        self.storage_cmd('storage container exists -n {}', account_info, container) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage blob upload -c {} -f "{}" -n "{}"', account_info,
                         container, source_file, blob)
        self.storage_cmd('storage blob exists -c {} -n "{}"', account_info, container, blob) \
            .assert_with_checks(JMESPathCheck('exists', True))

        sas_token = self.storage_cmd(
            'storage blob generate-sas -c {} -n "{}" --permissions rw --https-only --expiry {} --account-name {} -otsv',
            account_info, container, blob, expiry, storage_account).output.strip()
        # print(sas_token
        blob_url = self.storage_cmd(
            'storage blob url -c {} -n "{}" --account-name {} --sas-token "{}" -otsv', account_info,
            container, blob, storage_account, sas_token).output.strip()
        self.assertIn('?' + sas_token, blob_url)
        self.assertEqual(requests.get(blob_url).status_code, 200)

        sas_token_uri = self.storage_cmd(
            'storage blob generate-sas -c {} -n "{}" --permissions rw --https-only --expiry {} --account-name {} --full-uri -otsv',
            account_info, container, blob, expiry, storage_account).output.strip()

        self.assertIn("blob%201", sas_token_uri)
        self.assertEqual(sas_token_uri, blob_url)
