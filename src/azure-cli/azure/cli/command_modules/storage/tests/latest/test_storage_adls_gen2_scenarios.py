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
