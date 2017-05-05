# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, JMESPathCheck
from .scenario_mixin import CdnScenarioMixin


class CdnCustomDomainScenarioTest(CdnScenarioMixin, ScenarioTest):

    @ResourceGroupPreparer()
    def test_custom_domain_list(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.custom_domain_list_cmd(resource_group, endpoint_name, profile_name, checks=list_checks)
