
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .scenario_mixin import CdnScenarioMixin

from azure.mgmt.cdn.models import SkuName


class CdnEndpointScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_endpoint_crud(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        
        name_exist_checks = [JMESPathCheck('reason', None),
                             JMESPathCheck('nameAvailable', True)]
        self.cmd(f"cdn name-exists --name {endpoint_name}", checks=name_exist_checks)

        origin = 'www.contoso.com'
        checks = [JMESPathCheck('name', endpoint_name),
                  JMESPathCheck('origins[0].hostName', origin),
                  JMESPathCheck('isHttpAllowed', True),
                  JMESPathCheck('isHttpsAllowed', True),
                  JMESPathCheck('isCompressionEnabled', False),
                  JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        self.endpoint_create_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 origin,
                                 checks=checks)
 
        name_exist_checks = [JMESPathCheck('reason', "Name is already in use"),
                             JMESPathCheck('nameAvailable', False)]
        self.cmd(f"cdn name-exists --name {endpoint_name}", checks=name_exist_checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', endpoint_name),
                       JMESPathCheck('@[0].origins[0].hostName', origin),
                       JMESPathCheck('@[0].isHttpAllowed', True),
                       JMESPathCheck('@[0].isHttpsAllowed', True),
                       JMESPathCheck('@[0].isCompressionEnabled', False),
                       JMESPathCheck('@[0].queryStringCachingBehavior', 'IgnoreQueryString')]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', False),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', True),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        options = '--no-http --enable-compression'
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=options,
                                 checks=update_checks)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', False),
                         JMESPathCheck('isCompressionEnabled', False),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        options = '--no-http false --no-https --enable-compression false'
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=options,
                                 checks=update_checks)

        self.endpoint_delete_cmd(resource_group, endpoint_name, profile_name)

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_endpoint_compression(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name)
        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.contoso.com'
        create_options = '--enable-compression --content-types-to-compress text/plain text/html'
        checks = [JMESPathCheck('name', endpoint_name),
                  JMESPathCheck('origins[0].hostName', origin),
                  JMESPathCheck('isHttpAllowed', True),
                  JMESPathCheck('isHttpsAllowed', True),
                  JMESPathCheck('isCompressionEnabled', True),
                  JMESPathCheck('contentTypesToCompress[0]', "text/plain"),
                  JMESPathCheck('contentTypesToCompress[1]', "text/html"),
                  JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        self.endpoint_create_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 origin,
                                 checks=checks,
                                 options=create_options)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', True),
                         JMESPathCheck('contentTypesToCompress[0]', "application/json"),
                         JMESPathCheck('contentTypesToCompress[1]', "application/xml"),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        update_options = '--content-types-to-compress application/json application/xml'
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=update_options,
                                 checks=update_checks)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', False),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        update_options = '--enable-compression False'
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=update_options,
                                 checks=update_checks)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', True),
                         JMESPathCheck('contentTypesToCompress[0]', "text/javascript"),
                         JMESPathCheck('contentTypesToCompress[1]', "application/x-javascript"),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        update_options = '--enable-compression --content-types-to-compress text/javascript application/x-javascript'
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=update_options,
                                 checks=update_checks)

        self.endpoint_delete_cmd(resource_group, endpoint_name, profile_name)

    @record_only()  # This test relies on existing resources in a specific subscription
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_private_link(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name, sku='Standard_Microsoft')

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.contoso.com'
        pls_subscription_id = '27cafca8-b9a4-4264-b399-45d0c9cca1ab'
        # Workaround for overly heavy-handed subscription id replacement in playback mode.
        if self.is_playback_mode():
            pls_subscription_id = '00000000-0000-0000-0000-000000000000'
        private_link_id = f'/subscriptions/{pls_subscription_id}/resourceGroups/cdn-sdk-test/providers/Microsoft.Network/privateLinkServices/cdn-sdk-pls-test'
        private_link_location = 'EastUS'
        private_link_message = 'Please approve the request'
        checks = [JMESPathCheck('name', endpoint_name),
                  JMESPathCheck('origins[0].hostName', origin),
                  JMESPathCheck('origins[0].privateLinkResourceId', private_link_id),
                  JMESPathCheck('origins[0].privateLinkLocation', private_link_location, False),
                  JMESPathCheck('origins[0].privateLinkApprovalMessage', private_link_message)]
        self.endpoint_create_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 origin,
                                 private_link_id=private_link_id,
                                 private_link_location=private_link_location,
                                 private_link_message=private_link_message,
                                 checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', endpoint_name),
                       JMESPathCheck('@[0].origins[0].hostName', origin),
                       JMESPathCheck('@[0].origins[0].privateLinkResourceId', private_link_id),
                       JMESPathCheck('@[0].origins[0].privateLinkLocation', private_link_location, False),
                       JMESPathCheck('@[0].origins[0].privateLinkApprovalMessage', private_link_message)]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_endpoint_start_and_stop(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.contoso.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        checks = [JMESPathCheck('resourceState', 'Stopped')]
        self.endpoint_stop_cmd(resource_group, endpoint_name, profile_name)
        self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        checks = [JMESPathCheck('resourceState', 'Running')]
        self.endpoint_start_cmd(resource_group, endpoint_name, profile_name)
        self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

    @ResourceGroupPreparer()
    def test_rule_engine_crud(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku='Standard_Microsoft')
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.contoso.com'
        checks = [JMESPathCheck('name', endpoint_name),
                  JMESPathCheck('origins[0].hostName', origin),
                  JMESPathCheck('isHttpAllowed', True),
                  JMESPathCheck('isHttpsAllowed', True),
                  JMESPathCheck('isCompressionEnabled', False),
                  JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin, checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        rulename = 'r1'
        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', False),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString'),
                         JMESPathCheck('length(deliveryPolicy.rules)', 1),
                         JMESPathCheck('deliveryPolicy.rules[0].name', rulename)]
        self.endpoint_add_rule_cmd(resource_group,
                                   endpoint_name,
                                   profile_name,
                                   order=1,
                                   rule_name=rulename,
                                   checks=update_checks)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', False),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString'),
                         JMESPathCheck('length(deliveryPolicy.rules[0].conditions)', 2)]
        self.endpoint_add_condition_cmd(resource_group,
                                        endpoint_name,
                                        profile_name,
                                        checks=update_checks,
                                        options='--rule-name r1 --match-variable RemoteAddress\
                                                 --operator GeoMatch --match-values "TH" "US"')

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules[0].actions)', 2)]
        self.endpoint_add_action_cmd(resource_group,
                                     endpoint_name,
                                     profile_name,
                                     checks=update_checks,
                                     options='--rule-name r1 --action-name "UrlRewrite"\
                                              --source-pattern "/abc" --destination "/def"')

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules[0].conditions)', 1)]
        self.endpoint_remove_condition_cmd(resource_group,
                                           endpoint_name,
                                           profile_name,
                                           checks=update_checks,
                                           options='--rule-name r1 --index 0')

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules[0].actions)', 1)]
        self.endpoint_remove_action_cmd(resource_group,
                                        endpoint_name,
                                        profile_name,
                                        checks=update_checks,
                                        options='--rule-name r1 --index 0')

        rulename = 'r2'
        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', False),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString'),
                         JMESPathCheck('length(deliveryPolicy.rules)', 2),
                         JMESPathCheck('deliveryPolicy.rules[1].name', rulename)]
        self.endpoint_add_rule_cmd(resource_group,
                                   endpoint_name,
                                   profile_name,
                                   order=2,
                                   rule_name=rulename,
                                   checks=update_checks)

        rulename = 'r3'
        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('origins[0].hostName', origin),
                         JMESPathCheck('isHttpAllowed', True),
                         JMESPathCheck('isHttpsAllowed', True),
                         JMESPathCheck('isCompressionEnabled', False),
                         JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString'),
                         JMESPathCheck('length(deliveryPolicy.rules)', 3),
                         JMESPathCheck('deliveryPolicy.rules[2].name', rulename)]
        self.endpoint_add_rule_cmd(resource_group,
                                   endpoint_name,
                                   profile_name,
                                   order=3,
                                   rule_name=rulename,
                                   checks=update_checks)

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules)', 2)]
        self.endpoint_remove_rule_cmd(resource_group,
                                      endpoint_name,
                                      profile_name,
                                      checks=update_checks,
                                      options='--rule-name r1')

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules)', 1)]
        self.endpoint_remove_rule_cmd(resource_group,
                                      endpoint_name,
                                      profile_name,
                                      checks=update_checks,
                                      options='--rule-name r3')

        self.endpoint_delete_cmd(resource_group, endpoint_name, profile_name)
