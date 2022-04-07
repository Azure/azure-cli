# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck, checkers
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin

from azure.cli.core.azclierror import (InvalidArgumentValueError)

from azure.mgmt.cdn.models import SkuName

from collections import namedtuple


class CdnAfdRuleScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_rule_set_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_rule_set_list_cmd(resource_group, profile_name, expect_failure=True)
        self.afd_profile_create_cmd(resource_group, profile_name)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_set_list_cmd(resource_group, profile_name, checks=list_checks)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.afd_rule_set_list_cmd(resource_group, profile_name, checks=list_checks)

        show_checks = [JMESPathCheck('name', rule_set_name),
                       JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_rule_set_show_cmd(resource_group, rule_set_name, profile_name, checks=show_checks)

        self.afd_rule_set_delete_cmd(resource_group, rule_set_name, profile_name)

        self.afd_rule_set_show_cmd(resource_group, rule_set_name, profile_name, expect_failure=True)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_set_list_cmd(resource_group, profile_name, checks=list_checks)

    @ResourceGroupPreparer()
    def test_afd_rule_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        rule_name = 'r1'
        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('matchProcessingBehavior', "Stop"),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RemoteAddress"),
                       JMESPathCheck('conditions[0].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "RouteConfigurationOverride"),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.queryStringCachingBehavior', 'UseQueryString'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.cacheBehavior', 'HonorOrigin'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.isCompressionEnabled', 'Disabled'),
                       JMESPathCheck('actions[0].parameters.originGroupOverride', None)]

        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options='--match-processing-behavior Stop --match-variable RemoteAddress --operator GeoMatch --match-values "TH" --action-name RouteConfigurationOverride --enable-caching True --enable-compression False --query-string-caching-behavior UseQueryString --cache-behavior HonorOrigin --order 1')

        self.afd_rule_show_cmd(resource_group,
                               rule_set_name,
                               rule_name,
                               profile_name,
                               checks=rule_checks)

        rule_name1 = 'r2'
        rule_checks = [JMESPathCheck('order', 2),
                       JMESPathCheck('name', rule_name1),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RequestScheme"),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'HTTP'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "UrlRedirect"),
                       JMESPathCheck('actions[0].parameters.redirectType', "Moved"),
                       JMESPathCheck('actions[0].parameters.destinationProtocol', 'Https')]
        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name1,
                              profile_name,
                              options='--match-variable RequestScheme --match-values "HTTP" --action-name UrlRedirect --redirect-protocol Https --redirect-type Moved --order 2')

        self.afd_rule_show_cmd(resource_group,
                               rule_set_name,
                               rule_name1,
                               profile_name,
                               checks=rule_checks)

        rule_list_checks = [JMESPathCheck('length(@)', 2)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        self.afd_rule_delete_cmd(resource_group, rule_set_name, rule_name1, profile_name)
        rule_list_checks = [JMESPathCheck('length(@)', 1)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 2),
                       JMESPathCheck('conditions[1].name', "RemoteAddress"),
                       JMESPathCheck('conditions[1].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[1].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('conditions[1].parameters.matchValues[1]', 'US'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "RouteConfigurationOverride"),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.queryStringCachingBehavior', 'UseQueryString'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.cacheBehavior', 'HonorOrigin'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.isCompressionEnabled', 'Disabled'),
                       JMESPathCheck('actions[0].parameters.originGroupOverride', None)]
        self.afd_rule_add_condition_cmd(resource_group,
                                        rule_set_name,
                                        rule_name,
                                        profile_name,
                                        options='--match-variable RemoteAddress '
                                                '--operator GeoMatch --match-values "TH" "US"')

        self.afd_rule_show_cmd(resource_group,
                               rule_set_name,
                               rule_name,
                               profile_name,
                               checks=rule_checks)

        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 2),
                       JMESPathCheck('conditions[1].name', "RemoteAddress"),
                       JMESPathCheck('conditions[1].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[1].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('conditions[1].parameters.matchValues[1]', 'US'),
                       JMESPathCheck('length(actions)', 2),
                       JMESPathCheck('actions[0].name', "RouteConfigurationOverride"),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.queryStringCachingBehavior', 'UseQueryString'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.cacheBehavior', 'HonorOrigin'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.isCompressionEnabled', 'Disabled'),
                       JMESPathCheck('actions[0].parameters.originGroupOverride', None),
                       JMESPathCheck('actions[1].name', "UrlRewrite"),
                       JMESPathCheck('actions[1].parameters.sourcePattern', '/abc'),
                       JMESPathCheck('actions[1].parameters.destination', '/def')]
        self.afd_rule_add_action_cmd(resource_group,
                                     rule_set_name,
                                     rule_name,
                                     profile_name,
                                     options='--action-name "UrlRewrite" '
                                             '--source-pattern "/abc" --destination "/def"')

        self.afd_rule_show_cmd(resource_group,
                               rule_set_name,
                               rule_name,
                               profile_name,
                               checks=rule_checks)

        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RemoteAddress"),
                       JMESPathCheck('conditions[0].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('conditions[0].parameters.matchValues[1]', 'US'),
                       JMESPathCheck('length(actions)', 2),
                       JMESPathCheck('actions[0].name', "RouteConfigurationOverride"),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.queryStringCachingBehavior', 'UseQueryString'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.cacheBehavior', 'HonorOrigin'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.isCompressionEnabled', 'Disabled'),
                       JMESPathCheck('actions[0].parameters.originGroupOverride', None),
                       JMESPathCheck('actions[1].name', "UrlRewrite"),
                       JMESPathCheck('actions[1].parameters.sourcePattern', '/abc'),
                       JMESPathCheck('actions[1].parameters.destination', '/def')]
        self.afd_rule_remove_condition_cmd(resource_group,
                                           rule_set_name,
                                           rule_name,
                                           profile_name,
                                           0)

        self.afd_rule_show_cmd(resource_group,
                               rule_set_name,
                               rule_name,
                               profile_name,
                               checks=rule_checks)

        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RemoteAddress"),
                       JMESPathCheck('conditions[0].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('conditions[0].parameters.matchValues[1]', 'US'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "UrlRewrite"),
                       JMESPathCheck('actions[0].parameters.sourcePattern', '/abc'),
                       JMESPathCheck('actions[0].parameters.destination', '/def')]
        self.afd_rule_remove_action_cmd(resource_group,
                                        rule_set_name,
                                        rule_name,
                                        profile_name,
                                        0)        

        origin_group_name = self.create_random_name(prefix='og', length=16)
        origin_group_id = f'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Cdn/profiles/{profile_name}/originGroups/{origin_group_name}'
        self.afd_origin_group_create_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         "--probe-request-type GET --probe-protocol Http --probe-interval-in-seconds 120 --probe-path /test1/azure.txt " +
                                         "--sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50")

        origin_name1 = self.create_random_name(prefix='origin', length=16)
        create_options = "--host-name huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--origin-host-header huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--priority 1 --weight 666 --http-port 8080 --https-port 443 --enabled-state Enabled"

        self.afd_origin_create_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name1,
                                   create_options)

        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RemoteAddress"),
                       JMESPathCheck('conditions[0].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('conditions[0].parameters.matchValues[1]', 'US'),
                       JMESPathCheck('length(actions)', 2),
                       JMESPathCheck('actions[1].name', "RouteConfigurationOverride"),
                       JMESPathCheck('actions[1].parameters.cacheConfiguration.queryStringCachingBehavior', 'IncludeSpecifiedQueryStrings'),
                       JMESPathCheck('actions[1].parameters.cacheConfiguration.cacheBehavior', 'OverrideAlways'),
                       JMESPathCheck('actions[1].parameters.cacheConfiguration.cacheDuration', '1.00:00:00'),
                       JMESPathCheck('actions[1].parameters.cacheConfiguration.isCompressionEnabled', 'Enabled'),
                       JMESPathCheck('actions[1].parameters.originGroupOverride.originGroup.id', origin_group_id, False),
                       JMESPathCheck('actions[1].parameters.originGroupOverride.forwardingProtocol', "MatchRequest"),
                       JMESPathCheck('actions[0].name', "UrlRewrite"),
                       JMESPathCheck('actions[0].parameters.sourcePattern', '/abc'),
                       JMESPathCheck('actions[0].parameters.destination', '/def')]
        self.afd_rule_add_action_cmd(resource_group,
                                     rule_set_name,
                                     rule_name,
                                     profile_name,
                                     options='--action-name "RouteConfigurationOverride" '
                                             f'--origin-group {origin_group_name} --forwarding-protocol MatchRequest '
                                             '--enable-compression True --enable-caching True '
                                             '--cache-behavior OverrideAlways --cache-duration 1.00:00:00 '
                                             '--query-string-caching-behavior IncludeSpecifiedQueryStrings '
                                             '--query-parameters x y z')

        self.afd_rule_show_cmd(resource_group,
                               rule_set_name,
                               rule_name,
                               profile_name,
                               checks=rule_checks)

        self.afd_rule_delete_cmd(resource_group,
                                 rule_set_name,
                                 rule_name,
                                 profile_name)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        self.afd_rule_set_delete_cmd(resource_group, rule_set_name, profile_name)

    @ResourceGroupPreparer()
    def test_afd_rule_complex_condition_creation(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        Condition = namedtuple('Condition', 'MatchVariable Operator MatchValues IsNegative Transforms Selector')
        conditions = [Condition("RemoteAddress", "GeoMatch", ["TH", "CN"], True, [], None),
                      Condition("RequestMethod", "Equal", ["HEAD"], False, [], None),
                      Condition("QueryString", "Contains", ["abc"], False, ["Lowercase", "UrlDecode"], None),
                      Condition("PostArgs", "RegEx", ["abc[0-9]+"], False, ["Lowercase"], "Arg1"),
                      Condition("RequestUri", "Equal", ["/test1/submit"], False, ["Lowercase", "UrlDecode"], None),
                      Condition("RequestHeader", "BeginsWith", ["head1", "header2"], False, ["Lowercase", "UrlDecode"], "Header1"),
                      Condition("RequestBody", "Contains", ["b1", "b2"], False, ["Lowercase", "UrlDecode"], None),
                      #Condition("RequestScheme", "Equal", ["HTTPS"], False, [], None),
                      Condition("UrlPath", "Contains", ["url1"], True, ["Lowercase"], None),
                      Condition("UrlFileExtension", "Equal", ["exe", "apk", "msi"], True, ["Lowercase"], None),
                      Condition("UrlFileName", "RegEx", ["[a-z1-9]+"], True, ["Lowercase"], None),
                      Condition("HttpVersion", "Equal", ["1.0", "1.1"], True, None, None),
                      Condition("Cookies", "Equal", ["exe", "apk", "msi"], True, ["Lowercase"], "cookie1"),
                      Condition("IsDevice", "Equal", ["Mobile"], False, [], None),
                      Condition("SocketAddr", "IPMatch", ["127.0.0.1"], True, [], None),
                      Condition("ClientPort", "Equal", ["8000"], True, [], None),
                      Condition("ServerPort", "Equal", ["80", "443"], False, [], None),
                      Condition("HostName", "Equal", ["www.contoso.com"], False, ["Lowercase"], None),
                      Condition("SslProtocol", "Equal", ["TLSv1", "TLSv1.1"], True, [], None)]

        for idx, condition in enumerate(conditions):           
            rule_name = self.create_random_name(prefix='rule', length=16)
            rule_checks = [JMESPathCheck('order', idx),
                        JMESPathCheck('name', rule_name),
                        JMESPathCheck('length(conditions)', 1),
                        JMESPathCheck(f'conditions[0].name', condition.MatchVariable),
                        JMESPathCheck(f'conditions[0].parameters.operator', condition.Operator),
                        JMESPathCheck(f'conditions[0].parameters.negateCondition', condition.IsNegative),                        
                        JMESPathCheck('length(actions)', 1),
                        JMESPathCheck('actions[0].name', "RouteConfigurationOverride"),
                        JMESPathCheck('actions[0].parameters.cacheConfiguration.queryStringCachingBehavior', 'UseQueryString'),
                        JMESPathCheck('actions[0].parameters.cacheConfiguration.cacheBehavior', 'HonorOrigin'),
                        JMESPathCheck('actions[0].parameters.cacheConfiguration.isCompressionEnabled', 'Disabled'),
                        JMESPathCheck('actions[0].parameters.originGroupOverride', None)]
            
            if condition.MatchValues is not None:
                for ii, matchValue in enumerate(condition.MatchValues):
                    rule_checks.append(JMESPathCheck(f'conditions[0].parameters.matchValues[{ii}]', matchValue))

            if condition.Transforms is not None:
                for ii, transform in enumerate(condition.Transforms):
                    rule_checks.append(JMESPathCheck(f'conditions[0].parameters.transforms[{ii}]', transform))

            matchValues = ' '.join(condition.MatchValues)
            options = f'--match-variable {condition.MatchVariable} --operator {condition.Operator} --negate-condition {condition.IsNegative} --match-values {matchValues} --action-name RouteConfigurationOverride --enable-caching True --enable-compression False --query-string-caching-behavior UseQueryString --cache-behavior HonorOrigin --order {idx}'
            
            if condition.Transforms is not None and len(condition.Transforms) > 0:
                options += " --transforms " + ' '.join(condition.Transforms)

            if condition.Selector is not None:
                options += f" --selector {condition.Selector}"

            self.afd_rule_add_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                options=options)

            self.afd_rule_show_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                checks=rule_checks)

        rule_list_checks = [JMESPathCheck('length(@)', len(conditions))]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        self.afd_rule_set_delete_cmd(resource_group, rule_set_name, profile_name)

    @ResourceGroupPreparer()
    def test_afd_rule_creation_invalid_operator(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        Condition = namedtuple('Condition', 'MatchVariable Operator MatchValues IsNegative Transforms Selector')
        conditions = [Condition("RemoteAddress", "GeoMatch1", ["TH", "CN"], True, [], None),
                      Condition("RequestMethod", "Equal1", ["HEAD"], False, [], None),
                      Condition("QueryString", "Contains1", ["abc"], False, ["Lowercase", "UrlDecode"], None),
                      Condition("PostArgs", "RegEx1", ["abc[0-9]+"], False, ["Lowercase"], "Arg1"),
                      Condition("RequestUri", "Equal1", ["/test1/submit"], False, ["Lowercase", "UrlDecode"], None),
                      Condition("RequestHeader", "BeginsWith1", ["head1", "header2"], False, ["Lowercase", "UrlDecode"], "Header1"),
                      Condition("RequestBody", "Contains1", ["b1", "b2"], False, ["Lowercase", "UrlDecode"], None),
                      Condition("RequestScheme", "Equal1", ["HTTPS"], False, [], None),
                      Condition("UrlPath", "Contains1", ["url1"], True, ["Lowercase"], None),
                      Condition("UrlFileExtension", "Equal1", ["exe", "apk", "msi"], True, ["Lowercase"], None),
                      Condition("UrlFileName", "RegEx1", ["[a-z1-9]+"], True, ["Lowercase"], None),
                      Condition("HttpVersion", "Equal1", ["1.0", "1.1"], True, None, None),
                      Condition("Cookies", "Equal1", ["exe", "apk", "msi"], True, ["Lowercase"], "cookie1"),
                      Condition("IsDevice", "Equal1", ["Mobile"], False, [], None),
                      Condition("SocketAddr", "IPMatch1", ["127.0.0.1"], True, [], None),
                      Condition("ClientPort", "Equal1", ["8000"], True, [], None),
                      Condition("ServerPort", "Equal1", ["80", "443"], False, [], None),
                      Condition("HostName", "Equal1", ["www.contoso.com"], False, ["Lowercase"], None),
                      Condition("SslProtocol", "Equal1", ["TLSv1", "TLSv1.1"], True, [], None)]

        for idx, condition in enumerate(conditions):           
            rule_name = self.create_random_name(prefix='rule', length=16)

            matchValues = ' '.join(condition.MatchValues)
            options = f'--match-variable {condition.MatchVariable} --operator {condition.Operator} --negate-condition {condition.IsNegative} --match-values {matchValues} --action-name RouteConfigurationOverride --enable-caching True --enable-compression False --query-string-caching-behavior UseQueryString --cache-behavior HonorOrigin --order {idx}'
            
            if condition.Transforms is not None and len(condition.Transforms) > 0:
                options += " --transforms " + ' '.join(condition.Transforms)

            if condition.Selector is not None:
                options += f" --selector {condition.Selector}"

            with self.assertRaises(InvalidArgumentValueError):
                self.afd_rule_add_cmd(resource_group,
                                    rule_set_name,
                                    rule_name,
                                    profile_name,
                                    options=options)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        self.afd_rule_set_delete_cmd(resource_group, rule_set_name, profile_name)

    @ResourceGroupPreparer()
    def test_afd_rule_creation_invalid_match_values(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        Condition = namedtuple('Condition', 'MatchVariable Operator MatchValues IsNegative Transforms Selector')
        conditions = [#Condition("HttpVersion", "Equal", ["1.8", "1.1"], True, None, None),
                      Condition("RequestMethod", "Equal", ["HEAD1"], False, [], None),
                      Condition("RequestScheme", "Equal", ["HTTPS1"], False, [], None),
                      Condition("IsDevice", "Equal", ["Mobile1"], False, [], None),
                      Condition("SslProtocol", "Equal", ["TLSv11", "TLSv1.1"], True, [], None)]

        for idx, condition in enumerate(conditions):           
            rule_name = self.create_random_name(prefix='rule', length=16)

            matchValues = ' '.join(condition.MatchValues)
            options = f'--match-variable {condition.MatchVariable} --operator {condition.Operator} --negate-condition {condition.IsNegative} --match-values {matchValues} --action-name RouteConfigurationOverride --enable-caching True --enable-compression False --query-string-caching-behavior UseQueryString --cache-behavior HonorOrigin --order {idx}'
            
            if condition.Transforms is not None and len(condition.Transforms) > 0:
                options += " --transforms " + ' '.join(condition.Transforms)

            if condition.Selector is not None:
                options += f" --selector {condition.Selector}"

            with self.assertRaises(InvalidArgumentValueError):
                self.afd_rule_add_cmd(resource_group,
                                    rule_set_name,
                                    rule_name,
                                    profile_name,
                                    options=options)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        self.afd_rule_set_delete_cmd(resource_group, rule_set_name, profile_name)

    @ResourceGroupPreparer()
    def test_afd_rule_actions(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        rule_set_name = self.create_random_name(prefix='ruleset', length=16)
        self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)

        rule_list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_rule_list_cmd(resource_group, rule_set_name, profile_name, checks=rule_list_checks)

        rule_name = 'r1'
        origin_group_name = self.create_random_name(prefix='og', length=16)
        origin_group_id = f'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Cdn/profiles/{profile_name}/originGroups/{origin_group_name}'
        self.afd_origin_group_create_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         "--probe-request-type GET --probe-protocol Http --probe-interval-in-seconds 120 --probe-path /test1/azure.txt " +
                                         "--sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50")

        origin_name1 = self.create_random_name(prefix='origin', length=16)
        create_options = "--host-name huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--origin-host-header huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--priority 1 --weight 666 --http-port 8080 --https-port 443 --enabled-state Enabled"

        self.afd_origin_create_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name1,
                                   create_options)

        # RouteConfigurationOverride
        rule_checks = [JMESPathCheck('order', 1),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('matchProcessingBehavior', "Stop"),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RemoteAddress"),
                       JMESPathCheck('conditions[0].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('conditions[0].parameters.matchValues[1]', 'US'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "RouteConfigurationOverride"),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.queryStringCachingBehavior', 'UseQueryString'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.cacheBehavior', 'HonorOrigin'),
                       JMESPathCheck('actions[0].parameters.cacheConfiguration.isCompressionEnabled', 'Disabled'),
                       JMESPathCheck('actions[0].parameters.originGroupOverride.originGroup.id', origin_group_id, False),
                       JMESPathCheck('actions[0].parameters.originGroupOverride.forwardingProtocol', "MatchRequest")]
        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options=f'--match-processing-behavior Stop --match-variable RemoteAddress --operator GeoMatch --match-values "TH" "US" '
                                      f'--action-name RouteConfigurationOverride --enable-caching True --enable-compression False --query-string-caching-behavior UseQueryString '
                                      f'--cache-behavior HonorOrigin --order 1 --origin-group {origin_group_name} --forwarding-protocol MatchRequest')
        self.afd_rule_show_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                checks=rule_checks)

        # URL Redirect
        rule_name = 'r2'
        rule_checks = [JMESPathCheck('order', 2),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "UrlFileExtension"),
                       JMESPathCheck('conditions[0].parameters.operator', 'Contains'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'exe'),
                       JMESPathCheck('conditions[0].parameters.matchValues[1]', 'apk'),
                       JMESPathCheck('matchProcessingBehavior', "Continue"),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "UrlRedirect"),
                       JMESPathCheck('actions[0].parameters.redirectType', "Moved"),
                       JMESPathCheck('actions[0].parameters.destinationProtocol', 'Https'),
                       JMESPathCheck('actions[0].parameters.customHostname', "www.contoso.com"),
                       JMESPathCheck('actions[0].parameters.customPath', '/path1'),
                       JMESPathCheck('actions[0].parameters.customQueryString', "a=b"),
                       JMESPathCheck('actions[0].parameters.customFragment', 'fg1')]
        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options='--match-variable UrlFileExtension --operator Contains --match-values exe apk '
                                      '--action-name UrlRedirect --redirect-protocol Https --redirect-type Moved --order 2 '
                                      '--custom-host "www.contoso.com" --custom-path "/path1" --custom-querystring "a=b" --custom-fragment fg1')
        self.afd_rule_show_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                checks=rule_checks)
        
        # URL Rewrite
        rule_name = 'r3'
        rule_checks = [JMESPathCheck('order', 3),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('matchProcessingBehavior', "Continue"),
                       JMESPathCheck('conditions[0].name', "RequestScheme"),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'HTTP'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "UrlRewrite"),
                       JMESPathCheck('actions[0].parameters.sourcePattern', "/abc"),
                       JMESPathCheck('actions[0].parameters.destination', '/def'),
                       JMESPathCheck('actions[0].parameters.preserveUnmatchedPath', True)]
        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options='--order 3 --match-variable RequestScheme --match-values "HTTP" '
                                      '--action-name UrlRewrite --source-pattern "/abc" --destination "/def" --preserve-unmatched-path true')
        self.afd_rule_show_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                checks=rule_checks)
        
        # ModifyRequestHeader
        rule_name = 'r4'
        rule_checks = [JMESPathCheck('order', 4),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('matchProcessingBehavior', "Continue"),
                       JMESPathCheck('conditions[0].name', "ServerPort"),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 443),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "ModifyRequestHeader"),
                       JMESPathCheck('actions[0].parameters.headerAction', "Append"),
                       JMESPathCheck('actions[0].parameters.headerName', 'header1'),
                       JMESPathCheck('actions[0].parameters.value', 'value1')]
        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options='--order 4 --match-variable ServerPort --operator Equal --match-values 443 '
                                      '--action-name ModifyRequestHeader --header-action Append --header-name header1 --header-value value1')
        self.afd_rule_show_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                checks=rule_checks)

        # ModifyResponseHeader
        rule_name = 'r5'
        rule_checks = [JMESPathCheck('order', 5),
                       JMESPathCheck('name', rule_name),
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('matchProcessingBehavior', "Continue"),
                       JMESPathCheck('conditions[0].name', "ClientPort"),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 8888),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "ModifyResponseHeader"),
                       JMESPathCheck('actions[0].parameters.headerAction', "Overwrite"),
                       JMESPathCheck('actions[0].parameters.headerName', 'header1'),
                       JMESPathCheck('actions[0].parameters.value', 'value1')]
        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options='--order 5 --match-variable ClientPort --operator Equal --match-values 8888 '
                                      '--action-name ModifyResponseHeader --header-action Overwrite --header-name header1 --header-value value1')
        self.afd_rule_show_cmd(resource_group,
                                rule_set_name,
                                rule_name,
                                profile_name,
                                checks=rule_checks)
       
        for rule_name in ["r1", "r2", "r3", "r4", "r5"]:
            self.afd_rule_delete_cmd(resource_group, rule_set_name, rule_name, profile_name)

        self.afd_rule_set_delete_cmd(resource_group, rule_set_name, profile_name)