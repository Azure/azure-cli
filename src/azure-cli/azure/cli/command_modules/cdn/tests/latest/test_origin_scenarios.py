# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, JMESPathCheck
from .scenario_mixin import CdnScenarioMixin


class CdnOriginScenarioTest(CdnScenarioMixin, ScenarioTest):

    @ResourceGroupPreparer()
    def test_origin_crud(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        checks = [JMESPathCheck('length(origins)', 1)]
        endpoint = self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        origin = self.origin_show_cmd(resource_group, endpoint_name, profile_name, endpoint.json_value['origins'][0]['name'])

        checks = [JMESPathCheck('length(@)', 1)]
        origins = self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        pls_subscription_id = 'da61bba1-cbd5-438c-a738-c717a6b2d59f'
        # Workaround for overly heavy-handed subscription id replacement in playback mode.
        if self.is_playback_mode():
            pls_subscription_id = '00000000-0000-0000-0000-000000000000'
        origin_name = origins.json_value[0]["name"]
        private_link_id = f'/subscriptions/{pls_subscription_id}/resourceGroups/moeidrg/providers/Microsoft.Network/privateLinkServices/pls-east'
        private_link_location = 'EastUS'
        private_link_message = 'Please approve the request'

        checks = [JMESPathCheck('name', origin_name),
                  JMESPathCheck('httpPort', 8080),
                  JMESPathCheck('httpsPort', 8443),
                  JMESPathCheck('privateLinkResourceId', private_link_id),
                  JMESPathCheck('privateLinkLocation', private_link_location),
                  JMESPathCheck('privateLinkApprovalMessage', private_link_message)]
        self.origin_update_cmd(resource_group,
                               origin_name,
                               endpoint_name,
                               profile_name,
                               http_port='8080',
                               https_port='8443',
                               private_link_id=private_link_id,
                               private_link_location=private_link_location,
                               private_link_message=private_link_message,
                               checks=checks)

        checks = [JMESPathCheck('name', origin_name),
                  JMESPathCheck('httpPort', 8080),
                  JMESPathCheck('httpsPort', 8443),
                  JMESPathCheck('privateLinkResourceId', private_link_id),
                  JMESPathCheck('privateLinkLocation', private_link_location),
                  JMESPathCheck('privateLinkApprovalMessage', private_link_message)]
        self.origin_show_cmd(resource_group,
                             endpoint_name,
                             profile_name,
                             origin_name,
                             checks=checks)
