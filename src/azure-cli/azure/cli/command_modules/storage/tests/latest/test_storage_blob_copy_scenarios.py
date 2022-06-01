# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck
from ..storage_test_util import StorageScenarioMixin


class StorageBlobCopyTests(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='source_account')
    @StorageAccountPreparer(parameter_name='target_account')
    def test_storage_blob_copy_with_sas_and_snapshot(self, resource_group, source_account, target_account):
        source_file = self.create_temp_file(16, full_random=True)
        source_account_info = self.get_account_info(resource_group, source_account)
        target_account_info = self.get_account_info(resource_group, target_account)

        with open(source_file, 'rb') as f:
            expect_content = f.read()

        source_container = self.create_container(source_account_info)
        target_container = self.create_container(target_account_info)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n src', source_account_info,
                         source_container, source_file)

        snapshot = self.storage_cmd('storage blob snapshot -c {} -n src', source_account_info,
                                    source_container).get_output_in_json()['snapshot']

        source_file = self.create_temp_file(24, full_random=True)
        self.storage_cmd('storage blob upload -c {} -f "{}" -n src --overwrite', source_account_info,
                         source_container, source_file)

        from datetime import datetime, timedelta
        start = datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')
        expiry = (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage blob generate-sas -c {} -n src --permissions r --start {}'
                               ' --expiry {}', source_account_info, source_container, start,
                               expiry).output.strip()

        self.storage_cmd('storage blob copy start -b dst -c {} --source-blob src --source-sas {} '
                         '--source-account-name {} --source-container {} --source-snapshot {}',
                         target_account_info, target_container, sas, source_account,
                         source_container, snapshot)

        from time import sleep, time
        start = time()
        while True:
            # poll until copy has succeeded
            blob = self.storage_cmd('storage blob show -c {} -n dst',
                                    target_account_info, target_container).get_output_in_json()
            if blob["properties"]["copy"]["status"] == "success" or time() - start > 10:
                break
            sleep(.1)

        target_file = self.create_temp_file(1)
        self.storage_cmd('storage blob download -c {} -n dst -f "{}"', target_account_info,
                         target_container, target_file)

        with open(target_file, 'rb') as f:
            actual_content = f.read()

        self.assertEqual(expect_content, actual_content)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_copy_same_account_sas(self, resource_group, storage_account):
        source_file = self.create_temp_file(16, full_random=True)
        account_info = self.get_account_info(resource_group, storage_account)

        with open(source_file, 'rb') as f:
            expect_content = f.read()

        source_container = self.create_container(account_info)
        target_container = self.create_container(account_info)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n src', account_info,
                         source_container, source_file)

        from datetime import datetime, timedelta
        start = datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')
        expiry = (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage blob generate-sas -c {} -n src --permissions r --start {}'
                               ' --expiry {}', account_info, source_container, start,
                               expiry).output.strip()

        self.storage_cmd('storage blob copy start -b dst -c {} --source-blob src --sas-token {} --source-container {} '
                         '--source-if-unmodified-since "2021-06-29T06:32Z" --destination-if-modified-since '
                         '"2020-06-29T06:32Z" ', account_info, target_container, sas, source_container)

        from time import sleep, time
        start = time()
        while True:
            # poll until copy has succeeded
            blob = self.storage_cmd('storage blob show -c {} -n dst',
                                    account_info, target_container).get_output_in_json()
            if blob["properties"]["copy"]["status"] == "success" or time() - start > 10:
                break
            sleep(.1)

        target_file = self.create_temp_file(1)
        self.storage_cmd('storage blob download -c {} -n dst -f "{}"', account_info,
                         target_container, target_file)

        with open(target_file, 'rb') as f:
            actual_content = f.read()

        self.assertEqual(expect_content, actual_content)

        # test source sas-token input starting with '?'
        if not sas.startswith('?'):
            sas = '?' + sas

        target_container = self.create_container(account_info)
        self.storage_cmd('storage blob copy start -b dst -c {} --source-blob src --source-sas {} --source-container {}',
                         account_info, target_container, sas, source_container)

        start = time()
        while True:
            blob = self.storage_cmd('storage blob show -c {} -n dst',
                                    account_info, target_container).get_output_in_json()
            if blob["properties"]["copy"]["status"] == "success" or time() - start > 10:
                break
            sleep(.1)

        target_file = self.create_temp_file(1)
        self.storage_cmd('storage blob download -c {} -n dst -f "{}"', account_info,
                         target_container, target_file)

        with open(target_file, 'rb') as f:
            actual_content = f.read()

        self.assertEqual(expect_content, actual_content)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account1', kind='storageV2')
    @StorageAccountPreparer(parameter_name='account2', kind='storageV2')
    def test_storage_blob_copy_requires_sync(self, resource_group, account1, account2):
        source_file = self.create_temp_file(16, full_random=True)
        account1_info = self.get_account_info(resource_group, account1)
        account2_info = self.get_account_info(resource_group, account2)

        # Prepare
        source_container = self.create_container(account1_info)
        target_container1 = self.create_container(account1_info)
        target_container2 = self.create_container(account2_info)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n src', account1_info,
                         source_container, source_file)

        # with different account name and account key
        self.storage_cmd('storage blob copy start --destination-blob dst --destination-container {} '
                         '--source-account-name {} --source-container {} --source-blob src --requires-sync true',
                         account2_info, target_container2, account1, source_container)

        # with source uri in the same account
        source_uri = self.storage_cmd('storage blob url -c {} -n src', account1_info, source_container).output
        self.storage_cmd('storage blob copy start -b dst -c {} --source-uri {}', account1_info,
                         target_container1, source_uri)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n pagesrc --type page', account1_info,
                         source_container, source_file)
        source_uri = self.storage_cmd('storage blob url -c {} -n pagesrc', account1_info, source_container).output
        # expect failure with page blob
        self.storage_cmd_negative('storage blob copy start -b dst -c {} --source-uri {} --requires-sync', account1_info,
                                  target_container1, source_uri)


