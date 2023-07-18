# This Python file uses the following encoding: utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck
from ..storage_test_util import StorageScenarioMixin


class StorageCopyTests(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_copy_non_ascii(self, storage_account_info):
        src_container = self.create_container(storage_account_info)
        dst_container = self.create_container(storage_account_info)

        source_file = self.create_temp_file(16, full_random=False)
        blobs = ['blobğşŞ', 'blobÉ®']

        for blob_name in blobs:
            self.storage_cmd('storage blob upload -c {} -f "{}" -n {}', storage_account_info,
                             src_container, source_file, blob_name)
            self.storage_cmd('storage blob exists -c {} -n {}', storage_account_info,
                             src_container, blob_name).assert_with_checks(JMESPathCheck('exists', True))
            url = self.storage_cmd('storage blob url -n {} -c {}', storage_account_info,
                                   blob_name, src_container).get_output_in_json()
            self.storage_cmd('storage blob copy start -c {} -b {} -u {}',
                             storage_account_info, dst_container, blob_name, url).assert_with_checks([
                                 JMESPathCheck('copy_status', "success")])
            self.storage_cmd('storage blob exists -c {} -n {}', storage_account_info,
                             dst_container, blob_name).assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage blob copy start-batch --destination-container {} --pattern * --source-container {}',
                         storage_account_info, dst_container, src_container).assert_with_checks(
                             JMESPathCheck('length(@)', 2))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_file_copy_non_ascii(self, storage_account_info):
        src_share = self.create_share(storage_account_info)
        dst_share = self.create_share(storage_account_info)

        source_dir = self.create_temp_dir()
        files = ['fileğşŞ', 'file的Φ']
        for file_name in files:
            with open(os.path.join(source_dir, file_name), 'wb') as temp_file:
                temp_file.write(bytearray([0] * 1024))
            self.storage_cmd('storage file upload -s {} --source "{}"', storage_account_info,
                             src_share, os.path.join(source_dir, file_name))
            self.storage_cmd('storage file exists -s {} -p "{}"', storage_account_info,
                             src_share, file_name).assert_with_checks(JMESPathCheck('exists', True))
            url = self.storage_cmd('storage file url -p "{}" -s {}', storage_account_info,
                                   file_name, src_share).get_output_in_json()
            self.storage_cmd('storage file copy start -s {} -p "{}" -u {}',
                             storage_account_info, dst_share, file_name, url).assert_with_checks([
                                 JMESPathCheck('status', "success")])
            self.storage_cmd('storage file exists -s {} -p "{}"', storage_account_info,
                             dst_share, file_name).assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage file copy start-batch --destination-share {} --pattern * --source-share {}',
                         storage_account_info, dst_share, src_share).assert_with_checks(
                             JMESPathCheck('length(@)', 2))
