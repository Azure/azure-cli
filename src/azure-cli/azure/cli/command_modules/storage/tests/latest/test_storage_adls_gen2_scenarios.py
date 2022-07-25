# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import os
import time
from datetime import datetime, timedelta

from azure.cli.testsdk import (ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck, JMESPathCheckExists,
                               api_version_constraint, RoleBasedServicePrincipalPreparer)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin, StorageTestFilesPreparer
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

    @unittest.skip('AssertionError: 0 != 1')
    @ResourceGroupPreparer(name_prefix='clitest', location='eastus2euap')
    @RoleBasedServicePrincipalPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_access_recursive_scenarios(self, resource_group, sp_name, sp_password, storage_account):
        import os
        # TODO: add back when other is ready
        # import time
        # self.cmd('role assignment create --role "Storage Blob Data Contributor" --assignee {} '.format('http://' + sp_name))
        # time.sleep(10)
        # self.cmd('login --service-principal -u {} -p {} --tenant 54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'.format(sp_name, sp_password))
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)

        dir0 = self.create_random_name(prefix="dir0", length=12)
        subdir0 = '/'.join([dir0, 'dir0'])
        subdir1 = '/'.join([dir0, 'dir1'])
        subdir2 = '/'.join([dir0, 'dir2'])

        file1 = '/'.join([subdir1, self.create_random_name(prefix="file1", length=12)])
        file2 = '/'.join([subdir1, self.create_random_name(prefix="file2", length=12)])
        file3 = '/'.join([subdir1, self.create_random_name(prefix="file3", length=12)])
        file4 = '/'.join([subdir2, self.create_random_name(prefix="file4", length=12)])
        file5 = '/'.join([subdir2, self.create_random_name(prefix="file5", length=12)])
        file6 = '/'.join([subdir2, self.create_random_name(prefix="file6", length=12)])

        local_file = self.create_temp_file(16)

        # Prepare files
        self.oauth_cmd('storage fs directory create -n "{}" -f {} --account-name {} '.format(
            dir0, filesystem, storage_account))
        self.oauth_cmd('storage fs directory create -n "{}" -f {} --account-name {} '.format(
            subdir0, filesystem, storage_account))
        self.oauth_cmd('storage fs directory create -n "{}" -f {} --account-name {} '.format(
            subdir1, filesystem, storage_account))
        self.oauth_cmd('storage fs directory create -n "{}" -f {} --account-name {} '.format(
            subdir2, filesystem, storage_account))

        self.storage_cmd('storage fs file upload -p "{}" -f {} -s "{}" ', account_info, file1, filesystem, local_file)
        self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} '.format(
            file2, filesystem, local_file, storage_account))
        self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} '.format(
            file3, filesystem, local_file, storage_account))
        self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} '.format(
            file4, filesystem, local_file, storage_account))
        self.storage_cmd('storage fs file upload -p "{}" -f {} -s "{}" ', account_info, file5, filesystem, local_file,
                         storage_account)
        self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} '.format(
            file6, filesystem, local_file, storage_account))

        # check permissions
        self.storage_cmd('storage fs access set -p "/" -f {} --permissions 111 ', account_info, filesystem)
        items = self.storage_cmd('storage fs file list -f {}  --exclude-dir --query [].name ',
                                 account_info, filesystem).get_output_in_json()
        for item in items:
            self.storage_cmd('storage fs access set -p "{}" -f {} --permissions rwxr-x--- ', account_info, item,
                             filesystem)

        acl1 = "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923:rwx"
        acl2 = "user::r-x"

        # ----------- directory ---------
        # set recursive
        self.storage_cmd('storage fs access set-recursive -f {} -p "{}" --acl {}', account_info, filesystem, dir0, acl1)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))
        # update recursive
        self.storage_cmd('storage fs access update-recursive -f {} -p "{}" --acl {}', account_info,
                         filesystem, subdir2, acl2)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 1),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 3))

        # remove recursive
        removal_acl = "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923"

        self.storage_cmd('storage fs access remove-recursive -f {} -p "{}"  --acl {}', account_info,
                         filesystem, dir0, removal_acl)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 4),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 6))

        # ----------- file ---------
        # set recursive
        self.storage_cmd('storage fs access set-recursive -f {} -p "{}" --acl {}', account_info, filesystem, file5, acl1)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 0),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 1))
        # update recursive
        self.storage_cmd('storage fs access update-recursive -f {} -p "{}" --acl {}', account_info, filesystem, file5, acl2)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 0),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 1))

        # remove recursive
        removal_acl = "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923"

        self.storage_cmd('storage fs access remove-recursive -f {} -p "{}" --acl {}', account_info, filesystem, file5, removal_acl)\
            .assert_with_checks(JMESPathCheck('continuation', None),
                                JMESPathCheck('counters.directoriesSuccessful', 0),
                                JMESPathCheck('counters.failureCount', 0),
                                JMESPathCheck('counters.filesSuccessful', 1))

        # Test continue on failure
        def reset_file_to_fail():
            # reset the file to make it failure in set acl resusive
            self.storage_cmd('storage fs file upload -p "{}" -f {} -s "{}" --overwrite', account_info, file1,
                             filesystem, local_file)
            self.storage_cmd('storage fs file upload -p "{}" -f {} -s "{}" --overwrite', account_info, file5,
                             filesystem, local_file)
        # set recursive
        result = self.oauth_cmd('storage fs access set-recursive -f {} -p "{}" --acl {} --batch-size 2 --max-batches 2 '
                                '--continue-on-failure --account-name {}'
                                .format(filesystem, dir0, acl1, storage_account)).get_output_in_json()

        self.assertIsNotNone(result['continuation'])
        self.assertEqual(result['counters']['directoriesSuccessful'], 3)
        self.assertEqual(result['counters']['failureCount'], 1)
        self.assertEqual(result['counters']['filesSuccessful'], 0)
        self.assertEqual(result['counters']['failureCount'], len(result['failedEntries']))

        # fix failed entries and recover from failure
        for item in result['failedEntries']:
            self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} --overwrite'.format(
                item['name'], filesystem, local_file, storage_account))
            self.oauth_cmd('storage fs access set-recursive -p "{}" -f {} --acl {} --account-name {} '
                           '--continue-on-failure false'.format(item['name'], filesystem, acl1, storage_account))

        # update recursive
        reset_file_to_fail()

        result = self.oauth_cmd('storage fs access update-recursive -f {} -p "{}" --acl {} --batch-size 3 '
                                '--continue-on-failure --account-name {}'.format(filesystem, dir0, acl1,
                                                                                 storage_account)).get_output_in_json()

        self.assertEqual(result['counters']['directoriesSuccessful'], 4)
        self.assertEqual(result['counters']['failureCount'], 2)
        self.assertEqual(result['counters']['filesSuccessful'], 4)
        self.assertEqual(result['counters']['failureCount'], len(result['failedEntries']))

        # fix failed entries and recover from failure
        for item in result['failedEntries']:
            self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} --permissions rwxr-x--- '
                           '--overwrite'.format(item['name'], filesystem, local_file, storage_account))
            self.oauth_cmd('storage fs access update-recursive -p "{}" -f {} --acl {} --account-name {} '
                           '--continue-on-failure false'.format(item['name'], filesystem, acl2, storage_account))

        # remove recursive
        reset_file_to_fail()

        result = self.oauth_cmd('storage fs access remove-recursive -f {} -p "{}" --acl {} --batch-size 20 '
                                '--continue-on-failure --account-name {} '
                                .format(filesystem, dir0, removal_acl, storage_account)).get_output_in_json()

        self.assertEqual(result['counters']['directoriesSuccessful'], 4)
        self.assertEqual(result['counters']['failureCount'], 2)
        self.assertEqual(result['counters']['filesSuccessful'], 4)
        self.assertEqual(result['counters']['failureCount'], len(result['failedEntries']))

        # fix failed entries and recover from failure
        for item in result['failedEntries']:
            self.oauth_cmd('storage fs file upload -p "{}" -f {} -s "{}" --account-name {} --permissions rwxr-x--- '
                           '--overwrite'.format(item['name'], filesystem, local_file, storage_account))
            self.oauth_cmd('storage fs access remove-recursive -p "{}" -f {} --acl {} --account-name {} '
                           '--continue-on-failure false'.format(item['name'], filesystem, removal_acl, storage_account))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_filesystem_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_str = self.cmd('storage account show-connection-string -n {} -g {} -otsv'
                                  .format(storage_account, resource_group)).output

        # Test with account key
        filesystem1 = self.create_random_name(prefix='filesystem', length=24)
        self.storage_cmd('storage fs exists -n {}', account_info, filesystem1) \
            .assert_with_checks(JMESPathCheck('exists', False))
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
    @StorageAccountPreparer(kind="StorageV2", hns=True, location="eastus2euap")
    def test_adls_fs_soft_delete(self, resource_group, storage_account_info):
        account_info = storage_account_info
        container = self.create_file_system(account_info)
        # Prepare
        local_file = self.create_temp_file(1)
        file_name = self.create_random_name(prefix='file', length=24)
        dir_name = 'dir'

        self.storage_cmd('storage fs file upload -f {} -s "{}" -p {} ', account_info,
                         container, local_file, file_name)
        self.assertEqual(len(self.storage_cmd('storage fs file list -f {}',
                                              account_info, container).get_output_in_json()), 1)
        self.storage_cmd('storage fs directory create -f {} -n {} ', account_info,
                         container, dir_name)
        self.assertEqual(len(self.storage_cmd('storage fs file list -f {}',
                                              account_info, container).get_output_in_json()), 2)

        # set delete-policy to enable soft-delete
        self.storage_cmd('storage fs service-properties update --delete-retention --delete-retention-period 2',
                         account_info)
        self.storage_cmd('storage fs service-properties show',
                         account_info).assert_with_checks(JMESPathCheck('delete_retention_policy.enabled', True),
                                                          JMESPathCheck('delete_retention_policy.days', 2))
        time.sleep(10)
        # soft-delete and check
        self.storage_cmd('storage fs file delete -f {} -p {} -y', account_info, container, file_name)
        self.storage_cmd('storage fs directory delete -f {} -n {} -y', account_info, container, dir_name)
        self.assertEqual(len(self.storage_cmd('storage fs file list -f {}',
                                              account_info, container).get_output_in_json()), 0)

        time.sleep(60)
        result = self.storage_cmd('storage fs list-deleted-path -f {} --path-prefix {} ',
                                  account_info, container, dir_name).get_output_in_json()
        self.assertEqual(len(result), 1)

        time.sleep(60)
        result = self.storage_cmd('storage fs list-deleted-path -f {}', account_info, container) \
            .get_output_in_json()
        self.assertEqual(len(result), 2)

        result = self.storage_cmd('storage fs list-deleted-path -f {} --num-results 1', account_info, container) \
            .get_output_in_json()
        self.assertEqual(len(result), 2)
        marker = result[-1]['nextMarker']

        result = self.storage_cmd('storage fs list-deleted-path -f {} --marker {}', account_info, container, marker) \
            .get_output_in_json()
        self.assertEqual(len(result), 1)

        deleted_version = result[0]["deletionId"]

        # undelete and check
        self.storage_cmd('storage fs undelete-path -f {} --deleted-path-name {} --deletion-id  {}',
                         account_info, container, file_name, deleted_version)
        self.assertEqual(len(self.storage_cmd('storage fs file list -f {}',
                                              account_info, container).get_output_in_json()), 1)

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
        with self.assertRaisesRegex(CLIError, 'You cannot upload to an existing non-empty file with overwrite=false.'):
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

        # List files with marker
        result = self.storage_cmd('storage fs file list -f {} --num-results 1 --show-next-marker',
                                  account_info, filesystem).get_output_in_json()
        self.assertIsNotNone(result[1]['nextMarker'])
        next_marker = result[1]['nextMarker']

        self.storage_cmd('storage fs file list -f {} --num-results 1 --marker {}',
                         account_info, filesystem, next_marker).assert_with_checks(JMESPathCheck('length(@)', 1))

        # List files excluding directory with marker
        result = self.storage_cmd('storage fs file list -f {} --num-results 1 --show-next-marker --exclude-dir',
                                  account_info, filesystem).get_output_in_json()
        self.assertIsNotNone(result[0]['nextMarker'])

        # Download file
        local_dir = self.create_temp_dir()
        self.storage_cmd('storage fs file download -p {} -f {} -d "{}"', account_info, file_path, filesystem, local_dir)
        import os
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_dir)))

        with self.assertRaisesRegex(CLIError, "The specified path already exists. Please change to a valid path."):
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

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_fs_generate_sas_full_uri(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        f = self.create_file_system(account_info)

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        fs_uri = self.storage_cmd('storage fs generate-sas -n {} --expiry {} --permissions '
                                  'r --https-only --full-uri', account_info, f, expiry).output
        self.assertTrue(fs_uri)
        self.assertIn('&sig=', fs_uri)
        self.assertTrue(fs_uri.startswith('"https://{}.dfs.core.windows.net/{}?s'.format(storage_account, f)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_fs_generate_sas_as_user(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        f = self.create_file_system(account_info)

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        with self.assertRaisesRegex(CLIError, "incorrect usage: specify --as-user when --auth-mode login"):
            self.cmd('storage fs generate-sas --account-name {} -n {} --expiry {} --permissions r --https-only '
                     '--auth-mode login'.format(storage_account, f, expiry))

        fs_sas = self.cmd('storage fs generate-sas --account-name {} -n {} --expiry {} --permissions '
                          'dlrwop --https-only --as-user --auth-mode login'.format(storage_account, f, expiry)).output
        self.assertIn('&sig=', fs_sas)
        self.assertIn('skoid=', fs_sas)
        self.assertIn('sktid=', fs_sas)
        self.assertIn('skt=', fs_sas)
        self.assertIn('ske=', fs_sas)
        self.assertIn('sks=', fs_sas)
        self.assertIn('skv=', fs_sas)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_storage_fs_directory_generate_sas_full_uri(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = 'testdir/subdir'

        self.storage_cmd('storage fs directory create -n {} -f {}',
                         account_info, directory, filesystem)

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        fs_uri = self.storage_cmd('storage fs directory generate-sas -n {} -f {} --expiry {} --permissions '
                                  'r --https-only --full-uri', account_info, directory, filesystem, expiry).output
        self.assertTrue(fs_uri)
        self.assertIn('&sig=', fs_uri)
        self.assertTrue(fs_uri.startswith('"https://{}.dfs.core.windows.net/{}/{}?s'.format(storage_account,
                                                                                            filesystem, directory)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_storage_fs_directory_generate_sas_as_user(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = 'testdir/subdir'

        self.storage_cmd('storage fs directory create -n {} -f {}', account_info, directory, filesystem)

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        with self.assertRaisesRegex(CLIError, "incorrect usage: specify --as-user when --auth-mode login"):
            self.cmd('storage fs directory generate-sas --account-name {} -n {} -f {} --expiry {} --permissions r '
                     '--https-only --auth-mode login'.format(storage_account, directory, filesystem, expiry))

        fs_sas = self.cmd('storage fs directory generate-sas --account-name {} -n {} -f {} --expiry {} --permissions '
                          'dlrwop --https-only --as-user --auth-mode login'.format(storage_account, directory,
                                                                                   filesystem, expiry)).output
        self.assertIn('&sig=', fs_sas)
        self.assertIn('skoid=', fs_sas)
        self.assertIn('sktid=', fs_sas)
        self.assertIn('skt=', fs_sas)
        self.assertIn('ske=', fs_sas)
        self.assertIn('sks=', fs_sas)
        self.assertIn('skv=', fs_sas)
        self.assertIn('sr=d', fs_sas)
        self.assertIn('sdd=2', fs_sas)

class StorageADLSGen2LiveTests(StorageScenarioMixin, LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    @StorageTestFilesPreparer()
    def test_adls_directory_upload(self, resource_group, storage_account, test_dir):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        filesystem = 'testfilesystem'
        directory = 'testdir'
        self.storage_cmd('storage fs create -n {}', account_info, filesystem)
        self.storage_cmd('storage fs directory create -n {} -f {}', account_info, directory, filesystem)

        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage container generate-sas -n {} --https-only '
                               '--permissions acdlrw --expiry {} -otsv',
                               account_info, filesystem, expiry).output.strip()

        # Upload a single file to the fs directory
        self.storage_cmd('storage fs directory upload -f {} -d {} -s "{}"', account_info, filesystem, directory,
                         os.path.join(test_dir, 'readme'))
        self.storage_cmd('storage fs file list -f {} --path {}', account_info, filesystem, directory) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # Upload a local directory to the fs directory
        self.oauth_cmd('storage fs directory upload -f {} -d {} -s "{}" --recursive --account-name {}', filesystem,
                       directory, os.path.join(test_dir, 'apple'), storage_account)
        self.oauth_cmd('storage fs file list -f {} --path {} --account-name {}',
                       filesystem, directory, storage_account)\
            .assert_with_checks(JMESPathCheck('length(@)', 12))

        # Upload files in a local directory to the fs directory
        self.cmd('storage fs directory upload -f {} -d {} -s "{}" --recursive --connection-string {}'
                 .format(filesystem, directory, os.path.join(test_dir, 'butter/file_*'), connection_string))
        self.cmd('storage fs file list -f {} --path {} --connection-string {}'
                 .format(filesystem, directory, connection_string), checks=[JMESPathCheck('length(@)', 22)])

        # Upload files in a local directory to the fs subdirectory
        self.cmd('storage fs directory upload -f {} -d {} -s "{}" --recursive --account-name {} --sas-token {}'
                 .format(filesystem, '/'.join([directory, 'subdir']),
                         os.path.join(test_dir, 'butter/file_*'), storage_account, sas))
        self.cmd('storage fs file list -f {} --path {} --account-name {} --sas-token {}'
                 .format(filesystem, '/'.join([directory, 'subdir']), storage_account, sas),
                 checks=[JMESPathCheck('length(@)', 10)])

        # Upload single file to the fs root directory
        self.storage_cmd('storage fs directory upload -f {} -s "{}"', account_info, filesystem,
                         os.path.join(test_dir, 'readme'))
        self.storage_cmd('storage fs file exists -f {} --path {}', account_info, filesystem, 'readme') \
            .assert_with_checks(JMESPathCheck('exists', True))

        # Upload files to the fs root directory
        self.storage_cmd('storage fs directory upload -f {} -s "{}" -r', account_info, filesystem,
                         os.path.join(test_dir, 'duff'))
        self.storage_cmd('storage fs file exists -f {} --path {}', account_info, filesystem, 'duff/edward') \
            .assert_with_checks(JMESPathCheck('exists', True))

        # Argument validation: Fail when destination path is file name
        self.cmd('storage fs directory upload -f {} -d {} -s {} --account-name {}'.format(
            filesystem, '/'.join([directory, 'readme']), test_dir, storage_account), expect_failure=True)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    @StorageTestFilesPreparer()
    def test_adls_directory_download(self, resource_group, storage_account, test_dir):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        filesystem = 'testfilesystem'
        directory = 'testdir'
        self.storage_cmd('storage fs create -n {}', account_info, filesystem)
        self.storage_cmd('storage fs directory create -n {} -f {}', account_info, directory, filesystem)
        self.storage_cmd('storage fs directory upload -f {} -d {} -s "{}" --recursive', account_info, filesystem,
                         directory, os.path.join(test_dir, 'readme'))
        self.storage_cmd('storage fs directory upload -f {} -d {} -s "{}" --recursive', account_info, filesystem,
                         directory, os.path.join(test_dir, 'apple'))

        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage container generate-sas -n {} --https-only '
                               '--permissions lr --expiry {} -otsv',
                               account_info, filesystem, expiry).output.strip()

        local_folder = self.create_temp_dir()
        # Download a single file
        self.storage_cmd('storage fs directory download -f {} -s "{}" -d "{}" --recursive', account_info, filesystem,
                         '/'.join([directory, 'readme']), local_folder)
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download entire directory
        self.oauth_cmd('storage fs directory download -f {} -s {} -d "{}" --recursive --account-name {}',
                       filesystem, directory, local_folder, storage_account)
        self.assertEqual(2, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(12, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download an entire subdirectory of a storage blob directory.
        self.cmd('storage fs directory download -f {} -s {} -d "{}" --recursive --connection-string {}'
                 .format(filesystem, '/'.join([directory, 'apple']), local_folder, connection_string))
        self.assertEqual(3, sum(len(d) for r, d, f in os.walk(local_folder)))

        # Download from root directory
        self.cmd('storage fs directory download -f {} -d "{}" --recursive --account-name {} --sas-token {}'
                 .format(filesystem, local_folder, storage_account, sas))
        self.assertEqual(6, sum(len(d) for r, d, f in os.walk(local_folder)))
