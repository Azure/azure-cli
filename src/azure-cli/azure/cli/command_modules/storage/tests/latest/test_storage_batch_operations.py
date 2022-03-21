# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime
from azure.cli.testsdk import LiveScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, JMESPathCheck
from ..storage_test_util import StorageScenarioMixin, StorageTestFilesPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class StorageBatchOperationScenarios(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_batch_download_scenarios(self, test_dir, storage_account_info):
        src_container = self.create_container(storage_account_info)

        # upload test files to storage account
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --max-connections 3', storage_account_info,
                         test_dir, src_container)
        from azure.cli.core.azclierror import AzureResponseError
        with self.assertRaises(AzureResponseError):
            self.storage_cmd('storage blob upload-batch -s "{}" -d {} --max-connections 3', storage_account_info,
                                 test_dir, src_container)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --max-connections 3 --overwrite', storage_account_info,
                         test_dir, src_container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 41))

        # download recursively without pattern
        local_folder = self.create_temp_dir()
        cmd = 'storage blob download-batch -s {} -d "{}"'.format(src_container, local_folder)
        self.storage_cmd(cmd, storage_account_info)
        self.assertEqual(41, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download recursively with wild card *, and use URL as source
        local_folder = self.create_temp_dir()
        src_url = self.storage_cmd('storage blob url -c {} -n readme -otsv', storage_account_info, src_container).output
        src_url = src_url[:src_url.rfind('/')]

        self.storage_cmd('storage blob download-batch -s {} -d "{}" --pattern *', storage_account_info, src_url,
                         local_folder)
        self.assertEqual(41, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download recursively with wild card after dir
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage blob download-batch -s {} -d "{}" --pattern {}', storage_account_info, src_container,
                         local_folder, 'apple/*')

        self.assertEqual(10, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download recursively with wild card before name
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage blob download-batch -s {} -d "{}" --pattern {}', storage_account_info, src_container,
                         local_folder, '*/file_0')
        self.assertEqual(4, sum(len(f) for r, d, f in os.walk(local_folder)))

        # upload blobs with names that start with path separator
        local_file = self.create_temp_file(1)
        src_container = self.create_container(storage_account_info)
        blob_names = ['/dir1/file', 'dir1/file', '/dir2//file', 'dir2/file']

        for name in blob_names:
            self.storage_cmd('storage blob upload -c {} -f "{}" -n {} --type block', storage_account_info,
                             src_container, local_file, name)

        # download blobs that start with forward slash into local folder
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage blob download-batch -s {} -d "{}" --pattern {}', storage_account_info, src_container,
                         local_folder, '/*')
        self.assertEqual(2, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download blobs that start with forward slash into local folder with conflicts
        local_folder = self.create_temp_dir()
        self.storage_cmd_negative('storage blob download-batch -s {} -d "{}"', storage_account_info, src_container,
                                  local_folder)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_batch_upload_scenarios(self, test_dir, storage_account_info):
        # upload files without pattern
        container = self.create_container(storage_account_info)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --max-connections 3', storage_account_info,
                         test_dir, container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, container).assert_with_checks(
            JMESPathCheck('length(@)', 41))

        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --content-md 123 --max-connections 3 --overwrite', storage_account_info,
                         test_dir, container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, container).assert_with_checks(
            JMESPathCheck('length(@)', 41))


        # upload files with pattern apple/*
        container = self.create_container(storage_account_info)
        src_url = self.storage_cmd('storage blob url -c {} -n \'\' -otsv', storage_account_info,
                                   container).output.strip()[:-1]
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --pattern apple/*', storage_account_info, test_dir,
                         src_url)
        self.storage_cmd('storage blob list -c {}', storage_account_info, container).assert_with_checks(
            JMESPathCheck('length(@)', 10))

        # upload files with pattern */file_0
        container = self.create_container(storage_account_info)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --pattern */file_0', storage_account_info, test_dir,
                         container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, container).assert_with_checks(
            JMESPathCheck('length(@)', 4))

        # upload files with pattern nonexists/*
        container = self.create_container(storage_account_info)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --pattern nonexists/*', storage_account_info,
                         test_dir, container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, container).assert_with_checks(
            JMESPathCheck('length(@)', 0))

        # upload files while specifying container path
        container = self.create_container(storage_account_info)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {} --pattern */file_0 --destination-path some_dir',
                         storage_account_info, test_dir, container)
        self.storage_cmd('storage blob list -c {} --prefix some_dir',
                         storage_account_info, container).assert_with_checks(JMESPathCheck('length(@)', 4))

        # upload-batch with preconditon
        self.storage_cmd('storage blob upload-batch -d {} -s "{}"',
                                  storage_account_info, container, test_dir)
        import time
        from datetime import datetime
        time.sleep(1)
        current = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        time.sleep(1)
        result = self.storage_cmd('storage blob upload-batch -d {} -s "{}" --if-modified-since {}',
                                  storage_account_info, container, test_dir, current).get_output_in_json()
        self.assertEqual(len(result), 0)
        result = self.storage_cmd('storage blob upload-batch -d {} -s "{}" --if-modified-since {} --overwrite',
                                  storage_account_info, container, test_dir, current).get_output_in_json()
        self.assertEqual(len(result), 0)
        result = self.storage_cmd('storage blob upload-batch -d {} -s "{}" --if-unmodified-since {}',
                                  storage_account_info,
                                  container, test_dir, current).get_output_in_json()
        self.assertEqual(len(result), 41)

        #check result url
        result = self.storage_cmd('storage blob upload-batch -s "{}" -d {} --overwrite', storage_account_info,
                         test_dir, container).get_output_in_json()
        for res in result:
            self.assertRegex(res['Blob'], '^.*[^\/]+$')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_file_batch_download_scenarios(self, test_dir, storage_account_info):
        src_share = self.create_share(storage_account_info)
        # Prepare files
        snapshot = self.storage_cmd('storage share snapshot -n {} ',
                                    storage_account_info, src_share).get_output_in_json()["snapshot"]
        self.storage_cmd('storage file upload-batch -s "{}" -d {} --max-connections 3', storage_account_info,
                         test_dir, src_share)

        # download without pattern
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file download-batch -s {} -d "{}"', storage_account_info, src_share, local_folder)
        self.assertEqual(41, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download with pattern apple/*
        local_folder = self.create_temp_dir()
        share_url = self.storage_cmd('storage file url -s {} -p \'\' -otsv', storage_account_info,
                                     src_share).output.strip()[:-1]
        self.storage_cmd('storage file download-batch -s {} -d "{}" --pattern apple/*', storage_account_info, share_url,
                         local_folder)
        self.assertEqual(10, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download with pattern */file0
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file download-batch -s {} -d "{}" --pattern */file_0', storage_account_info,
                         src_share, local_folder)
        self.assertEqual(4, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download with pattern nonexsits/*
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file download-batch -s {} -d "{}" --pattern nonexists/*', storage_account_info,
                         src_share, local_folder)
        self.assertEqual(0, sum(len(f) for r, d, f in os.walk(local_folder)))

        # download with snapshot
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file download-batch -s {} -d "{}" --snapshot {}', storage_account_info,
                         src_share, local_folder, snapshot)
        self.assertEqual(0, sum(len(f) for r, d, f in os.walk(local_folder)))

        snapshot = self.storage_cmd('storage share snapshot -n {} ',
                                    storage_account_info, src_share).get_output_in_json()["snapshot"]
        self.storage_cmd('storage file download-batch -s {} -d "{}" --snapshot {}', storage_account_info,
                         src_share, local_folder, snapshot)
        self.assertEqual(41, sum(len(f) for r, d, f in os.walk(local_folder)))

        local_folder = self.create_temp_dir()
        share_url = self.storage_cmd('storage file url -s {} -p \'\' -otsv', storage_account_info,
                                     src_share).output.strip()[:-1]
        self.storage_cmd('storage file download-batch -s {} -d "{}" --pattern apple/* --snapshot {} ',
                         storage_account_info, share_url, local_folder, snapshot)
        self.assertEqual(10, sum(len(f) for r, d, f in os.walk(local_folder)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_file_batch_upload_scenarios(self, test_dir, storage_account_info):
        # upload without pattern
        src_share = self.create_share(storage_account_info)
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file upload-batch -s "{}" -d {} --max-connections 3', storage_account_info,
                         test_dir, src_share)
        self.storage_cmd('storage file download-batch -s {} -d "{}"', storage_account_info, src_share, local_folder)
        self.assertEqual(41, sum(len(f) for r, d, f in os.walk(local_folder)))

        # upload with pattern apple/*
        src_share = self.create_share(storage_account_info)
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file upload-batch -s "{}" -d {} --pattern apple/*', storage_account_info, test_dir,
                         src_share)
        self.storage_cmd('storage file download-batch -s {} -d "{}"', storage_account_info, src_share, local_folder)
        self.assertEqual(10, sum(len(f) for r, d, f in os.walk(local_folder)))

        # upload with pattern */file_0
        src_share = self.create_share(storage_account_info)
        local_folder = self.create_temp_dir()
        share_url = self.storage_cmd('storage file url -s {} -p \'\' -otsv', storage_account_info,
                                     src_share).output.strip()[:-1]
        self.storage_cmd('storage file upload-batch -s "{}" -d {} --pattern */file_0', storage_account_info, test_dir,
                         share_url)
        self.storage_cmd('storage file download-batch -s {} -d "{}"', storage_account_info, src_share, local_folder)
        self.assertEqual(4, sum(len(f) for r, d, f in os.walk(local_folder)))

        # upload with pattern nonexists/*
        src_share = self.create_share(storage_account_info)
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file upload-batch -s "{}" -d {} --pattern nonexists/*', storage_account_info,
                         test_dir, src_share)
        self.storage_cmd('storage file download-batch -s {} -d "{}"', storage_account_info, src_share, local_folder)
        self.assertEqual(0, sum(len(f) for r, d, f in os.walk(local_folder)))

        # upload while specifying share path
        src_share = self.create_share(storage_account_info)
        local_folder = self.create_temp_dir()
        share_url = self.storage_cmd('storage file url -s {} -p \'\' -otsv', storage_account_info,
                                     src_share).output.strip()[:-1]
        self.storage_cmd('storage file upload-batch -s "{}" -d {} --pattern */file_0 --destination-path some_dir',
                         storage_account_info, test_dir, share_url)
        self.storage_cmd('storage file download-batch -s {} -d "{}" --pattern some_dir*', storage_account_info,
                         src_share, local_folder)
        self.assertEqual(4, sum(len(f) for r, d, f in os.walk(local_folder)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='src_account')
    @StorageAccountPreparer(parameter_name='dst_account')
    @StorageTestFilesPreparer()
    def test_storage_blob_batch_copy(self, src_account_info, dst_account_info, test_dir):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        src_container = self.create_container(src_account_info)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {}', src_account_info, test_dir, src_container)

        src_share = self.create_share(src_account_info)
        self.storage_cmd('storage file upload-batch -s "{}" -d {}', src_account_info, test_dir, src_share)

        # from blob container to container with a sas in same account
        dst_container = self.create_container(src_account_info)

        self.storage_cmd('storage blob copy start-batch --source-container {} '
                         '--destination-container {}', src_account_info, src_container, dst_container)
        self.storage_cmd('storage blob list -c {}',
                         src_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 41))

        # from blob container to container with a sas between different accounts with pattern
        dst_container = self.create_container(dst_account_info)
        sas_token = self.storage_cmd('storage container generate-sas -n {} --permissions rl '
                                     '--expiry {}', src_account_info, src_container, expiry).output
        self.storage_cmd('storage blob copy start-batch --source-container {} '
                         '--destination-container {} --source-sas {} --pattern apple/* '
                         '--source-account-name {}', dst_account_info, src_container, dst_container, sas_token,
                         src_account_info[0])
        self.storage_cmd('storage blob list -c {}',
                         dst_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 10))

        # from blob container to container without a sas between different accounts with pattern
        dst_container = self.create_container(dst_account_info)
        self.storage_cmd('storage blob copy start-batch --source-container {} '
                         '--destination-container {} --source-account-name {} --source-account-key {}'
                         ' --pattern */file_0', dst_account_info, src_container, dst_container, src_account_info[0],
                         src_account_info[1])
        self.storage_cmd('storage blob list -c {}',
                         dst_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 4))

        # from file share to blob container with a sas in same account
        dst_container = self.create_container(src_account_info)

        self.storage_cmd('storage blob copy start-batch --source-share {} --destination-container {}',
                         src_account_info, src_share, dst_container)
        self.storage_cmd('storage blob list -c {}',
                         src_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 41))

        # from file share to blob container with a sas between different accounts with pattern
        dst_container = self.create_container(dst_account_info)
        sas_token = self.storage_cmd('storage share generate-sas -n {} --permissions rl --expiry {} -otsv',
                                     src_account_info, src_share, expiry).output.strip()
        self.storage_cmd('storage blob copy start-batch --source-share {} '
                         '--destination-container {} --source-sas {} --pattern apple/* '
                         '--source-account-name {}', dst_account_info, src_share, dst_container, sas_token,
                         src_account_info[0])
        self.storage_cmd('storage blob list -c {}',
                         dst_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 10))

        # from file share to blob container without a sas between different accounts with pattern
        dst_container = self.create_container(dst_account_info)
        self.storage_cmd('storage blob copy start-batch --source-share {} '
                         '--destination-container {} --source-account-name {} --source-account-key {}'
                         ' --pattern */file_0', dst_account_info, src_share, dst_container, src_account_info[0],
                         src_account_info[1])
        self.storage_cmd('storage blob list -c {}',
                         dst_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 4))

        # from file share to blob container while specifying destination path
        dst_container = self.create_container(dst_account_info)
        self.storage_cmd('storage blob copy start-batch --source-share {} '
                         '--destination-container {} --source-account-name {} --source-account-key {}'
                         ' --pattern */file_0 --destination-path some_dir', dst_account_info, src_share, dst_container,
                         src_account_info[0], src_account_info[1])
        self.storage_cmd('storage blob list -c {} --prefix some_dir',
                         dst_account_info, dst_container).assert_with_checks(JMESPathCheck('length(@)', 4))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='src_account')
    @StorageAccountPreparer(parameter_name='dst_account')
    @StorageTestFilesPreparer()
    def test_storage_file_batch_copy(self, src_account_info, dst_account_info, test_dir):
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        src_container = self.create_container(src_account_info)
        self.storage_cmd('storage blob upload-batch -s "{}" -d {}', src_account_info, test_dir, src_container)

        src_share = self.create_share(src_account_info)
        self.storage_cmd('storage file upload-batch -s "{}" -d {}', src_account_info, test_dir, src_share)

        # from blob container to file share with a sas in same account
        dst_share = self.create_share(src_account_info)

        self.storage_cmd('storage file copy start-batch --source-container {} '
                         '--destination-share {}', src_account_info, src_container, dst_share)
        self.assert_share_file_count(src_account_info, dst_share, 41)

        # from blob container to file share with a sas between different accounts with pattern
        dst_share = self.create_share(dst_account_info)
        sas_token = self.storage_cmd('storage container generate-sas -n {} --permissions rl '
                                     '--expiry {}', src_account_info, src_container, expiry).output
        self.storage_cmd('storage file copy start-batch --source-container {} '
                         '--destination-share {} --source-sas {} --pattern apple/* '
                         '--source-account-name {}', dst_account_info, src_container, dst_share, sas_token,
                         src_account_info[0])
        self.assert_share_file_count(dst_account_info, dst_share, 10)

        # from blob container to file share without a sas between different accounts with pattern
        dst_share = self.create_share(dst_account_info)
        self.storage_cmd('storage file copy start-batch --source-container {} '
                         '--destination-share {} --source-account-name {} --source-account-key {}'
                         ' --pattern */file_0', dst_account_info, src_container, dst_share, src_account_info[0],
                         src_account_info[1])
        self.assert_share_file_count(dst_account_info, dst_share, 4)

        # from file share to file share with a sas in same account
        dst_share = self.create_share(src_account_info)

        self.storage_cmd('storage file copy start-batch --source-share {} --destination-share {}',
                         src_account_info, src_share, dst_share)
        self.assert_share_file_count(src_account_info, dst_share, 41)

        # from file share to file share with a sas between different accounts with pattern
        dst_share = self.create_share(dst_account_info)
        sas_token = self.storage_cmd('storage share generate-sas -n {} --permissions rl --expiry {} -otsv',
                                     src_account_info, src_share, expiry).output.strip()
        self.storage_cmd('storage file copy start-batch --source-share {} '
                         '--destination-share {} --source-sas {} --pattern apple/* '
                         '--source-account-name {}', dst_account_info, src_share, dst_share, sas_token,
                         src_account_info[0])
        self.assert_share_file_count(dst_account_info, dst_share, 10)

        # from file share to file share without a sas between different accounts with pattern
        dst_share = self.create_share(dst_account_info)
        self.storage_cmd('storage file copy start-batch --source-share {} '
                         '--destination-share {} --source-account-name {} --source-account-key {}'
                         ' --pattern */file_0', dst_account_info, src_share, dst_share, src_account_info[0],
                         src_account_info[1])
        self.assert_share_file_count(dst_account_info, dst_share, 4)

    def assert_share_file_count(self, account_info, share_name, expect_file_count):
        local_folder = self.create_temp_dir()
        self.storage_cmd('storage file download-batch -s {} -d "{}"', account_info, share_name, local_folder)
        self.assertEqual(expect_file_count, sum(len(f) for r, d, f in os.walk(local_folder)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_batch_delete_scenarios(self, test_dir, storage_account_info):
        def create_and_populate_container():
            src_container = self.create_container(storage_account_info)

            # upload test files to storage account
            self.storage_cmd('storage blob upload-batch -s "{}" -d {}', storage_account_info, test_dir, src_container)
            return src_container

        # delete recursively without pattern
        src_container = create_and_populate_container()
        cmd = 'storage blob delete-batch -s {}'.format(src_container)
        self.storage_cmd(cmd, storage_account_info)
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 0))

        # delete recursively with wild card *, and use URL as source
        src_container = create_and_populate_container()
        src_url = self.storage_cmd('storage blob url -c {} -n readme -otsv', storage_account_info, src_container).output
        src_url = src_url[:src_url.rfind('/')]

        self.storage_cmd('storage blob delete-batch -s {} --pattern *', storage_account_info, src_url)
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 0))

        # delete recursively with wild card after dir
        src_container = create_and_populate_container()
        self.storage_cmd('storage blob delete-batch -s {} --pattern apple/*', storage_account_info, src_container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 31))

        # delete recursively with wild card before name
        src_container = create_and_populate_container()
        self.storage_cmd('storage blob delete-batch -s {} --pattern */file_0', storage_account_info, src_container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 37))

        # delete recursively with non-existing pattern
        src_container = create_and_populate_container()
        self.storage_cmd('storage blob delete-batch -s {} --pattern nonexists/*', storage_account_info, src_container)
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 41))

        # delete recursively with if-modified-since
        src_container = create_and_populate_container()
        self.storage_cmd('storage blob delete-batch -s {} --if-modified-since {} --dryrun',
                         storage_account_info, src_container, '2000-12-31T12:59:59Z')
        self.storage_cmd('storage blob delete-batch -s {} --if-modified-since {}',
                         storage_account_info, src_container, '2000-12-31T12:59:59Z')
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 0))

        # delete recursively with if-unmodified-since
        src_container = create_and_populate_container()
        self.storage_cmd('storage blob delete-batch -s {} --if-unmodified-since {} --dryrun',
                         storage_account_info, src_container, datetime.max.strftime('%Y-%m-%dT%H:%MZ'))
        self.storage_cmd('storage blob delete-batch -s {} --if-unmodified-since {}',
                         storage_account_info, src_container, datetime.max.strftime('%Y-%m-%dT%H:%MZ'))
        self.storage_cmd('storage blob list -c {}', storage_account_info, src_container).assert_with_checks(
            JMESPathCheck('length(@)', 0))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_file_batch_delete_scenarios(self, test_dir, storage_account_info):
        def create_and_populate_share():
            src_share = self.create_share(storage_account_info)

            # upload test files to storage account
            self.storage_cmd('storage file upload-batch -s "{}" -d {}', storage_account_info, test_dir, src_share)
            return src_share

        # delete recursively without pattern
        src_share = create_and_populate_share()
        cmd = 'storage file delete-batch -s {}'.format(src_share)
        self.storage_cmd(cmd, storage_account_info)
        self.storage_cmd('storage file list -s {} --exclude-dir', storage_account_info,
                         src_share).assert_with_checks(JMESPathCheck('length(@)', 0))
        for path in ['apple', 'butter', 'butter/charlie', 'duff/edward']:
            self.storage_cmd('storage file list -s {} -p {} --exclude-dir', storage_account_info,
                             src_share, path).assert_with_checks(JMESPathCheck('length(@)', 0))

        # delete recursively with wild card *, and use URL as source
        src_share = create_and_populate_share()
        src_url = self.storage_cmd('storage file url -s {} -p readme -otsv', storage_account_info, src_share).output
        src_url = src_url[:src_url.rfind('/')]

        self.storage_cmd('storage file delete-batch -s {} --pattern *', storage_account_info, src_url)
        self.storage_cmd('storage file list -s {} --exclude-dir', storage_account_info,
                         src_share).assert_with_checks(JMESPathCheck('length(@)', 0))
        for path in ['apple', 'butter', 'butter/charlie', 'duff/edward']:
            self.storage_cmd('storage file list -s {} -p {} --exclude-dir', storage_account_info,
                             src_share, path).assert_with_checks(JMESPathCheck('length(@)', 0))

        # delete recursively with wild card after dir
        src_share = create_and_populate_share()
        self.storage_cmd('storage file delete-batch -s {} --pattern apple/*', storage_account_info, src_share)
        self.storage_cmd('storage file list -s {} -p apple --exclude-dir', storage_account_info,
                         src_share).assert_with_checks(JMESPathCheck('length(@)', 0))

        # delete recursively with wild card before name
        src_share = create_and_populate_share()
        self.storage_cmd('storage file delete-batch -s {} --pattern */file_0', storage_account_info, src_share)
        for path in ['apple', 'butter', 'butter/charlie', 'duff/edward']:
            self.storage_cmd('storage file list -s {} -p {} --exclude-dir', storage_account_info,
                             src_share, path).assert_with_checks(JMESPathCheck('length(@)', 9))

        # delete recursively with non-existing pattern
        src_share = create_and_populate_share()
        self.storage_cmd('storage file delete-batch -s {} --pattern nonexists/*', storage_account_info, src_share)
        for path in ['apple', 'butter', 'butter/charlie', 'duff/edward']:
            self.storage_cmd('storage file list -s {} -p {} --exclude-dir', storage_account_info,
                             src_share, path).assert_with_checks(JMESPathCheck('length(@)', 10))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_batch_sas_scenarios(self, test_dir, storage_account_info):
        from datetime import datetime, timedelta

        container_name = self.create_container(storage_account_info)
        temp_dir = self.create_temp_dir()
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        sas_token = self.storage_cmd('storage container generate-sas -n {} --permissions dwrl '
                                     '--expiry {}', storage_account_info, container_name, expiry).get_output_in_json()

        storage_account = self.cmd('storage account show -n {}'.format(storage_account_info[0])).get_output_in_json()

        # create container url with sas token
        container_url = storage_account.get('primaryEndpoints').get('blob') + container_name
        container_url += '?' + sas_token

        self.kwargs.update({
            'test_dir': test_dir,
            'container_url': container_url,
            'temp_dir': temp_dir
        })

        self.cmd('storage blob upload-batch -s "{test_dir}" -d {container_url}')
        self.cmd('storage blob download-batch -s {container_url} -d "{temp_dir}"')

        self.storage_cmd('storage blob list -c {}', storage_account_info, container_name).assert_with_checks(
            JMESPathCheck('length(@)', sum(len(files) for _, __, files in os.walk(test_dir))),
            JMESPathCheck('length(@)', sum(len(files) for _, __, files in os.walk(temp_dir))))

        self.cmd('storage blob delete-batch -s {container_url}')
        self.storage_cmd('storage blob list -c {}', storage_account_info, container_name).assert_with_checks(
            JMESPathCheck('length(@)', 0))


if __name__ == '__main__':
    import unittest

    unittest.main()
