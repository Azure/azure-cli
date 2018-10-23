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
                  JMESPathCheck('sku.name', SkuName.standard_akamai.value)]
        self.profile_create_cmd(resource_group, profile_name, checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.profile_list_cmd(resource_group, checks=list_checks)

        checks.append(JMESPathCheck('tags.foo', 'bar'))
        self.profile_update_cmd(resource_group, profile_name, tags='foo=bar', checks=checks)

        self.profile_delete_cmd(resource_group, profile_name)


class CdnCustomDomainScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cdn_domain')
    def test_cdn_custom_domain(self, resource_group):
        from azure.mgmt.cdn.models import ErrorResponseException
        from knack.util import CLIError

        self.kwargs.update({
            'profile': 'cdnprofile1',
            'endpoint': self.create_random_name(prefix='endpoint', length=24),
            'origin': 'www.test.com',
            'hostname': 'www.example.com',
            'name': 'customdomain1'
        })

        self.cmd('cdn profile create -g {rg} -n {profile}')
        self.cmd('cdn endpoint create -g {rg} --origin {origin} --profile-name {profile} -n {endpoint}')
        self.cmd('cdn custom-domain list -g {rg} --endpoint-name {endpoint} --profile-name {profile}')

        # These will all fail because we don't really have the ability to create the custom endpoint in test.
        # but they should still fail if there was a CLI-level regression.
        with self.assertRaises(ErrorResponseException):
            self.cmd(
                'cdn custom-domain create -g {rg} --endpoint-name {endpoint} --hostname {hostname} --profile-name {profile} -n {name}')
        with self.assertRaises(SystemExit):  # exits with code 3 due to missing resource
            self.cmd('cdn custom-domain show -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        self.cmd('cdn custom-domain delete -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        with self.assertRaises(CLIError):
            self.cmd(
                'cdn custom-domain enable-https -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        with self.assertRaises(CLIError):
            self.cmd(
                'cdn custom-domain disable-https -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
