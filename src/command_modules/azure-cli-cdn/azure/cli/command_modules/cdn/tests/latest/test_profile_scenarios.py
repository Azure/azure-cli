# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
from azure.mgmt.cdn.models import SkuName
from .scenario_mixin import CdnScenarioMixin


class CdnProfileScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_profile_crud(self, resource_group):
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.profile_list_cmd(resource_group, checks=list_checks)

        profile_name = 'profile123'
        checks = [JMESPathCheck('name', profile_name),
                  JMESPathCheck('sku.name', SkuName.standard_akamai.value)]
        self.profile_create_cmd(resource_group, profile_name, checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.profile_list_cmd(resource_group, checks=list_checks)

        checks.append(JMESPathCheck('tags.foo', 'bar'))
        self.profile_update_cmd(resource_group, profile_name, tags='foo=bar', checks=checks)

        self.profile_delete_cmd(resource_group, profile_name)
