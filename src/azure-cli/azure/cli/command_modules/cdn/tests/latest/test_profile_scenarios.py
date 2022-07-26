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
    def test_cdn_profile_crud(self, resource_group):
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.profile_list_cmd(resource_group, checks=list_checks)

        profile_name = 'profile123'
        checks = [JMESPathCheck('name', profile_name),
                  JMESPathCheck('sku.name', SkuName.STANDARD_AKAMAI)]
        self.profile_create_cmd(resource_group, profile_name, checks=checks)
        self.profile_show_cmd(resource_group, profile_name, checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.profile_list_cmd(resource_group, checks=list_checks)

        checks.append(JMESPathCheck('tags.foo', 'bar'))
        self.profile_update_cmd(resource_group, profile_name, tags='foo=bar', checks=checks)

        self.profile_delete_cmd(resource_group, profile_name)


class CdnProfileDeleteDoesNotExistScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_cdn_profile_delete_not_found(self, resource_group):
        # see https://github.com/Azure/azure-cli/issues/3304
        # request should respond with a 204 rather than a 404
        res = self.profile_delete_cmd(resource_group, "foo12345")
        self.assertEqual("", res.output)


class CdnProfileMicrosoftScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_cdn_microsoft_standard_sku(self, resource_group):
        # https://github.com/Azure/azure-cli/issues/7635
        self.kwargs.update({
            'profile': 'cdnprofile1',
            'sku': 'Standard_Microsoft',
            'rg': resource_group,
        })
        self.cmd('cdn profile create -g {rg} -n {profile} --sku {sku}')
