# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck, NoneCheck,
                               api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin
from knack.util import CLIError


@api_version_constraint(ResourceType.DATA_STORAGE_FILEDATALAKE, min_api='2018-11-09')
class StorageADLSGen2Tests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_access_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = self.create_random_name(prefix="dir", length=12)
        file = self.create_random_name(prefix="file", length=12)
        file_path = '/'.join([directory, file])

        # Create file path
        self.storage_cmd('storage fs file create -p {} -f {}', account_info, file_path, filesystem)
        # Check the permission of file
        self.storage_cmd('storage fs file show -p {} -f {}', account_info, file_path, filesystem) \
            .assert_with_checks(JMESPathCheck('permissions', 'rw-r-----'))
        # Check the permission of directory
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, directory, filesystem) \
            .assert_with_checks(JMESPathCheck('metadata.hdi_isfolder', 'true')) \
            .assert_with_checks(JMESPathCheck('permissions', 'rwxr-x---'))

        # Set acl for root path
        acl = "user::rwx,group::r--,other::---"
        self.storage_cmd('storage fs access set -f {} -p / --acl {}', account_info, filesystem, acl)

        self.storage_cmd('storage fs access show -f {} -p / ', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('acl', acl)) \
            .assert_with_checks(JMESPathCheck('group', "$superuser")) \
            .assert_with_checks(JMESPathCheck('owner', "$superuser")) \
            .assert_with_checks(JMESPathCheck('permissions', "rwxr-----"))

        # Set permissions for a file
        permissions = "rwxrwxrwx"
        self.storage_cmd('storage fs access set -f {} -p {} --permissions {}', account_info, filesystem, file_path,
                         permissions)
        self.storage_cmd('storage fs access show -f {} -p {} ', account_info, filesystem, file_path) \
            .assert_with_checks(JMESPathCheck('permissions', permissions))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_access_recursive_scenarios(self, resource_group, storage_account):
        import os
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        dir0 = self.create_random_name(prefix="dir0", length=12)
        subdir0 = os.path.join(dir0, 'dir0')
        subdir1 = os.path.join(dir0, 'dir1')
        subdir2 = os.path.join(dir0, 'dir2')

        file1 = os.path.join(subdir1, self.create_random_name(prefix="file1", length=12))
        file2 = os.path.join(subdir1, self.create_random_name(prefix="file2", length=12))
        file3 = os.path.join(subdir1, self.create_random_name(prefix="file3", length=12))
        file4 = os.path.join(subdir2, self.create_random_name(prefix="file4", length=12))
        file5 = os.path.join(subdir2, self.create_random_name(prefix="file5", length=12))
        file6 = os.path.join(subdir2, self.create_random_name(prefix="file6", length=12))

        local_file = self.create_temp_file(16)

        # Prepare files
        self.oauth_cmd('storage fs directory create -n {} -f {} --account-name {} ', dir0, filesystem, storage_account)
        self.oauth_cmd('storage fs directory create -n {} -f {} --account-name {} ', subdir0, filesystem, storage_account)
        self.oauth_cmd('storage fs directory create -n {} -f {} --account-name {} ', subdir1, filesystem, storage_account)
        self.oauth_cmd('storage fs directory create -n {} -f {} --account-name {} ', subdir2, filesystem, storage_account)

        self.storage_cmd('storage fs file upload -p {} -f {} -s {} ', account_info, file1, filesystem, local_file)
        self.oauth_cmd('storage fs file upload -p {} -f {} -s {} --account-name {} ', file2, filesystem, local_file, storage_account)
        self.oauth_cmd('storage fs file upload -p {} -f {} -s {} --account-name {} ', file3, filesystem, local_file,
                       storage_account)
        self.oauth_cmd('storage fs file upload -p {} -f {} -s {} --account-name {} ', file4, filesystem, local_file,
                       storage_account)
        self.storage_cmd('storage fs file upload -p {} -f {} -s {} ', account_info, file5, filesystem, local_file,
                          storage_account)
        self.oauth_cmd('storage fs file upload -p {} -f {} -s {} --account-name {} ', file6, filesystem, local_file,
                       storage_account)

        items = self.oauth_cmd('storage fs file list -f {} --account-name {} --query [].name', filesystem, storage_account).get_outpu_in_json()
        for item in items:
            self.storage_cmd('storage fs access set -p {} -f {} --permissions rwxr-x--- ', account_info, item, filesystem) \
                .assert_with_checks(JMESPathCheck('permissions', 'rwxr-x---'))

        # Set acl for root path

        acl1 = "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923:rwx"
        acl2 = "user::r-x"

        # ----------- directory ---------
        # set recursive
        self.storage_cmd('storage fs access set-recursive -f {} -p {} --acl {}', account_info, filesystem, dir0, acl1)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))
        # update recursive
        self.storage_cmd('storage fs access update-recursive -f {} -p {} --acl {}', account_info, filesystem, subdir2, acl2)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))

        # remove recursive
        removal_acl = "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923"

        self.storage_cmd('storage fs access remove-recursive -f {} -p {} --acl {}', account_info, filesystem, dir0, removal_acl)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))

        # ----------- file ---------
        # set recursive
        self.storage_cmd('storage fs access set-recursive -f {} -p {} --acl {}', account_info, filesystem, file5, acl1)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))
        # update recursive
        self.storage_cmd('storage fs access update-recursive -f {} -p {} --acl {}', account_info, filesystem, file5, acl2)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))

        # remove recursive
        removal_acl = "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923"

        self.storage_cmd('storage fs access remove-recursive -f {} -p {} --acl {}', account_info, filesystem, file5, removal_acl)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))

        # Test continue on failure
        result = self.oauth_cmd('storage fs access set-recursive -f {} -p {} --acl {} --batch-size 2 --max-batches 2 '
                                '--continue-on-failure --account-name {}', filesystem, dir0, acl1, storage_account)\
            .get_output_in_json()

        self.assertIsNotNone(result['continuation'])
        self.assertEqual(result['counters']['directoriesSuccessful'], 4)
        self.assertEqual(result['counters']['failureCount'], 2)
        self.assertEqual(result['counters']['filesSuccessful'], 4)

        # fix failed entries and recover from failure
        self.oauth_cmd('storage fs access set-recursive -f {} -p {} --acl {} --batch-size 2 --max-batches 2 '
                       '--continue-on-failure --account-name {} --continuation {}', filesystem, dir0, acl1,
                       storage_account, result['continuation'])



    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_filesystem_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_str = self.cmd('storage account show-connection-string -n {} -g {} -otsv'
                                  .format(storage_account, resource_group)).output

        # Test with account key
        filesystem1 = self.create_random_name(prefix='filesystem', length=24)
        self.storage_cmd('storage fs create -n {} --public-access file', account_info, filesystem1)
        self.storage_cmd('storage fs exists -n {}', account_info, filesystem1) \
            .assert_with_checks(JMESPathCheck('exists', True))
        self.storage_cmd('storage fs show -n {}', account_info, filesystem1)\
            .assert_with_checks(JMESPathCheck('name', filesystem1)) \
            .assert_with_checks(JMESPathCheck('publicAccess', 'file'))

        # Test with connection string
        filesystem2 = self.create_random_name(prefix='filesystem', length=24)
        self.cmd('storage fs create -n {} --public-access filesystem --connection-string {}'.format(
            filesystem2, connection_str))

        self.cmd('storage fs show -n {} --connection-string {}'.format(filesystem2, connection_str)) \
            .assert_with_checks(JMESPathCheck('name', filesystem2)) \
            .assert_with_checks(JMESPathCheck('publicAccess', 'filesystem'))

        filesystem3 = self.create_random_name(prefix='filesystem', length=24)
        self.storage_cmd('storage fs create -n {} --public-access off', account_info, filesystem3)

        self.storage_cmd('storage fs show -n {}', account_info, filesystem3) \
            .assert_with_checks(JMESPathCheck('name', filesystem3)) \
            .assert_with_checks(JMESPathCheck('publicAccess', None))

        self.storage_cmd('storage fs list', account_info) \
            .assert_with_checks(JMESPathCheck('length(@)', 3))

        self.storage_cmd('storage fs delete -n {} -y', account_info, filesystem1)
        self.storage_cmd('storage fs delete -n {} -y', account_info, filesystem2)
        self.storage_cmd('storage fs delete -n {} -y', account_info, filesystem3)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_directory_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = self.create_random_name(prefix="dir", length=12)
        subdir = self.create_random_name(prefix="subdir", length=12)

        subdir_path = '/'.join([directory, subdir])

        # Create Directory
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, directory, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', False))
        self.storage_cmd('storage fs directory create -n {} -f {}', account_info, directory, filesystem)
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, directory, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', True))
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, directory, filesystem)\
            .assert_with_checks(JMESPathCheck('name', directory)) \
            .assert_with_checks(JMESPathCheck('deleted', False)) \
            .assert_with_checks(JMESPathCheck('metadata.hdi_isfolder', 'true')) \
            .assert_with_checks(JMESPathCheck('permissions', 'rwxr-x---'))

        self.storage_cmd('storage fs directory create -n {} -f {} --permissions rwxrwxrwx --umask 0007', account_info,
                         subdir_path, filesystem)
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, subdir_path, filesystem) \
            .assert_with_checks(JMESPathCheck('name', subdir_path)) \
            .assert_with_checks(JMESPathCheck('deleted', False)) \
            .assert_with_checks(JMESPathCheck('metadata.hdi_isfolder', 'true')) \
            .assert_with_checks(JMESPathCheck('permissions', 'rwxrwx---'))

        # List Directories
        self.storage_cmd('storage fs directory list -f {}', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('length(@)', 2))
        self.storage_cmd('storage fs directory list -f {} --path {}', account_info, filesystem, directory) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # Move Directory
        new_dir = "new_dir"
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, new_dir, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', False))
        self.storage_cmd('storage fs directory move -n {} -f {} --new-directory {}', account_info, subdir_path,
                         filesystem, '/'.join([filesystem, new_dir]))
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, new_dir, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', True))
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, subdir_path, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', False))
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, new_dir, filesystem) \
            .assert_with_checks(JMESPathCheck('name', new_dir)) \
            .assert_with_checks(JMESPathCheck('deleted', False)) \
            .assert_with_checks(JMESPathCheck('metadata.hdi_isfolder', 'true')) \
            .assert_with_checks(JMESPathCheck('permissions', 'rwxrwx---'))

        self.storage_cmd('storage fs directory list -f {}', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('length(@)', 2))
        self.storage_cmd('storage fs directory list -f {} --path {}', account_info, filesystem, directory) \
            .assert_with_checks(JMESPathCheck('length(@)', 0))

        new_filesystem = self.create_file_system(account_info)
        self.storage_cmd('storage fs directory move -n {} -f {} --new-directory {}',
                         account_info, directory, filesystem, '/'.join([new_filesystem, new_dir]))
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, new_dir, new_filesystem) \
            .assert_with_checks(JMESPathCheck('name', new_dir)) \
            .assert_with_checks(JMESPathCheck('deleted', False)) \
            .assert_with_checks(JMESPathCheck('metadata.hdi_isfolder', 'true')) \
            .assert_with_checks(JMESPathCheck('permissions', 'rwxr-x---'))

        # Delete Directory
        self.storage_cmd('storage fs directory delete -n {} -f {} -y', account_info, new_dir, filesystem)
        self.storage_cmd('storage fs directory delete -n {} -f {} -y', account_info, new_dir, new_filesystem)
        self.storage_cmd('storage fs directory list -f {}', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('length(@)', 0))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_file_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = self.create_random_name(prefix="dir", length=12)
        file = self.create_random_name(prefix="file", length=12)

        # Create File
        self.storage_cmd('storage fs file exists -p {} -f {}', account_info, file, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', False))
        self.storage_cmd('storage fs file create -p {} -f {} --content-type "application/json"',
                         account_info, file, filesystem)
        self.storage_cmd('storage fs file exists -p {} -f {}', account_info, file, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage fs file show -p {} -f {}', account_info, file, filesystem) \
            .assert_with_checks(JMESPathCheck('name', file)) \
            .assert_with_checks(JMESPathCheck('deleted', False)) \
            .assert_with_checks(JMESPathCheck('size', 0)) \
            .assert_with_checks(JMESPathCheck('permissions', 'rw-r-----')) \
            .assert_with_checks(JMESPathCheck('content_settings.contentType', 'application/json'))

        # Append File
        content = "testappend"
        content_size = len(content)
        self.storage_cmd('storage fs file append -p {} -f {} --content {}', account_info, file, filesystem, content)
        self.storage_cmd('storage fs file show -p {} -f {}', account_info, file, filesystem) \
            .assert_with_checks(JMESPathCheck('name', file)) \
            .assert_with_checks(JMESPathCheck('deleted', False)) \
            .assert_with_checks(JMESPathCheck('size', content_size)) \
            .assert_with_checks(JMESPathCheck('permissions', 'rw-r-----'))

        # Upload File to a new path
        file_path = "/".join([directory, file])
        local_file = self.create_temp_file(1024)
        self.storage_cmd('storage fs file upload -p {} -f {} -s "{}"', account_info, file_path, filesystem, local_file)

        # Upload File to an existing non-empty file with default overwrite=false
        new_local_file = self.create_temp_file(512)
        with self.assertRaisesRegexp(CLIError, 'You cannot upload to an existing non-empty file with overwrite=false.'):
            self.storage_cmd('storage fs file upload -p {} -f {} -s "{}"', account_info, file_path, filesystem,
                             new_local_file)

        # Upload File to an existing non-empty file with --overwrite
        self.storage_cmd('storage fs file upload -p {} -f {} -s "{}" --overwrite', account_info, file_path, filesystem,
                         new_local_file)
        # Upload File to an existing non-empty file with --overwrite true
        self.storage_cmd('storage fs file upload -p {} -f {} -s "{}" --overwrite true', account_info, file_path,
                         filesystem, new_local_file)

        # List files including directory
        self.storage_cmd('storage fs file list -f {}', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('length(@)', 3))

        # List files excluding directory
        self.storage_cmd('storage fs file list -f {} --exclude-dir', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('length(@)', 2))

        # List files under specific path
        self.storage_cmd('storage fs file list --path {} -f {} --exclude-dir', account_info, directory, filesystem) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # Download file
        local_dir = self.create_temp_dir()
        self.storage_cmd('storage fs file download -p {} -f {} -d "{}"', account_info, file_path, filesystem, local_dir)
        import os
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_dir)))

        with self.assertRaisesRegexp(CLIError, "The specified path already exists. Please change to a valid path."):
            self.storage_cmd('storage fs file download -p {} -f {} -d "{}" --overwrite false', account_info, file_path,
                             filesystem, local_dir)

        # Move file
        new_filesystem = self.create_file_system(account_info)
        self.storage_cmd('storage fs file move -p {} -f {} --new-path {}', account_info, file_path, filesystem,
                         '/'.join([new_filesystem, file])) \
            .assert_with_checks(JMESPathCheck('pathName', file))
        self.storage_cmd('storage fs file exists -p {} -f {}', account_info, file_path, filesystem) \
            .assert_with_checks(JMESPathCheck('exists', False))
        self.storage_cmd('storage fs file exists -p {} -f {}', account_info, file, new_filesystem) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage fs file delete -p {} -f {} -y', account_info, file, new_filesystem)

        self.storage_cmd('storage fs file exists -p {} -f {}', account_info, file, new_filesystem) \
            .assert_with_checks(JMESPathCheck('exists', False))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_metadata_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = self.create_random_name(prefix="dir", length=12)
        file = self.create_random_name(prefix="file", length=12)

        self.storage_cmd('storage fs metadata update -n {} --metadata a=b c=d',
                         account_info, filesystem)
        self.storage_cmd('storage fs metadata show -n {}', account_info, filesystem) \
            .assert_with_checks(JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'))

        self.storage_cmd('storage fs directory create -n {} -f {}',
                         account_info, directory, filesystem)
        self.storage_cmd('storage fs directory metadata update -n {} -f {} --metadata foo=bar moo=bak',
                         account_info, directory, filesystem)
        self.storage_cmd('storage fs directory metadata show -n {} -f {}', account_info, directory, filesystem) \
            .assert_with_checks(JMESPathCheck('foo', 'bar'), JMESPathCheck('moo', 'bak'))

        self.storage_cmd('storage fs file create -p {} -f {}',
                         account_info, file, filesystem)
        self.storage_cmd('storage fs file metadata update -p {} -f {} --metadata test=beta cat=file',
                         account_info, file, filesystem)
        self.storage_cmd('storage fs file metadata show -p {} -f {}', account_info, file, filesystem) \
            .assert_with_checks(JMESPathCheck('test', 'beta'), JMESPathCheck('cat', 'file'))
