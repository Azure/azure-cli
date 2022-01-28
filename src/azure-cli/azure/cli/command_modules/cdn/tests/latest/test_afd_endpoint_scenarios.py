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
        origin_response_timeout_seconds = 100
        enabled_state = "Enabled"
        checks = [JMESPathCheck('originResponseTimeoutSeconds', 100),
                  JMESPathCheck('enabledState', 'Enabled')]
        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     origin_response_timeout_seconds,
                                     enabled_state,
                                     checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].hostName', f'{endpoint_name}.z01.azurefd.net'),
                       JMESPathCheck('@[0].originResponseTimeoutSeconds', 100),
                       JMESPathCheck('@[0].enabledState', 'Enabled')]
        self.afd_endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        update_checks = [JMESPathCheck('hostName', f'{endpoint_name}.z01.azurefd.net'),
                         JMESPathCheck('originResponseTimeoutSeconds', 100),
                         JMESPathCheck('enabledState', 'Disabled')]
        options = '--enabled-state Disabled'
        self.afd_endpoint_update_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     options=options,
                                     checks=update_checks)

        update_checks = [JMESPathCheck('hostName', f'{endpoint_name}.z01.azurefd.net'),
                         JMESPathCheck('originResponseTimeoutSeconds', 120),
                         JMESPathCheck('enabledState', 'Enabled')]
        options = '--origin-response-timeout-seconds 120 --enabled-state Enabled'
        self.afd_endpoint_update_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     options=options,
                                     checks=update_checks)

        self.afd_endpoint_delete_cmd(resource_group, endpoint_name, profile_name)

    @ResourceGroupPreparer()
    def test_afd_endpoint_purge(self, resource_group):
        profile_name = 'profile123'
        self.afd_profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin_response_timeout_seconds = 100
        enabled_state = "Enabled"
        self.afd_endpoint_create_cmd(resource_group, profile_name, endpoint_name, origin_response_timeout_seconds, enabled_state)

        content_paths = ['/index.html', '/javascript/*']
        self.afd_endpoint_purge_cmd(resource_group, endpoint_name, profile_name, content_paths)

        self.afd_endpoint_purge_cmd(resource_group, endpoint_name, profile_name, content_paths, domains=[f'{endpoint_name}.z01.azurefd.net'])
