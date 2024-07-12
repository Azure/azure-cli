# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
import time
from .scenario_mixin import CdnScenarioMixin


class ClassicCdnMigration(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_classic_cdn_migration_commit(self, resource_group):
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.profile_list_cmd(resource_group, checks=list_checks)

        profile_name = 'profile123'
        checks = [JMESPathCheck('name', profile_name),
                  JMESPathCheck('sku.name', 'Standard_Microsoft')]
        self.profile_create_cmd(resource_group, profile_name, sku='Standard_Microsoft', checks=checks)

        checks = [JMESPathCheck('canMigrate', True),
                  JMESPathCheck('type', 'Microsoft.Cdn/canmigrate')]
        self.cdn_can_migrate_to_afd(resource_group, profile_name, checks=checks)

        checks = [JMESPathCheck('type', 'Microsoft.Cdn/migrate')]
        self.cdn_migrate_to_afd(resource_group, profile_name, sku='Premium_AzureFrontDoor', checks=checks)

        time.sleep(30)

        # self.cdn_migration_commit(resource_group, profile_name)

        # self.profile_delete_cmd(resource_group, profile_name)

    # skip "https://github.com/Azure/azure-cli/issues/28678"
    # @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    # def test_classic_cdn_migration_abort(self, resource_group):
    #     list_checks = [JMESPathCheck('length(@)', 0)]
    #     self.profile_list_cmd(resource_group, checks=list_checks)

    #     profile_name = 'profile123'
    #     checks = [JMESPathCheck('name', profile_name),
    #               JMESPathCheck('sku.name', 'Standard_Microsoft')]
    #     self.profile_create_cmd(resource_group, profile_name, sku='Standard_Microsoft', checks=checks)

    #     checks = [JMESPathCheck('canMigrate', True),
    #               JMESPathCheck('type', 'Microsoft.Cdn/canmigrate')]
    #     self.cdn_can_migrate_to_afd(resource_group, profile_name, checks=checks)

    #     checks = [JMESPathCheck('type', 'Microsoft.Cdn/migrate')]
    #     self.cdn_migrate_to_afd(resource_group, profile_name, sku='Premium_AzureFrontDoor', checks=checks)

    #     self.cdn_migration_abort(resource_group, profile_name)

    #     self.profile_delete_cmd(resource_group, profile_name)

    def test_classic_cdn_migration_with_endpoint(self):
        rg_name = "cli-test-rg"
        profile_name = "cli-test-profile"
        checks = [JMESPathCheck('canMigrate', True),
                  JMESPathCheck('type', 'Microsoft.Cdn/canmigrate')]
        self.cdn_can_migrate_to_afd(rg_name, profile_name, checks=checks)

        maps = "[{{migrated-from:maxtestendpointcli-test-profile1.azureedge.net,migrated-to:maxtestendpointcli-test-profile2}}]"
        self.cdn_migrate_to_afd(rg_name, profile_name, "Premium_AzureFrontDoor", maps)

    def test_classic_cdn_migration_abort(self):
        rg_name = "cli-test-rg"
        profile_name = "cli-test-profile"
        self.cdn_migration_abort(rg_name, profile_name)
