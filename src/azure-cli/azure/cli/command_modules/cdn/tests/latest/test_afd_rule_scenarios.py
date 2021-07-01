# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin

from azure.mgmt.cdn.models import SkuName


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
                       JMESPathCheck('length(conditions)', 1),
                       JMESPathCheck('conditions[0].name', "RemoteAddress"),
                       JMESPathCheck('conditions[0].parameters.operator', 'GeoMatch'),
                       JMESPathCheck('conditions[0].parameters.matchValues[0]', 'TH'),
                       JMESPathCheck('length(actions)', 1),
                       JMESPathCheck('actions[0].name', "CacheExpiration"),
                       JMESPathCheck('actions[0].parameters.cacheBehavior', 'BypassCache')]

        self.afd_rule_add_cmd(resource_group,
                              rule_set_name,
                              rule_name,
                              profile_name,
                              options='--match-variable RemoteAddress --operator GeoMatch --match-values "TH" --action-name CacheExpiration --cache-behavior BypassCache --order 1')

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
                       JMESPathCheck('actions[0].name', "CacheExpiration"),
                       JMESPathCheck('actions[0].parameters.cacheBehavior', 'BypassCache')]
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
                       JMESPathCheck('actions[0].name', "CacheExpiration"),
                       JMESPathCheck('actions[0].parameters.cacheBehavior', 'BypassCache'),
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
                       JMESPathCheck('actions[0].name', "CacheExpiration"),
                       JMESPathCheck('actions[0].parameters.cacheBehavior', 'BypassCache'),
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
