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
        filesystem = self.create_container(account_info)
        self.kwargs = {
            "fs": filesystem,
            "dir": self.create_random_name(prefix="dir", length=12),
            "file": self.create_random_name(prefix="file", length=12)
        }
        # Set access control
        acl = "user::rwx,user:john.doe@contoso:rwx,group::r--,other::---,mask::rwx"
        self.storage_cmd('storage fs access set -f {} -p / --acl {}', account_info, filesystem, acl)
        self.storage_cmd('storage fs access show -f {} -p /', account_info, filesystem).assert_with_checks(
            JMESPathCheck('acl', acl))

        # Set permissions
        permissions = "rwxrwxrwx"
        self.storage_cmd('storage fs access set -f {} -p / --permissions {}', account_info, filesystem, permissions)
        self.storage_cmd('storage fs access show -f {} -p /', account_info, filesystem).assert_with_checks(
            JMESPathCheck('permissions', permissions))

        # Set owner
        owner = "john.doe@contoso"
        self.storage_cmd('storage fs access set -f {} -p / --owner {}', account_info, filesystem, owner)
        self.storage_cmd('storage fs access show -f {} -p /', account_info, filesystem).assert_with_checks(
            JMESPathCheck('permissions', permissions))

        # Set owning group
        group = "john.doe@contoso"
        self.storage_cmd('storage fs access set -f {} -p / --group {}', account_info, filesystem, group) \
            .assert_with_checks(JMESPathCheck('group', group))
