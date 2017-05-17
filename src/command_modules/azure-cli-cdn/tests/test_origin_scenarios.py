# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, JMESPathCheck
from .scenario_mixin import CdnScenarioMixin


class CdnOriginScenarioTest(CdnScenarioMixin, ScenarioTest):

    @ResourceGroupPreparer()
    def test_origin_list_and_show(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        checks = [JMESPathCheck('length(@)', 1)]
        origins = self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        origin_name = origins.json_value[0]["name"]
        checks = [JMESPathCheck('name', origin_name)]
        self.origin_show_cmd(resource_group,
                             endpoint_name,
                             profile_name,
                             origin_name,
                             checks=checks)
