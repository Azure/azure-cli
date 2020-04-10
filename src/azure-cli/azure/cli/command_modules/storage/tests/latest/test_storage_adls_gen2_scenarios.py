# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck, NoneCheck,
                               api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.DATA_STORAGE_FILEDATALAKE, min_api='2018-11-09')
class StorageADLSGen2Tests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_access_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        #TODO: Change to create_file_system() when ready
        filesystem = self.create_container(account_info)

        dir = self.create_random_name(prefix="dir", length=12),
        subdir = self.create_random_name(prefix="subdir", length=12)
        subpath = '/'.join([dir, subdir])

        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, dir, filesystem)
        # Create Directory
        self.storage_cmd('storage fs directory create -n {} -f {}', account_info, dir, filesystem)

        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, dir, filesystem)
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, dir, filesystem)

        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, subpath, filesystem)
        self.storage_cmd('storage fs directory create -n {} -f {}', account_info, subpath, filesystem)

        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, subpath, filesystem)
        self.storage_cmd('storage fs directory show -n {} -f {}', account_info, subpath, filesystem)

        new_dir = '/'.join([filesystem, 'newdir'])
        self.storage_cmd('storage fs directory move -n {} -f {} -d {}', account_info, subpath, filesystem, new_dir)
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, subpath, filesystem)
        self.storage_cmd('storage fs directory exists -n {} -f {}', account_info, 'newdir', filesystem)

        self.storage_cmd('storage fs directory list -f {}', account_info, filesystem)

        self.storage_cmd('storage fs directory list --path {} -f {}', account_info, dir, filesystem)

        self.storage_cmd('storage fs directory delete -n {} -f {} -y', account_info, dir, filesystem)

        self.storage_cmd('storage fs directory list -f {}', account_info, filesystem)


        # Set owning group
        group = "john.doe@contoso"
        self.storage_cmd('storage fs access set -f {} -p / --group {}', account_info, filesystem, group) \
            .assert_with_checks(JMESPathCheck('group', group))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_filesystem_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)

        filesystem1 = self.create_random_name(prefix='filesystem', length=24)
        self.storage_cmd('storage fs create -n {} --public-access file', account_info, filesystem1)

        self.storage_cmd('storage fs show -n {}', account_info, filesystem1)\
            .assert_with_checks(JMESPathCheck('name', filesystem1)) \
            .assert_with_checks(JMESPathCheck('publicAccess', 'file'))

        filesystem2 = self.create_random_name(prefix='filesystem', length=24)
        self.storage_cmd('storage fs create -n {} --public-access filesystem', account_info, filesystem2)

        self.storage_cmd('storage fs show -n {}', account_info, filesystem2) \
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
        self.kwargs = {
            "fs": filesystem,
            "dir": self.create_random_name(prefix="dir", length=12),
            "subdir": self.create_random_name(prefix="subdir", length=12)
        }

        # Create Directory
        self.storage_cmd('storage fs directory create -n {dir} -f {subdir}', account_info)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_adls_file_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        filesystem = self.create_file_system(account_info)
        directory = self.create_random_name(prefix="dir", length=12),
        file = self.create_random_name(prefix="file", length=12)

        # Create File
        self.storage_cmd('storage fs file exists -n {} -f {}', account_info, file, filesystem)
        self.storage_cmd('storage fs file create -n {} -f {}', account_info, file, filesystem)
        self.storage_cmd('storage fs file show -n {} -f {}', account_info, file, filesystem)
        self.storage_cmd('storage fs file append -n {} -f {} --content "testappend"', account_info, file, filesystem)

        file_path = '/'.join([directory, file])
        local_file = self.create_temp_file(1024)
        self.storage_cmd('storage fs file upload -p {} -f {} -s {}', account_info, file_path, filesystem, local_file)

        self.storage_cmd('storage fs file list -n {} -f {}', account_info, file, filesystem, checks=[
            JMESPathCheck('length(@)', 3)
        ])

        self.storage_cmd('storage fs file list -n {} -f {} --exclude-dir', account_info, file, filesystem, checks=[
            JMESPathCheck('length(@)', 2)
        ])

        local_dir = self.create_temp_dir()
        self.storage_cmd('storage fs file download -p {} -f {} -d {}', account_info, file_path, filesystem, local_dir)
        import os
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_dir)))

        self.storage_cmd('storage fs file move -p {} -f {} -s {}', account_info, file_path, filesystem, local_file)

        self.storage_cmd('storage fs file delete -p {} -f {} -y', account_info, file_path, filesystem)
        self.storage_cmd('storage fs file exists -n {} -f {}', account_info, file, filesystem)
