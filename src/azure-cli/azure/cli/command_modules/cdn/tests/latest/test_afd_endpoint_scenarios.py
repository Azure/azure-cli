# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnAfdEndpointScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_endpoint_crud(self, resource_group):
        profile_name = 'profile123'
        self.afd_endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.afd_profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        enabled_state = "Enabled"

        checks = [JMESPathCheck('enabledState', 'Enabled')]
        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     enabled_state,
                                     name_reuse_scope="ResourceGroupReuse",
                                     checks=checks)
        endpoint = self.afd_endpoint_show_cmd(resource_group, profile_name, endpoint_name).get_output_in_json()
        hostName = endpoint["hostName"] 

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].hostName', hostName),
                       JMESPathCheck('@[0].enabledState', 'Enabled')]
        self.afd_endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        update_checks = [JMESPathCheck('hostName', hostName),
                         JMESPathCheck('enabledState', 'Disabled')]
        options = '--enabled-state Disabled'
        self.afd_endpoint_update_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     options=options,
                                     checks=update_checks)

        update_checks = [JMESPathCheck('hostName', hostName),
                         JMESPathCheck('enabledState', 'Enabled')]
        options = '--enabled-state Enabled'
        self.afd_endpoint_update_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     options=options,
                                     checks=update_checks)


    @ResourceGroupPreparer()
    def test_afd_endpoint_purge(self, resource_group):
        profile_name = 'profile123'
        self.afd_profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        enabled_state = "Enabled"
        self.afd_endpoint_create_cmd(resource_group, profile_name, endpoint_name, enabled_state)
        endpoint = self.afd_endpoint_show_cmd(resource_group, profile_name, endpoint_name).get_output_in_json()
        hostName = endpoint["hostName"]        
        
        content_paths = ['/index.html', '/javascript/*']
        self.afd_endpoint_purge_cmd(resource_group, endpoint_name, profile_name, content_paths)

        self.afd_endpoint_purge_cmd(resource_group, endpoint_name, profile_name, content_paths, domains=[hostName])
