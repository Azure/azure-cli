# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, NoneCheck, StringCheck, StringContainCheck, JMESPathCheckExists)
from ..storage_test_util import StorageScenarioMixin
from azure.cli.testsdk.scenario_tests import record_only, AllowLargeResponse


class StorageFileShareFileScenarios(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(location='EastUS2', parameter_name='storage_account')
    @StorageAccountPreparer(location='EastUS2', parameter_name='storage_account_2')
    def test_storage_file_copy_scenario(self, resource_group, storage_account, storage_account_2):
        account_info = self.get_account_info(resource_group, storage_account)
        s1 = self.create_share(account_info)
        s2 = self.create_share(account_info)
        d1 = 'dir1'
        d2 = 'dir2'

        self.storage_cmd('storage directory create --share-name {} -n {}', account_info, s1, d1)
        self.storage_cmd('storage directory create --share-name {} -n {}', account_info, s2, d2)

        local_file = self.create_temp_file(512, full_random=False)
        src_file = os.path.join(d1, 'source_file.txt')
        dst_file = os.path.join(d2, 'destination_file.txt')

        self.storage_cmd('storage file upload -p "{}" --share-name {} --source "{}"', account_info,
                         src_file, s1, local_file)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src_file, s1) \
            .assert_with_checks(JMESPathCheck('exists', True))

        # test that a file can be successfully copied to root
        src_uri = self.storage_cmd('storage file url -p "{}" -s {}', account_info, src_file,
                                   s1).output
        self.assertTrue(src_uri)

        copy_id = self.storage_cmd('storage file copy start -s {} -p "{}" -u {}',
                                   account_info, s2, dst_file, src_uri) \
            .assert_with_checks(JMESPathCheck('status', 'success')) \
            .get_output_in_json()['id']

        self.storage_cmd('storage file show --share-name {} -p "{}"', account_info, s2, dst_file) \
            .assert_with_checks(JMESPathCheck('name', os.path.basename(dst_file)),
                                JMESPathCheck('properties.copy.id', copy_id),
                                JMESPathCheck('properties.copy.status', 'success'))

        # test that a file can be successfully copied to a directory
        copy_id = \
            self.storage_cmd('storage file copy start -s {} -p "{}" -u {}', account_info, s2,
                             dst_file,
                             src_uri).assert_with_checks(
                JMESPathCheck('status', 'success')).get_output_in_json()['id']

        self.storage_cmd('storage file show -s {} -p "{}"', account_info, s2, dst_file) \
            .assert_with_checks(JMESPathCheck('name', os.path.basename(dst_file)),
                                JMESPathCheck('properties.copy.id', copy_id),
                                JMESPathCheck('properties.copy.status', 'success'))

        # test that a file can be successfully copied by name components
        self.storage_cmd('storage file copy start -s {} -p "{}" --source-share {} --source-path "{}"',
                         account_info, s2, dst_file, s1, src_file) \
            .assert_with_checks(JMESPathCheck('status', 'success'))

        # test copy between two different storage accounts
        account_2_info = self.get_account_info(resource_group, storage_account_2)
        s3 = self.create_share(account_2_info)
        src_file = 'source_file.txt'
        dst_file = 'dst_file.txt'
        self.storage_cmd('storage file upload -p "{}" --share-name {} --source "{}"', account_2_info,
                         src_file, s3, local_file)
        self.storage_cmd('storage file copy start -s {} -p "{}" --source-share {} --source-path "{}" '
                         '--source-account-name {} --source-account-key {}',
                         account_info, s2, dst_file, s3, src_file, account_2_info[0], account_2_info[1])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(location='EastUS2')
    def test_storage_file_main_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        s1 = self.create_share(account_info)
        s2 = self.create_random_name('share', 24)
        self.storage_cmd('storage share create -n {} --metadata foo=bar cat=hat', account_info, s2)
        self.storage_cmd('storage share exists -n {}', account_info, s1) \
            .assert_with_checks(JMESPathCheck('exists', True))
        self.storage_cmd('storage share metadata show --name {}', account_info, s2) \
            .assert_with_checks(JMESPathCheck('cat', 'hat'), JMESPathCheck('foo', 'bar'))

        share_list = self.storage_cmd('storage share list --query "[].name"',
                                      account_info).get_output_in_json()
        self.assertIn(s1, share_list)
        self.assertIn(s2, share_list)

        # verify metadata can be set, queried, and cleared
        self.storage_cmd('storage share metadata update --name {} --metadata a=b c=d', account_info, s1)
        self.storage_cmd('storage share metadata show -n {}', account_info, s1) \
            .assert_with_checks(JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'))
        self.storage_cmd('storage share metadata update -n {}', account_info, s1)
        self.storage_cmd('storage share metadata show -n {}', account_info, s1) \
            .assert_with_checks(NoneCheck())

        self.storage_cmd('storage share update --name {} --quota 3', account_info, s1)
        self.storage_cmd('storage share show --name {}', account_info, s1) \
            .assert_with_checks(JMESPathCheck('properties.quota', 3))
        self.storage_cmd('storage share url --name {}', account_info, s1) \
            .assert_with_checks(StringContainCheck(s1), StringContainCheck('http'))
        unc = self.storage_cmd('storage share url --name {} --unc', account_info, s1).output
        self.assertTrue('http' not in unc and s1 in unc)

        sas = self.storage_cmd('storage share generate-sas -n {} --permissions r --expiry '
                               '2046-08-23T10:30Z', account_info, s1).output
        self.assertIn('sig=', sas)

        self.validate_file_scenario(account_info, s1)
        self.validate_directory_scenario(account_info, s1)

        self.storage_cmd('storage share delete -n {}', account_info, s1) \
            .assert_with_checks(JMESPathCheck('deleted', True))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(location='EastUS2', allow_blob_public_access=True)
    def test_storage_file_main_oauth_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        s1 = self.create_share(account_info)

        self.validate_file_oauth_scenario(storage_account, s1)
        self.validate_directory_oauth_scenario(storage_account, s1)

        self.storage_cmd('storage share delete -n {}', account_info, s1) \
            .assert_with_checks(JMESPathCheck('deleted', True))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_file_upload_content_md5_scenarios(self, resource_group, storage_account):
        import hashlib
        import base64

        account_info = self.get_account_info(resource_group, storage_account)
        share = self.create_share(account_info)
        local_file = self.create_temp_file(128)

        def md5(fname):
            hash_md5 = hashlib.md5()
            with open(fname, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.digest()

        md5_digest = md5(local_file)
        md5_base64_encode = base64.b64encode(md5_digest).decode("utf-8")
        file_name = self.create_random_name(prefix='file', length=24) + '.txt'
        self.storage_cmd('storage file upload -s {} --source "{}" --path {} --content-md5 {}', account_info,
                         share, local_file, file_name, md5_base64_encode)
        self.storage_cmd('storage file show -s {} --path {}', account_info, share, file_name). \
            assert_with_checks(JMESPathCheck("properties.contentSettings.contentMd5", md5_base64_encode))

        self.storage_cmd('storage file update -s {} --path {} --content-md5 0000', account_info, share, file_name)
        self.storage_cmd('storage file show -s {} --path {}', account_info, share, file_name). \
            assert_with_checks(JMESPathCheck("properties.contentSettings.contentMd5", '0000'))

    @record_only()
    # manual test, only run the recording
    # To reproduce the prerequisite steps:
    # 1. Create a file share under a storage account/ resource group as specified below
    # 2. Upload Book1.csv to the root dir of the file share, add a dir called dir1 and upload another file testjson.json
    # 3. Create a Python file to open both files and sleep so the file handles are held
    # 4. Create two VMs and ssh to them
    # 5. Mount the file share using the script in the connect tab and run the Python file
    def test_storage_file_share_handle_scenario(self):
        resource_group = 'azure-cli-test-file-handle-rg'
        storage_account = 'testfilehandlesa'
        account_info = self.get_account_info(resource_group, storage_account)
        file_share = 'file-share'
        self.storage_cmd('storage share list-handle --name {} --recursive', account_info, file_share).\
            assert_with_checks(JMESPathCheck("length(items[?path=='Book1.csv'])",2),
                               JMESPathCheck("length(items[?path=='dir1/testjson.json'])",2),
                               JMESPathCheck("length(items[?path=='dir1/dir2/1.png'])",2))

        self.storage_cmd("storage share list-handle --name {} --recursive --path dir1",  account_info, file_share).\
            assert_with_checks(JMESPathCheck("length(items[?path=='dir1/testjson.json'])", 2),
                               JMESPathCheck("length(items[?path=='dir1/dir2/1.png'])",2))

        self.storage_cmd("storage share list-handle --name {} --recursive --path ./dir1/dir2/1.png", account_info, file_share). \
            assert_with_checks(JMESPathCheck("length(items[?path=='dir1/dir2/1.png'])", 2))

        result = self.storage_cmd("storage share list-handle --name {} --path 'Book1.csv'", account_info, file_share).\
            get_output_in_json()['items']
        self.assertEqual(len(result), 2)
        handle_id = result[0]["handleId"]

        self.storage_cmd("storage share close-handle --name {} --path 'Book1.csv' --handle-id {}", account_info,
                         file_share, handle_id)
        self.storage_cmd("storage share list-handle --name {} --path 'Book1.csv'", account_info, file_share). \
            assert_with_checks(JMESPathCheck("length(items[?path=='Book1.csv'])", 1))
        self.storage_cmd("storage share close-handle --name {} --path 'dir1' --recursive --close-all", account_info,
                         file_share)
        self.storage_cmd("storage share list-handle --name {} --path 'dir1/testjson.json'", account_info, file_share). \
            assert_with_checks(JMESPathCheck("length(items[?path=='dir1/testjson.json'])", 0))
        self.storage_cmd("storage share close-handle --name {} --recursive --handle-id '*'", account_info,
                         file_share)
        self.storage_cmd("storage share list-handle --name {} --recursive", account_info, file_share). \
            assert_with_checks(JMESPathCheck("length(items)", 0))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(location='EastUS2')
    def test_storage_file_copy_snapshot_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        s1 = self.create_share(account_info)
        s2 = self.create_share(account_info)
        d1 = 'dir1'
        d2 = 'dir2'

        self.storage_cmd('storage directory create --share-name {} -n {}', account_info, s1, d1)
        self.storage_cmd('storage directory create --share-name {} -n {}', account_info, s2, d2)

        local_file = self.create_temp_file(512, full_random=False)
        src_file = os.path.join(d1, 'source_file.txt')
        dst_file = os.path.join(d2, 'destination_file.txt')

        self.storage_cmd('storage file upload -p "{}" --share-name {} --source "{}"', account_info,
                         src_file, s1, local_file)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src_file, s1) \
            .assert_with_checks(JMESPathCheck('exists', True))

        snapshot = self.storage_cmd('storage share snapshot -n {}', account_info,
                                    s1).get_output_in_json()['snapshot']

        # remove the source file from share
        self.storage_cmd('storage file delete --share-name {} -p "{}"',
                         account_info, s1, src_file)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src_file, s1) \
            .assert_with_checks(JMESPathCheck('exists', False))

        copy_id = self.storage_cmd('storage file copy start -s {} -p "{}" --source-share {} --source-path "{}" '
                                   '--file-snapshot {}', account_info, s2, dst_file, s1, src_file, snapshot) \
            .assert_with_checks(JMESPathCheck('status', 'success')) \
            .get_output_in_json()['id']

        self.storage_cmd('storage file show --share-name {} -p "{}"', account_info, s2, dst_file) \
            .assert_with_checks(JMESPathCheck('name', os.path.basename(dst_file)),
                                JMESPathCheck('properties.copy.id', copy_id),
                                JMESPathCheck('properties.copy.status', 'success'))
        # without --delete-snapshots, should fail because there is an existing snapshot
        with self.assertRaises(Exception):
            self.storage_cmd('storage share delete --name {}', account_info, s1)

        self.cmd('storage share delete --name {} --account-name {} '
                 '--delete-snapshots include-leased'.format(s1, storage_account),
                 checks=JMESPathCheck('deleted', True))

    def validate_directory_scenario(self, account_info, share):
        directory = self.create_random_name('dir', 16)
        self.storage_cmd('storage directory create --share-name {} --name {} --fail-on-exist',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('created', True))
        self.storage_cmd('storage directory list -s {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))
        self.storage_cmd('storage directory exists --share-name {} -n {}',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('exists', True))
        self.storage_cmd('storage directory metadata update -s {} -n {} --metadata a=b c=d',
                         account_info, share, directory)
        self.storage_cmd('storage directory metadata show --share-name {} -n {}',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'))
        self.storage_cmd('storage directory show --share-name {} -n {}',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('metadata', {'a': 'b', 'c': 'd'}),
                                JMESPathCheck('name', directory))
        self.storage_cmd('storage directory metadata update --share-name {} --name {}',
                         account_info, share, directory)
        self.storage_cmd('storage directory metadata show --share-name {} --name {}',
                         account_info, share, directory).assert_with_checks(NoneCheck())

        self.validate_subdir_scenario(account_info, share, directory)

        self.storage_cmd('storage directory delete --share-name {} --name {} --fail-not-exist',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('deleted', True))
        self.storage_cmd('storage directory exists --share-name {} --name {}',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('exists', False))

        # verify a directory can be created with metadata and then delete
        directory = self.create_random_name('dir', 16)
        self.storage_cmd('storage directory create --share-name {} --name {} --fail-on-exist '
                         '--metadata foo=bar cat=hat', account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('created', True))
        self.storage_cmd('storage directory metadata show --share-name {} -n {}',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('cat', 'hat'), JMESPathCheck('foo', 'bar'))
        self.storage_cmd('storage directory delete --share-name {} --name {} --fail-not-exist',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('deleted', True))

    def validate_file_scenario(self, account_info, share):
        source_file = self.create_temp_file(128, full_random=False)
        dest_file = self.create_temp_file(1)
        filename = "sample_file.bin"

        self.storage_cmd('storage file upload --share-name {} --source "{}" -p {}', account_info,
                         share, source_file, filename)
        self.storage_cmd('storage file exists -s {} -p {}', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', True))

        if os.path.isfile(dest_file):
            os.remove(dest_file)

        self.storage_cmd('storage file download --share-name {} -p "{}" --dest "{}"', account_info,
                         share, filename, dest_file)

        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 128 * 1024)

        self.storage_cmd('storage file download --share-name {} -p "{}" --dest "{}" --start-range 0 --end-range 511', account_info,
                         share, filename, dest_file)

        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 512)

        # test resize command
        self.storage_cmd('storage file resize --share-name {} -p "{}" --size 1234', account_info,
                         share, filename)
        self.storage_cmd('storage file show -s {} -p "{}"', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('properties.contentLength', 1234))

        # test ability to set and reset metadata
        self.storage_cmd('storage file metadata update --share-name {} -p "{}" --metadata a=b c=d',
                         account_info, share, filename)
        self.storage_cmd('storage file metadata show -s {} -p "{}"', account_info, share,
                         filename) \
            .assert_with_checks(JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'))
        self.storage_cmd('storage file metadata update --share-name {} -p "{}"', account_info,
                         share, filename)
        self.storage_cmd('storage file metadata show -s {} -p "{}"', account_info, share,
                         filename) \
            .assert_with_checks(NoneCheck())

        file_url = 'https://{}.file.core.windows.net/{}/{}'.format(account_info[0], share, filename)
        self.storage_cmd('storage file url -s {} -p "{}"', account_info, share, filename) \
            .assert_with_checks(StringCheck(file_url))

        # try uploading with file url
        new_source_file = self.create_temp_file(64, full_random=False)
        self.storage_cmd('storage file upload --source "{}" --file-url {}', account_info, new_source_file, file_url)
        # download to validate the new upload with file-url uploaded file with new size
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        self.storage_cmd('storage file download --share-name {} -p "{}" --dest "{}"', account_info,
                         share, filename, dest_file)
        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 64 * 1024)

        self.assertIn(filename,
                      self.storage_cmd('storage file list -s {} --query "[].name"',
                                       account_info, share).get_output_in_json())

        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        self.storage_cmd('storage file generate-sas -s {} -p {} --permissions r --expiry {}', account_info, share,
                         filename, expiry).assert_with_checks(StringContainCheck('sig='))

        self.storage_cmd('storage file update -s {} -p {} --content-type "test/type"', account_info,
                         share, filename)
        self.storage_cmd('storage file show -s {} -p {}', account_info, share,
                         filename) \
            .assert_with_checks(JMESPathCheck('properties.contentSettings.contentType',
                                              'test/type'))

        self.storage_cmd('storage file delete --share-name {} -p "{}"',
                         account_info, share, filename)
        self.storage_cmd('storage file exists --share-name {} -p "{}"',
                         account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', False))

    def validate_subdir_scenario(self, account_info, share, directory):
        source_file = self.create_temp_file(64, full_random=False)
        dest_file = self.create_temp_file(1)
        filename = 'testfile.txt'

        self.storage_cmd('storage file upload --share-name {} -p "{}/{}" --source "{}"',
                         account_info, share, directory, filename, source_file)
        self.storage_cmd('storage file exists --share-name {} -p "{}/{}"',
                         account_info, share, directory, filename) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage file download --share-name {} -p "{}/{}" --dest "{}"',
                         account_info, share, directory, filename, dest_file)

        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 64 * 1024)

        self.assertIn(filename, self.storage_cmd('storage file list -s {} -p {} --query "[].name"',
                                                 account_info, share, directory)
                      .get_output_in_json())

        self.storage_cmd('storage share stats --name {}', account_info, share) \
            .assert_with_checks(StringCheck('1'))
        self.storage_cmd('storage file delete --share-name {} -p "{}/{}"',
                         account_info, share, directory, filename)
        self.storage_cmd('storage file exists -s {} -p "{}"', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', False))

    def validate_directory_oauth_scenario(self, account, share):
        directory = self.create_random_name('dir', 16)
        self.file_oauth_cmd('storage directory create --account-name {} --share-name {} --name {} --fail-on-exist',
                            account, share, directory) \
            .assert_with_checks(JMESPathCheck('created', True))
        self.file_oauth_cmd('storage directory list --account-name {} -s {}', account, share) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))
        self.file_oauth_cmd('storage directory exists --account-name {} --share-name {} -n {}',
                            account, share, directory) \
            .assert_with_checks(JMESPathCheck('exists', True))
        self.file_oauth_cmd('storage directory metadata update --account-name {} -s {} -n {} --metadata a=b c=d',
                            account, share, directory)
        self.file_oauth_cmd('storage directory metadata show --account-name {} --share-name {} -n {}',
                            account, share, directory) \
            .assert_with_checks(JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'))
        self.file_oauth_cmd('storage directory show --account-name {} --share-name {} -n {}',
                            account, share, directory) \
            .assert_with_checks(JMESPathCheck('metadata', {'a': 'b', 'c': 'd'}),
                                JMESPathCheck('name', directory))

        self.file_oauth_cmd('storage directory delete --account-name {} --share-name {} --name {} --fail-not-exist',
                            account, share, directory) \
            .assert_with_checks(JMESPathCheck('deleted', True))
        self.file_oauth_cmd('storage directory exists --account-name {} --share-name {} --name {}',
                            account, share, directory) \
            .assert_with_checks(JMESPathCheck('exists', False))

    def validate_file_oauth_scenario(self, account, share):
        source_file = self.create_temp_file(128, full_random=False)
        dest_file = self.create_temp_file(1)
        filename = "sample_file.bin"

        self.file_oauth_cmd('storage file upload --account-name {} --share-name {} --source "{}" -p {}',
                            account, share, source_file, filename)
        self.file_oauth_cmd('storage file exists --account-name {} -s {} -p {}', account, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', True))

        if os.path.isfile(dest_file):
            os.remove(dest_file)

        self.file_oauth_cmd('storage file download --account-name {} --share-name {} -p "{}" --dest "{}"',
                            account, share, filename, dest_file)

        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 128 * 1024)

        self.file_oauth_cmd(
            'storage file download --account-name {} --share-name {} -p "{}" --dest "{}" --start-range 0 --end-range 511',
            account, share, filename, dest_file)

        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 512)

        # test resize command
        self.file_oauth_cmd('storage file resize --account-name {} --share-name {} -p "{}" --size 1234', account, share, filename)
        self.file_oauth_cmd('storage file show --account-name {} -s {} -p "{}"', account, share, filename) \
            .assert_with_checks(JMESPathCheck('properties.contentLength', 1234))

        # test ability to set and reset metadata
        self.file_oauth_cmd('storage file metadata update --account-name {} --share-name {} -p "{}" --metadata a=b c=d',
                            account, share, filename)
        self.file_oauth_cmd('storage file metadata show --account-name {} -s {} -p "{}"', account, share, filename) \
            .assert_with_checks(JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'))
        self.file_oauth_cmd('storage file metadata update --account-name {} --share-name {} -p "{}"', account, share, filename)
        self.file_oauth_cmd('storage file metadata show --account-name {} -s {} -p "{}"', account, share, filename) \
            .assert_with_checks(NoneCheck())

        file_url = 'https://{}.file.core.windows.net/{}/{}'.format(account, share, filename)
        self.file_oauth_cmd('storage file url --account-name {} -s {} -p "{}"', account, share, filename) \
            .assert_with_checks(StringCheck(file_url))

        self.assertIn(filename,
                      self.file_oauth_cmd('storage file list --account-name {} -s {} --query "[].name"',
                                          account, share).get_output_in_json())

        self.file_oauth_cmd('storage file update --account-name {} -s {} -p {} --content-type "test/type"',
                            account, share, filename)
        self.file_oauth_cmd('storage file show --account-name {} -s {} -p {}', account, share, filename) \
            .assert_with_checks(JMESPathCheck('properties.contentSettings.contentType',
                                              'test/type'))

        self.file_oauth_cmd('storage file delete --account-name {} --share-name {} -p "{}"', account, share, filename)
        self.file_oauth_cmd('storage file exists --account-name {} --share-name {} -p "{}"', account, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', False))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(location='EastUS2')
    @AllowLargeResponse()
    def test_storage_file_trailing_dot_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        s1 = self.create_share(account_info)

        self._validate_file_trailing_dot_scenario(account_info, s1)
        self._validate_directory_trailing_dot_scenario(account_info, s1)

        self.storage_cmd('storage share delete -n {}', account_info, s1) \
            .assert_with_checks(JMESPathCheck('deleted', True))

    def _validate_directory_trailing_dot_scenario(self, account_info, share):
        directory = self.create_random_name('dir', 16)
        directory = directory + '..'
        # by default allow trailing dot
        self.storage_cmd('storage directory create --share-name {} --name {} --fail-on-exist',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('created', True))
        connection_string = self.cmd('storage account show-connection-string -n {}'.format(account_info[0])
                                     ).get_output_in_json()['connectionString']
        self.storage_cmd('storage directory create --share-name {} --name {} --connection-string {}',
                         account_info, share, directory, connection_string)
        self.storage_cmd('storage directory list -s {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))
        self.storage_cmd('storage directory show --share-name {} -n {}',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('name', directory))

        # requests with --disallow-trailing-dot would point to the trimmed url
        self.storage_cmd('storage directory create --share-name {} --name {} --fail-on-exist --disallow-trailing-dot',
                         account_info, share, directory) \
            .assert_with_checks(JMESPathCheck('created', True))
        self.storage_cmd('storage directory create --share-name {} --name {}  --disallow-trailing-dot '
                         '--connection-string {}',
                         account_info, share, directory, connection_string)
        self.storage_cmd('storage directory list -s {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('length(@)', 2))
        self.storage_cmd('storage directory show --share-name {} -n {} --disallow-trailing-dot',
                         account_info, share, directory[:-2]) \
            .assert_with_checks(JMESPathCheck('name', directory[:-2]))

    def _validate_file_trailing_dot_scenario(self, account_info, share):
        source_file = self.create_temp_file(128, full_random=False)
        dest_file = self.create_temp_file(1)
        filename = "sample_file.bin..."
        # default is not trimming trialing dot
        self.storage_cmd('storage file upload --share-name {} --source "{}" -p {}', account_info,
                         share, source_file, filename)
        self.storage_cmd('storage file exists -s {} -p {}', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', True))
        connection_string = self.cmd('storage account show-connection-string -n {}'.format(account_info[0])
                                     ).get_output_in_json()['connectionString']
        self.storage_cmd('storage file upload --share-name {} --source "{}" -p {} --connection-string {}',
                         account_info, share, source_file, filename, connection_string)

        if os.path.isfile(dest_file):
            os.remove(dest_file)

        self.storage_cmd('storage file download --share-name {} -p "{}" --dest "{}"', account_info,
                         share, filename, dest_file)

        self.assertTrue(os.path.isfile(dest_file))
        self.assertEqual(os.stat(dest_file).st_size, 128 * 1024)

        # with --disallow-trailing-dot, should fail because file does not exist
        with self.assertRaises(Exception):
            self.storage_cmd('storage file download --share-name {} -p "{}" --dest "{}" --disallow-trailing-dot',
                             account_info, share, filename, dest_file)

        # copy from file
        copy_dst_name = "sample_file_dst.bin..."
        # copy without trimming
        self.storage_cmd('storage file copy start --source-account-name {} --source-path {} --source-share {} '
                         '--destination-path {} --destination-share {}', account_info, account_info[0], filename,
                         share, copy_dst_name, share)
        self.storage_cmd('storage file exists -s {} -p {}', account_info, share, copy_dst_name) \
            .assert_with_checks(JMESPathCheck('exists', True))

        # copy with trimming dst name
        self.storage_cmd('storage file copy start --source-account-name {} --source-path {} --source-share {} '
                         '--destination-path {} --destination-share {} --disallow-trailing-dot',
                         account_info, account_info[0], filename,
                         share, copy_dst_name, share)
        self.storage_cmd('storage file exists -s {} -p {} --disallow-trailing-dot', account_info, share, copy_dst_name) \
            .assert_with_checks(JMESPathCheck('exists', True))

        # copy with trimmed src name should fail because src file does not exist
        with self.assertRaises(Exception):
            self.storage_cmd('storage file copy start --source-account-name {} --source-path {} --source-share {} '
                             '--destination-path {} --destination-share {} --disallow-source-trailing-dot',
                             account_info,
                             account_info[0], filename, share, copy_dst_name, share)

        # try uploading file with trailing dot with --disallow-trailing-dot
        self.storage_cmd('storage file delete -s {} -p {}', account_info, share, filename)
        self.storage_cmd('storage file exists -s {} -p {}', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', False))
        self.storage_cmd('storage file upload --share-name {} --source "{}" -p {} --disallow-trailing-dot',
                         account_info,
                         share, source_file, filename)
        self.storage_cmd('storage file upload --share-name {} --source "{}" -p {} --disallow-trailing-dot '
                         '--connection-string {}', account_info, share, source_file, filename, connection_string)
        self.storage_cmd('storage file exists -s {} -p {} --disallow-trailing-dot', account_info, share, filename) \
            .assert_with_checks(JMESPathCheck('exists', True))