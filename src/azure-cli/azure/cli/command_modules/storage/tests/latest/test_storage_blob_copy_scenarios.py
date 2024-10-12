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
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage blob generate-sas -c {} -n src --permissions r --start {}'
                               ' --expiry {}', account_info, source_container, start,
                               expiry).output.strip()

        self.storage_cmd('storage blob copy start -b dst -c {} --source-blob src --sas-token {} --source-container {} '
                         '--source-if-unmodified-since {} --destination-if-modified-since {}',
                         account_info, target_container, sas, source_container, expiry, expiry)

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

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account1', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='account2', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='accountpremium', sku='Premium_LRS', kind='StorageV2')
    def test_storage_blob_copy_destination_blob_type(self, resource_group, account1, account2, accountpremium):
        source_file = self.create_temp_file(16, full_random=True)
        account1_info = self.get_account_info(resource_group, account1)
        account2_info = self.get_account_info(resource_group, account2)
        accountpremium_info = self.get_account_info(resource_group, accountpremium)

        # Prepare
        source_container = self.create_container(account1_info)
        target_container = self.create_container(account1_info)
        target_container_different_account = self.create_container(account2_info)
        target_container_premium = self.create_container(accountpremium_info)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n srcBlockBlob', account1_info,
                         source_container, source_file)

        # same account
        dst_types = ['', 'Detect', 'BlockBlob', 'AppendBlob', 'PageBlob']
        src_type = 'BlockBlob'
        src_blob_name = 'srcBlockBlob'
        for dst_type in dst_types:
            self.storage_cmd('storage blob copy start --destination-blob {} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob {} '
                             '{}',
                             account1_info, 'dst'+dst_type, target_container, account1, source_container,
                             src_blob_name, '--destination-blob-type '+dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob show -c {} -n {}', account1_info, target_container, 'dst'+dst_type). \
                assert_with_checks([JMESPathCheck('properties.blobType',
                                                  dst_type if (dst_type != '' and dst_type != 'Detect')
                                                  else src_type)])

        src_type = 'AppendBlob'
        src_blob_name = 'dstAppendBlob'
        for dst_type in dst_types:
            self.storage_cmd('storage blob copy start --destination-blob {} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob {} '
                             '{}',
                             account1_info, 'dst2' + dst_type, target_container, account1, target_container,
                             src_blob_name, '--destination-blob-type ' + dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob show -c {} -n {}', account1_info, target_container, 'dst2' + dst_type). \
                assert_with_checks([JMESPathCheck('properties.blobType',
                                                  dst_type if (dst_type != '' and dst_type != 'Detect')
                                                  else src_type)])

        src_type = 'PageBlob'
        src_blob_name = 'dstPageBlob'
        for dst_type in dst_types:
            self.storage_cmd('storage blob copy start --destination-blob {} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob {} '
                             '{}',
                             account1_info, 'dst3' + dst_type, target_container, account1, target_container,
                             src_blob_name, '--destination-blob-type ' + dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob show -c {} -n {}', account1_info, target_container, 'dst3' + dst_type). \
                assert_with_checks([JMESPathCheck('properties.blobType',
                                                  dst_type if (dst_type != '' and dst_type != 'Detect')
                                                  else src_type)])

        # tier
        # specify dst-blob-type BlockBlob
        tiers = ['Cold', 'Cool', 'Hot', 'Archive']
        for tier in tiers:
            self.storage_cmd('storage blob copy start --destination-blob dsttier{} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob srcBlockBlob '
                             '--destination-blob-type BlockBlob --tier {}',
                             account1_info, tier, target_container, account1, source_container, tier)
            self.storage_cmd('storage blob show -c {} -n {}', account1_info, target_container, 'dsttier'+tier). \
                assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        # does not specify dst-blob-type BlockBlob
        for tier in tiers:
            self.storage_cmd('storage blob copy start --destination-blob dsttier2{} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob srcBlockBlob '
                             '--tier {}',
                             account1_info, tier, target_container, account1, source_container, tier)
            self.storage_cmd('storage blob show -c {} -n {}', account1_info, target_container, 'dsttier2'+tier). \
                assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        self.storage_cmd('storage blob copy start --destination-blob dstpremium --destination-container {} '
                         '--source-account-name {} --source-container {} --source-blob srcBlockBlob '
                         '--destination-blob-type PageBlob',
                         accountpremium_info, target_container_premium, account1, source_container)

        # does not specify dst-blob-type PageBlob Premium
        tiers = ['P10', 'P20', 'P30', 'P40', 'P50', 'P60', 'P4', 'P6']
        for tier in tiers:
            self.storage_cmd('storage blob copy start --destination-blob dstpremiumtier{} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob dstpremium --tier {}',
                             accountpremium_info, tier, target_container_premium, accountpremium, target_container_premium, tier)
            self.storage_cmd('storage blob show -c {} -n {}', accountpremium_info, target_container_premium,
                             'dstpremiumtier'+tier).assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        # different account
        src_type = 'BlockBlob'
        src_blob_name = 'srcBlockBlob'
        for dst_type in dst_types:
            self.storage_cmd('storage blob copy start --destination-blob {} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob {} '
                             '{}',
                             account2_info, 'dst' + dst_type, target_container_different_account, account1,
                             source_container, src_blob_name,
                             '--destination-blob-type ' + dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob show -c {} -n {}', account2_info, target_container_different_account,
                             'dst' + dst_type).\
                assert_with_checks([JMESPathCheck('properties.blobType',
                                                  dst_type if (dst_type != '' and dst_type != 'Detect')
                                                  else src_type)])

        src_type = 'AppendBlob'
        src_blob_name = 'dstAppendBlob'
        for dst_type in dst_types:
            self.storage_cmd('storage blob copy start --destination-blob {} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob {} '
                             '{}',
                             account2_info, 'dst2' + dst_type, target_container_different_account, account1,
                             target_container, src_blob_name,
                             '--destination-blob-type ' + dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob show -c {} -n {}', account2_info, target_container_different_account, 'dst2' + dst_type). \
                assert_with_checks([JMESPathCheck('properties.blobType',
                                                  dst_type if (dst_type != '' and dst_type != 'Detect')
                                                  else src_type)])

        src_type = 'PageBlob'
        src_blob_name = 'dstPageBlob'
        for dst_type in dst_types:
            self.storage_cmd('storage blob copy start --destination-blob {} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob {} '
                             '{}',
                             account2_info, 'dst3' + dst_type, target_container_different_account, account1,
                             target_container, src_blob_name,
                             '--destination-blob-type ' + dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob show -c {} -n {}', account2_info, target_container_different_account, 'dst3' + dst_type). \
                assert_with_checks([JMESPathCheck('properties.blobType',
                                                  dst_type if (dst_type != '' and dst_type != 'Detect')
                                                  else src_type)])

        # tier
        # specify dst-blob-type BlockBlob
        tiers = ['Cold', 'Cool', 'Hot', 'Archive']
        for tier in tiers:
            self.storage_cmd('storage blob copy start --destination-blob dsttier3{} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob srcBlockBlob '
                             '--destination-blob-type BlockBlob --tier {}',
                             account2_info, tier, target_container_different_account, account1, source_container, tier)
            self.storage_cmd('storage blob show -c {} -n {}', account2_info, target_container_different_account, 'dsttier3'+tier). \
                assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        # does not specify dst-blob-type BlockBlob
        for tier in tiers:
            self.storage_cmd('storage blob copy start --destination-blob dsttier4{} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob srcBlockBlob '
                             '--tier {}',
                             account2_info, tier, target_container_different_account, account1, source_container, tier)
            self.storage_cmd('storage blob show -c {} -n {}', account2_info, target_container_different_account, 'dsttier4'+tier). \
                assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        # does not specify dst-blob-type PageBlob Premium
        tiers = ['P10', 'P20', 'P30', 'P40', 'P50', 'P60', 'P4', 'P6']
        for tier in tiers:
            self.storage_cmd('storage blob copy start --destination-blob dstpremiumtier2{} --destination-container {} '
                             '--source-account-name {} --source-container {} --source-blob dstPageBlob --tier {}',
                             accountpremium_info, tier, target_container_premium, account1,
                             target_container, tier)
            self.storage_cmd('storage blob show -c {} -n {}', accountpremium_info, target_container_premium,
                             'dstpremiumtier' + tier).assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account1', kind='StorageV2', hns=True)
    @StorageAccountPreparer(parameter_name='account2', kind='StorageV2')
    def test_storage_blob_copy_batch(self, resource_group, account1, account2):
        source_file = self.create_temp_file(16, full_random=False)
        source_file2 = self.create_temp_file(16, full_random=False)

        for src_account, dst_account in [(account1, account1), (account2, account2), (account1, account2),
                                         (account2, account1)]:
            src_account_info = self.get_account_info(resource_group, src_account)
            dst_account_info = self.get_account_info(resource_group, dst_account)
            src_container = self.create_container(src_account_info)
            dst_container = self.create_container(dst_account_info)
            src_share = self.create_share(src_account_info)

            blobs = ['blobğşŞ', 'blogÉ®']
            for blob_name in blobs:
                self.storage_cmd('storage blob upload -c {} -f "{}" -n {}', src_account_info,
                                 src_container, source_file, blob_name)

            self.storage_cmd('storage fs directory create -f {} -n newdir', src_account_info, src_container)

            # empty dir will be skipped when copy from hns to hns
            copied_file = 2 if (src_account, dst_account) == (account1, account1) else 3
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --source-account-key {}',
                             dst_account_info, dst_container, src_container, src_account_info[0],
                             src_account_info[1]).assert_with_checks(
                JMESPathCheck('length(@)', copied_file))
            self.storage_cmd('storage blob copy start-batch --destination-container {} --pattern "blob*" '
                             '--source-container {} --source-account-name {} --source-account-key {}',
                             dst_account_info, dst_container, src_container, src_account_info[0],
                             src_account_info[1]).assert_with_checks(
                JMESPathCheck('length(@)', 1))

            # copy from share
            for file in [source_file, source_file2]:
                self.storage_cmd('storage file upload -s {} --source "{}"', src_account_info,
                                 src_share, file)

            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-share {} '
                             '--source-account-name {} --source-account-key {}',
                             dst_account_info, dst_container, src_share, src_account_info[0],
                             src_account_info[1]).assert_with_checks(
                JMESPathCheck('length(@)', 2))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account1', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='account2', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='accountpremium', sku='Premium_LRS', kind='StorageV2')
    def test_storage_blob_copy_batch_destination_blob_type(self, resource_group, account1, account2, accountpremium):
        source_file = self.create_temp_file(16, full_random=False)
        account1_info = self.get_account_info(resource_group, account1)
        account2_info = self.get_account_info(resource_group, account2)
        accountpremium_info = self.get_account_info(resource_group, accountpremium)

        src_container = self.create_container(account1_info)
        src_container_premium = self.create_container(accountpremium_info)
        src_container_block = self.create_container(account1_info)
        src_container_page = self.create_container(account1_info)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n srcBlockBlob -t block', account1_info,
                         src_container, source_file)
        self.storage_cmd('storage blob upload -c {} -f "{}" -n srcAppendBlob -t append', account1_info,
                         src_container, source_file)
        self.storage_cmd('storage blob upload -c {} -f "{}" -n srcPageBlob -t page', account1_info,
                         src_container, source_file)
        self.storage_cmd('storage blob upload -c {} -f "{}" -n srcPrePageBlob -t page', account1_info,
                         src_container_page, source_file)
        self.storage_cmd('storage blob upload -c {} -f "{}" -n srcPrePageBlob -t page', accountpremium_info,
                         src_container_premium, source_file)

        # same account
        dst_types = ['', 'Detect', 'BlockBlob', 'AppendBlob', 'PageBlob']
        src_types = ['BlockBlob', 'AppendBlob', 'PageBlob']
        for dst_type in dst_types:
            if dst_type == 'BlockBlob':
                dst_container = src_container_block
            else:
                dst_container = self.create_container(account1_info)
            dst_container_different_account = self.create_container(account2_info)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --source-account-key {} '
                             '{}',
                             account1_info, dst_container, src_container,
                             account1_info[0], account1_info[1],
                             '--destination-blob-type ' + dst_type if dst_type != '' else '')
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --source-account-key {} '
                             '{}',
                             account2_info, dst_container_different_account, src_container,
                             account1_info[0], account1_info[1],
                             '--destination-blob-type ' + dst_type if dst_type != '' else '')
            for src_type in src_types:
                blob_name = 'src' + src_type
                self.storage_cmd('storage blob show -c {} -n {}', account1_info, dst_container, blob_name). \
                    assert_with_checks([JMESPathCheck('properties.blobType',
                                                      dst_type if (dst_type != '' and dst_type != 'Detect')
                                                      else src_type)])
                self.storage_cmd('storage blob show -c {} -n {}', account2_info, dst_container_different_account,
                                 blob_name). \
                    assert_with_checks([JMESPathCheck('properties.blobType',
                                                      dst_type if (dst_type != '' and dst_type != 'Detect')
                                                      else src_type)])

        # tier
        # specify dst-blob-type BlockBlob
        tiers = ['Cold', 'Cool', 'Hot', 'Archive']
        blob_names = ['srcBlockBlob', 'srcAppendBlob', 'srcPageBlob']
        for tier in tiers:
            dst_container = self.create_container(account1_info)
            dst_container_different_account = self.create_container(account2_info)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --destination-blob-type BlockBlob --tier {}',
                             account1_info, dst_container, src_container_block, account1, tier)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --source-account-key {} --destination-blob-type BlockBlob'
                             ' --tier {}',
                             account2_info, dst_container_different_account, src_container_block,
                             account1_info[0], account1_info[1], tier)
            for blob_name in blob_names:
                self.storage_cmd('storage blob show -c {} -n {}', account1_info, dst_container, blob_name). \
                    assert_with_checks([JMESPathCheck('properties.blobTier', tier)])
                self.storage_cmd('storage blob show -c {} -n {}', account2_info, dst_container_different_account,
                                 blob_name). assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        # does not specify dst-blob-type BlockBlob
        for tier in tiers:
            dst_container = self.create_container(account1_info)
            dst_container_different_account = self.create_container(account2_info)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --tier {}',
                             account1_info, dst_container, src_container_block, account1, tier)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --source-account-key {} --tier {}',
                             account2_info, dst_container_different_account, src_container_block,
                             account1_info[0], account1_info[1], tier)
            for blob_name in blob_names:
                self.storage_cmd('storage blob show -c {} -n {}', account1_info, dst_container, blob_name). \
                    assert_with_checks([JMESPathCheck('properties.blobTier', tier)])
                self.storage_cmd('storage blob show -c {} -n {}', account2_info, dst_container_different_account,
                                 blob_name).assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

        # does not specify dst-blob-type PageBlob Premium
        tiers = ['P10', 'P20', 'P30', 'P40', 'P50', 'P60', 'P4', 'P6']
        for tier in tiers:
            dst_container = self.create_container(accountpremium_info)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --tier {}',
                             accountpremium_info, dst_container, src_container_premium, accountpremium, tier)
            self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                             '--source-account-name {} --source-account-key {} --tier {}',
                             accountpremium_info, dst_container, src_container_page,
                             account1_info[0], account1_info[1], tier)
            self.storage_cmd('storage blob show -c {} -n srcPrePageBlob', accountpremium_info, dst_container). \
                assert_with_checks([JMESPathCheck('properties.blobTier', tier)])
            self.storage_cmd('storage blob show -c {} -n srcPrePageBlob', accountpremium_info, dst_container). \
                assert_with_checks([JMESPathCheck('properties.blobTier', tier)])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='storageV2')
    def test_storage_blob_copy_batch_rehydrate_priority(self, resource_group, storage_account):
        source_file_1 = self.create_temp_file(16)
        source_file_2 = self.create_temp_file(16)
        account_info = self.get_account_info(resource_group, storage_account)
        src_name_1 = self.create_random_name('blob', 16)
        src_name_2 = self.create_random_name('blob', 16)

        source_container = self.create_container(account_info)
        target_container = self.create_container(account_info)

        for src in [(source_file_1, src_name_1), (source_file_2, src_name_2)]:
            self.storage_cmd('storage blob upload -c {} -f "{}" -n {} ', account_info,
                             source_container, src[0], src[1])
            self.storage_cmd('storage blob set-tier -c {} -n {} --tier Archive', account_info,
                             source_container, src[1])
            self.storage_cmd('az storage blob show -c {} -n {} ', account_info, source_container, src[1]) \
                .assert_with_checks(JMESPathCheck('properties.blobTier', 'Archive'))

        self.storage_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                         '--source-account-name {} --source-account-key {} --tier Cool -r High', account_info,
                         target_container, source_container, account_info[0], account_info[1])
        for src in [src_name_1, src_name_2]:
            self.storage_cmd('storage blob show -c {} -n {} ', account_info, target_container, src) \
                .assert_with_checks(JMESPathCheck('properties.blobTier', 'Archive'),
                                    JMESPathCheck('properties.rehydrationStatus', 'rehydrate-pending-to-cool'))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2', parameter_name='source_account', location='westus')
    @StorageAccountPreparer(kind='StorageV2', parameter_name='target_account', location='westeurope')
    def test_storage_blob_show_with_copy_in_progress(self, resource_group, source_account, target_account):
        source_file = self.create_temp_file(4*1000*1000)
        source_account_info = self.get_account_info(resource_group, source_account)
        target_account_info = self.get_account_info(resource_group, target_account)
        source_blob = self.create_random_name('blob', 16)
        target_blob = self.create_random_name('blob', 16)

        source_container = self.create_container(source_account_info)
        target_container = self.create_container(target_account_info)

        self.storage_cmd('storage blob upload -c {} -f "{}" -n {} --type page', source_account_info,
                         source_container, source_file, source_blob)
        self.storage_cmd('storage blob copy start --source-account-name {} --source-container {} --source-blob {} '
                         '--destination-container {} --destination-blob {}', target_account_info,
                         source_account, source_container, source_blob, target_container, target_blob)
        self.storage_cmd('storage blob show -n {} -c {}', target_account_info, target_blob, target_container)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='source_account', allow_shared_key_access=False)
    @StorageAccountPreparer(parameter_name='target_account', allow_shared_key_access=False)
    def test_storage_blob_copy_oauth(self, resource_group, source_account, target_account):
        source_file = self.create_temp_file(16, full_random=True)
        source_account_info = self.get_account_info(resource_group, source_account)
        target_account_info = self.get_account_info(resource_group, target_account)

        with open(source_file, 'rb') as f:
            expect_content = f.read()

        source_container = self.create_container(source_account_info, oauth=True)
        target_container = self.create_container(target_account_info, oauth=True)
        source_blob = 'srcblob'
        target_blob = 'dstblob'

        self.oauth_cmd('storage blob upload -c {} -f "{}" -n {} --account-name {}'.format(
            source_container, source_file, source_blob, source_account))

        self.oauth_cmd('storage blob copy start -b {} -c {} --source-blob {} --source-account-name {} '
                       '--source-container {} --account-name {}'.format(
            target_blob, target_container, source_blob, source_account, source_container, target_account))

        from time import sleep, time
        start = time()
        while True:
            # poll until copy has succeeded
            blob = self.oauth_cmd('storage blob show -c {} -n {} --account-name {}'.format(
                target_container, target_blob, target_account)).get_output_in_json()
            if blob["properties"]["copy"]["status"] == "success" or time() - start > 10:
                break
            sleep(1)

        target_file = self.create_temp_file(1)
        self.oauth_cmd('storage blob download -c {} -n {} -f "{}" --account-name {}'.format(
            target_container, target_blob, target_file, target_account))

        with open(target_file, 'rb') as f:
            actual_content = f.read()

        self.assertEqual(expect_content, actual_content)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account1', kind='StorageV2', allow_shared_key_access=False, hns=True)
    @StorageAccountPreparer(parameter_name='account2', kind='StorageV2', allow_shared_key_access=False)
    def test_storage_blob_copy_batch_oauth(self, resource_group, account1, account2):
        source_file = self.create_temp_file(16, full_random=False)
        for src_account, dst_account in [(account1, account1), (account2, account2), (account1, account2),
                                         (account2, account1)]:
            src_account_info = self.get_account_info(resource_group, src_account)
            dst_account_info = self.get_account_info(resource_group, dst_account)
            src_container = self.create_container(src_account_info, oauth=True)
            dst_container = self.create_container(dst_account_info, oauth=True)
            dst_container_2 = self.create_container(dst_account_info, oauth=True)

            blobs = ['blobğşŞ', 'blogÉ®']
            for blob_name in blobs:
                self.oauth_cmd('storage blob upload -c {} -f "{}" -n {} --account-name {}',
                               src_container, source_file, blob_name, src_account)

            self.oauth_cmd('storage fs directory create -f {} -n newdir --account-name {}', src_container, src_account)

            # empty dir will be skipped when copy from hns to hns
            copied_file = 2 if (src_account, dst_account) == (account1, account1) else 3
            self.oauth_cmd('storage blob copy start-batch --destination-container {} --source-container {} '
                           '--source-account-name {} --account-name {}', dst_container, src_container,
                           src_account, dst_account).assert_with_checks(
                JMESPathCheck('length(@)', copied_file))
            self.oauth_cmd('storage blob copy start-batch --destination-container {} --pattern "blob*" '
                           '--source-container {} --source-account-name {} --account-name {}',
                           dst_container_2, src_container, src_account, dst_account).assert_with_checks(
                JMESPathCheck('length(@)', 1))
