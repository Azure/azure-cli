# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnAfdRouteScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_route_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin_response_timeout_seconds = 100
        enabled_state = "Enabled"
        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     origin_response_timeout_seconds,
                                     enabled_state)

        origin_group_name = self.create_random_name(prefix='og', length=16)
        self.afd_origin_group_create_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         "--probe-request-type GET --probe-protocol Http --probe-interval-in-seconds 120 --probe-path /test1/azure.txt " +
                                         "--sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50")

        origin_group_id = f'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Cdn/profiles/{profile_name}/originGroups/{origin_group_name}'

        origin_name = self.create_random_name(prefix='origin', length=16)
        create_options = "--host-name huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--origin-host-header huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--priority 1 --weight 1000 --http-port 80 --https-port 443 --enabled-state Enabled"

        self.afd_origin_create_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name,
                                   create_options)

        route_name = self.create_random_name(prefix='route', length=16)
        create_options = f"--origin-group {origin_group_name} " \
                         + "--supported-protocols Https Http --link-to-default-domain Enabled " \
                         + "--https-redirect Enabled --forwarding-protocol MatchRequest"

        create_checks = [JMESPathCheck('supportedProtocols[0]', "Https"),
                         JMESPathCheck('supportedProtocols[1]', "Http"),
                         JMESPathCheck('linkToDefaultDomain', "Enabled"),
                         JMESPathCheck('forwardingProtocol', "MatchRequest"),
                         JMESPathCheck('httpsRedirect', "Enabled"),
                         JMESPathCheck('queryStringCachingBehavior', "NotSet"),
                         JMESPathCheck('compressionSettings.isCompressionEnabled', False),
                         JMESPathCheck('originGroup.id', origin_group_id)]
        self.afd_route_create_cmd(resource_group,
                                  profile_name,
                                  endpoint_name,
                                  route_name,
                                  create_options,
                                  create_checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', route_name)]
        self.afd_route_list_cmd(resource_group, profile_name, endpoint_name, checks=list_checks)

        update_checks = [JMESPathCheck('supportedProtocols[0]', "Https"),
                         JMESPathCheck('supportedProtocols[1]', "Http"),
                         JMESPathCheck('linkToDefaultDomain', "Enabled"),
                         JMESPathCheck('forwardingProtocol', "HttpsOnly"),
                         JMESPathCheck('httpsRedirect', "Enabled"),
                         JMESPathCheck('queryStringCachingBehavior', "IgnoreQueryString"),
                         JMESPathCheck('compressionSettings.isCompressionEnabled', True),
                         JMESPathCheck('length(compressionSettings.contentTypesToCompress)', 2),
                         JMESPathCheck('compressionSettings.contentTypesToCompress[0]', 'text/javascript'),
                         JMESPathCheck('compressionSettings.contentTypesToCompress[1]', 'text/plain'),
                         JMESPathCheck('originGroup.id', origin_group_id)]
        options = '--forwarding-protocol HttpsOnly --query-string-caching-behavior IgnoreQueryString --enable-compression True --content-types-to-compress text/javascript text/plain'
        self.afd_route_update_cmd(resource_group,
                                  profile_name,
                                  endpoint_name,
                                  route_name,
                                  options=options,
                                  checks=update_checks)

        update_checks = [JMESPathCheck('supportedProtocols[0]', "Https"),
                         JMESPathCheck('supportedProtocols[1]', "Http"),
                         JMESPathCheck('linkToDefaultDomain', "Enabled"),
                         JMESPathCheck('forwardingProtocol', "HttpsOnly"),
                         JMESPathCheck('httpsRedirect', "Enabled"),
                         JMESPathCheck('queryStringCachingBehavior', "UseQueryString"),
                         JMESPathCheck('compressionSettings.isCompressionEnabled', True),
                         JMESPathCheck('length(compressionSettings.contentTypesToCompress)', 1),
                         JMESPathCheck('compressionSettings.contentTypesToCompress[0]', 'text/css'),
                         JMESPathCheck('originGroup.id', origin_group_id)]
        options = '--query-string-caching-behavior UseQueryString --content-types-to-compress text/css'
        self.afd_route_update_cmd(resource_group,
                                  profile_name,
                                  endpoint_name,
                                  route_name,
                                  options=options,
                                  checks=update_checks)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)
        rule_set_id = f'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Cdn/profiles/{profile_name}/ruleSets/{rule_set_name}'

        update_checks = [JMESPathCheck('supportedProtocols[0]', "Https"),
                         JMESPathCheck('supportedProtocols[1]', "Http"),
                         JMESPathCheck('linkToDefaultDomain', "Enabled"),
                         JMESPathCheck('forwardingProtocol', "HttpsOnly"),
                         JMESPathCheck('httpsRedirect', "Enabled"),
                         JMESPathCheck('queryStringCachingBehavior', "UseQueryString"),
                         JMESPathCheck('compressionSettings.isCompressionEnabled', False),
                         JMESPathCheck('originGroup.id', origin_group_id),
                         JMESPathCheck('ruleSets[0].id', rule_set_id)]
        options = f'--rule-sets {rule_set_name} --enable-compression False'
        self.afd_route_update_cmd(resource_group,
                                  profile_name,
                                  endpoint_name,
                                  route_name,
                                  options=options,
                                  checks=update_checks)

        update_checks = [JMESPathCheck('supportedProtocols[0]', "Https"),
                         JMESPathCheck('supportedProtocols[1]', "Http"),
                         JMESPathCheck('linkToDefaultDomain', "Enabled"),
                         JMESPathCheck('forwardingProtocol', "HttpsOnly"),
                         JMESPathCheck('httpsRedirect', "Disabled"),
                         JMESPathCheck('compressionSettings.isCompressionEnabled', False),
                         JMESPathCheck('originGroup.id', origin_group_id),
                         JMESPathCheck('length(ruleSets)', 0),
                         JMESPathCheck('queryStringCachingBehavior', "UseQueryString")]
        options = '--rule-sets --https-redirect Disabled'
        self.afd_route_update_cmd(resource_group,
                                  profile_name,
                                  endpoint_name,
                                  route_name,
                                  options=options,
                                  checks=update_checks)

        self.afd_route_delete_cmd(resource_group, profile_name, endpoint_name, route_name)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_route_list_cmd(resource_group, profile_name, endpoint_name, list_checks)
