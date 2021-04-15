# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
from azure.mgmt.cdn.models import (SkuName,
                                   CdnEndpoint,
                                   EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink,
                                   PolicyMode,
                                   ActionType)
from .scenario_mixin import CdnScenarioMixin
from base64 import b64encode
from knack.util import CLIError


class CdnWafPolicyScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_cdn_waf_policy_crud(self, resource_group):

        self.kwargs.update({
            'resource_group': resource_group,
            'policy': 'policy123',
            'custom_rule_1': 'customrule1',
            'custom_rule_2': 'customrule2',
            'rate_limit_rule_1': 'ratelimitrule1',
            'rate_limit_rule_2': 'ratelimitrule2',
            'rule_set_type': 'DefaultRuleSet',
            'rule_set_version': '1.0',
            'rule_group': 'SQLI',
            'redirect_url': 'https://example.com',
            'block_response_body': b64encode('<html><body>example body</body></html>'.encode('utf-8')).decode('utf-8'),
            'block_response_status_code': 429,
        })

        # Create, show, and list empty policy.
        checks = [JMESPathCheck('name', self.kwargs['policy']),
                  JMESPathCheck('sku.name', SkuName.standard_microsoft.value),
                  JMESPathCheck('customRules.rules', []),
                  JMESPathCheck('rateLimitRules.rules', []),
                  JMESPathCheck('managedRules.managedRuleSets', []),
                  JMESPathCheck('policySettings.enabledState', 'Enabled'),
                  JMESPathCheck('policySettings.defaultRedirectUrl', self.kwargs['redirect_url']),
                  JMESPathCheck('endpointLinks', []),
                  JMESPathCheck('tags.foo', 'bar')]
        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', self.kwargs['policy']),
                       JMESPathCheck('@[0].sku.name', SkuName.standard_microsoft.value),
                       JMESPathCheck('@[0].customRules.rules', []),
                       JMESPathCheck('@[0].rateLimitRules.rules', []),
                       JMESPathCheck('@[0].managedRules.managedRuleSets', []),
                       JMESPathCheck('@[0].policySettings.enabledState', 'Enabled'),
                       JMESPathCheck('@[0].endpointLinks', []),
                       JMESPathCheck('@[0].tags.foo', 'bar')]
        with self.assertRaises(SystemExit):  # exits with code 3 due to missing resource
            self.cmd('cdn waf policy show -g {resource_group} -n {policy}')
        self.cmd(
            'cdn waf policy set -g {resource_group} --name {policy} --redirect-url "{redirect_url}" --tags="foo=bar"', checks=checks)
        self.cmd('cdn waf policy show -g {resource_group} -n {policy}', checks=checks)
        self.cmd('cdn waf policy list -g {resource_group}', checks=list_checks)

        # Add, show, and list managed rule set.
        checks = [JMESPathCheck('ruleSetType', self.kwargs['rule_set_type']),
                  JMESPathCheck('ruleSetVersion', self.kwargs['rule_set_version']),
                  JMESPathCheck('managedRuleOverrides', None)]
        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0]ruleSetType', self.kwargs['rule_set_type']),
                       JMESPathCheck('@[0]ruleSetVersion', self.kwargs['rule_set_version']),
                       JMESPathCheck('@[0]managedRuleOverrides', None)]
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy managed-rule-set show -g {resource_group} --policy-name {policy} '
                     '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version}')
        self.cmd('cdn waf policy managed-rule-set add -g {resource_group} --policy-name {policy} '
                 '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version}',
                 checks=checks)
        self.cmd('cdn waf policy managed-rule-set show -g {resource_group} --policy-name {policy} '
                 '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version}',
                 checks=checks)

        # Set, show, and list rule group override.
        checks = [JMESPathCheck('ruleGroupName', self.kwargs['rule_group']),
                  JMESPathCheck('rules[0].ruleId', '942440'),
                  JMESPathCheck('rules[0].action', 'Redirect'),
                  JMESPathCheck('rules[0].enabledState', 'Enabled'),
                  JMESPathCheck('rules[1].ruleId', '942120'),
                  JMESPathCheck('rules[1].action', 'Block'),
                  JMESPathCheck('rules[1].enabledState', 'Disabled'),
                  JMESPathCheck('rules[2].ruleId', '942100'),
                  JMESPathCheck('rules[2].action', 'Block'),
                  JMESPathCheck('rules[2].enabledState', 'Disabled')]
        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].ruleGroupName', self.kwargs['rule_group']),
                       JMESPathCheck('@[0].rules[0].ruleId', '942440'),
                       JMESPathCheck('@[0].rules[0].action', 'Redirect'),
                       JMESPathCheck('@[0].rules[0].enabledState', 'Enabled'),
                       JMESPathCheck('@[0].rules[1].ruleId', '942120'),
                       JMESPathCheck('@[0].rules[1].action', 'Block'),
                       JMESPathCheck('@[0].rules[1].enabledState', 'Disabled'),
                       JMESPathCheck('@[0].rules[2].ruleId', '942100'),
                       JMESPathCheck('@[0].rules[2].action', 'Block'),
                       JMESPathCheck('@[0].rules[2].enabledState', 'Disabled')]
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy managed-rule-set rule-group-override show -g {resource_group} '
                     '--policy-name {policy} --rule-set-type {rule_set_type} '
                     '--rule-set-version {rule_set_version} -n {rule_group}')
        self.cmd('cdn waf policy managed-rule-set rule-group-override set -g {resource_group} --policy-name {policy} '
                 '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version} -n {rule_group} '
                 '-r id=942440 action=Redirect enabled=Enabled -r id=942120 -r id=942100')
        self.cmd('cdn waf policy managed-rule-set rule-group-override show -g {resource_group} '
                 '--policy-name {policy} --rule-set-type {rule_set_type} '
                 '--rule-set-version {rule_set_version} -n {rule_group}',
                 checks=checks)
        self.cmd('cdn waf policy managed-rule-set rule-group-override list -g {resource_group} '
                 '--policy-name {policy} --rule-set-type {rule_set_type} '
                 '--rule-set-version {rule_set_version}',
                 checks=list_checks)

        # Set, show, and list custom rules.
        checks = [JMESPathCheck('name', self.kwargs['custom_rule_1']),
                  JMESPathCheck('action', ActionType.block.value),
                  JMESPathCheck('priority', 100),
                  JMESPathCheck('length(matchConditions)', 1),
                  JMESPathCheck('matchConditions[0].matchVariable', 'RequestMethod'),
                  JMESPathCheck('matchConditions[0].operator', 'Equal'),
                  JMESPathCheck('matchConditions[0].negateCondition', True),
                  JMESPathCheck('length(matchConditions[0].matchValue)', 2),
                  JMESPathCheck('matchConditions[0].matchValue[0]', 'GET'),
                  JMESPathCheck('matchConditions[0].matchValue[1]', 'HEAD')]
        checks2 = [JMESPathCheck('name', self.kwargs['custom_rule_2']),
                   JMESPathCheck('action', ActionType.redirect.value),
                   JMESPathCheck('priority', 200),
                   JMESPathCheck('length(matchConditions)', 2),
                   JMESPathCheck('matchConditions[0].matchVariable', 'RequestUri'),
                   JMESPathCheck('matchConditions[0].operator', 'Contains'),
                   JMESPathCheck('matchConditions[0].negateCondition', False),
                   JMESPathCheck('length(matchConditions[0].matchValue)', 1),
                   JMESPathCheck('matchConditions[0].matchValue[0]', '..'),
                   JMESPathCheck('matchConditions[1].matchVariable', 'QueryString'),
                   JMESPathCheck('matchConditions[1].operator', 'Contains'),
                   JMESPathCheck('matchConditions[1].negateCondition', False),
                   JMESPathCheck('length(matchConditions[1].matchValue)', 1),
                   JMESPathCheck('matchConditions[1].matchValue[0]', ' ')]
        list_checks = [JMESPathCheck('@[0].name', self.kwargs['custom_rule_1']),
                       JMESPathCheck('@[0].action', ActionType.block.value),
                       JMESPathCheck('@[0].priority', 100),
                       JMESPathCheck('length(@[0].matchConditions)', 1),
                       JMESPathCheck('@[0].matchConditions[0].matchVariable', 'RequestMethod'),
                       JMESPathCheck('@[0].matchConditions[0].operator', 'Equal'),
                       JMESPathCheck('@[0].matchConditions[0].negateCondition', True),
                       JMESPathCheck('length(@[0].matchConditions[0].matchValue)', 2),
                       JMESPathCheck('@[0].matchConditions[0].matchValue[0]', 'GET'),
                       JMESPathCheck('@[0].matchConditions[0].matchValue[1]', 'HEAD'),
                       JMESPathCheck('@[1].name', self.kwargs['custom_rule_2']),
                       JMESPathCheck('@[1].action', ActionType.redirect.value),
                       JMESPathCheck('@[1].priority', 200),
                       JMESPathCheck('length(@[1].matchConditions)', 2),
                       JMESPathCheck('@[1].matchConditions[0].matchVariable', 'RequestUri'),
                       JMESPathCheck('@[1].matchConditions[0].operator', 'Contains'),
                       JMESPathCheck('@[1].matchConditions[0].negateCondition', False),
                       JMESPathCheck('length(@[1].matchConditions[0].matchValue)', 1),
                       JMESPathCheck('@[1].matchConditions[0].matchValue[0]', '..'),
                       JMESPathCheck('@[1].matchConditions[1].matchVariable', 'QueryString'),
                       JMESPathCheck('@[1].matchConditions[1].operator', 'Contains'),
                       JMESPathCheck('@[1].matchConditions[1].negateCondition', False),
                       JMESPathCheck('length(@[1].matchConditions[1].matchValue)', 1),
                       JMESPathCheck('@[1].matchConditions[1].matchValue[0]', ' ')]
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy custom-rule show -g {resource_group} --policy-name {policy} -n {custom_rule_1}')
        self.cmd('cdn waf policy custom-rule set -g {resource_group} --policy-name {policy} -n {custom_rule_1} '
                 '--action Block --priority 100 --match-condition '
                 'match-variable=RequestMethod operator=Equal negate=true match-value=GET match-value=HEAD',
                 checks=checks)
        self.cmd('cdn waf policy custom-rule show -g {resource_group} --policy-name {policy} -n {custom_rule_1}',
                 checks=checks)
        self.cmd('cdn waf policy custom-rule set -g {resource_group} --policy-name {policy} -n {custom_rule_2} '
                 '--action Redirect --priority 200 '
                 '-m match-variable=RequestUri operator=Contains match-value=.. '
                 '-m match-variable=QueryString operator=Contains "match-value= "',
                 checks=checks2)
        self.cmd('cdn waf policy custom-rule show -g {resource_group} --policy-name {policy} -n {custom_rule_2}',
                 checks=checks2)
        self.cmd('cdn waf policy custom-rule list -g {resource_group} --policy-name {policy}', checks=list_checks)

        # Set, show, and list rate limit rules.
        checks = [JMESPathCheck('name', self.kwargs['rate_limit_rule_1']),
                  JMESPathCheck('action', ActionType.block.value),
                  JMESPathCheck('priority', 100),
                  JMESPathCheck('rateLimitThreshold', 100),
                  JMESPathCheck('rateLimitDurationInMinutes', 1),
                  JMESPathCheck('length(matchConditions)', 1),
                  JMESPathCheck('matchConditions[0].matchVariable', 'RequestMethod'),
                  JMESPathCheck('matchConditions[0].operator', 'Equal'),
                  JMESPathCheck('matchConditions[0].negateCondition', True),
                  JMESPathCheck('length(matchConditions[0].matchValue)', 2),
                  JMESPathCheck('matchConditions[0].matchValue[0]', 'GET'),
                  JMESPathCheck('matchConditions[0].matchValue[1]', 'HEAD')]
        checks2 = [JMESPathCheck('name', self.kwargs['rate_limit_rule_2']),
                   JMESPathCheck('action', ActionType.redirect.value),
                   JMESPathCheck('priority', 200),
                   JMESPathCheck('rateLimitThreshold', 100),
                   JMESPathCheck('rateLimitDurationInMinutes', 5),
                   JMESPathCheck('length(matchConditions)', 2),
                   JMESPathCheck('matchConditions[0].matchVariable', 'RequestMethod'),
                   JMESPathCheck('matchConditions[0].operator', 'Equal'),
                   JMESPathCheck('matchConditions[0].negateCondition', False),
                   JMESPathCheck('length(matchConditions[0].matchValue)', 1),
                   JMESPathCheck('matchConditions[0].matchValue[0]', 'PUT'),
                   JMESPathCheck('matchConditions[1].matchVariable', 'RequestUri'),
                   JMESPathCheck('matchConditions[1].operator', 'Contains'),
                   JMESPathCheck('matchConditions[1].negateCondition', False),
                   JMESPathCheck('length(matchConditions[1].matchValue)', 1),
                   JMESPathCheck('matchConditions[1].matchValue[0]', '/expensive/resource/')]
        list_checks = [JMESPathCheck('@[0].name', self.kwargs['rate_limit_rule_1']),
                       JMESPathCheck('@[0].action', ActionType.block.value),
                       JMESPathCheck('@[0].priority', 100),
                       JMESPathCheck('@[0].rateLimitThreshold', 100),
                       JMESPathCheck('@[0].rateLimitDurationInMinutes', 1),
                       JMESPathCheck('length(@[0].matchConditions)', 1),
                       JMESPathCheck('@[0].matchConditions[0].matchVariable', 'RequestMethod'),
                       JMESPathCheck('@[0].matchConditions[0].operator', 'Equal'),
                       JMESPathCheck('@[0].matchConditions[0].negateCondition', True),
                       JMESPathCheck('length(@[0].matchConditions[0].matchValue)', 2),
                       JMESPathCheck('@[0].matchConditions[0].matchValue[0]', 'GET'),
                       JMESPathCheck('@[0].matchConditions[0].matchValue[1]', 'HEAD'),
                       JMESPathCheck('@[1].name', self.kwargs['rate_limit_rule_2']),
                       JMESPathCheck('@[1].action', ActionType.redirect.value),
                       JMESPathCheck('@[1].priority', 200),
                       JMESPathCheck('@[1].rateLimitThreshold', 100),
                       JMESPathCheck('@[1].rateLimitDurationInMinutes', 5),
                       JMESPathCheck('length(@[1].matchConditions)', 2),
                       JMESPathCheck('@[1].matchConditions[0].matchVariable', 'RequestMethod'),
                       JMESPathCheck('@[1].matchConditions[0].operator', 'Equal'),
                       JMESPathCheck('@[1].matchConditions[0].negateCondition', False),
                       JMESPathCheck('length(@[1].matchConditions[0].matchValue)', 1),
                       JMESPathCheck('@[1].matchConditions[0].matchValue[0]', 'PUT'),
                       JMESPathCheck('@[1].matchConditions[1].matchVariable', 'RequestUri'),
                       JMESPathCheck('@[1].matchConditions[1].operator', 'Contains'),
                       JMESPathCheck('@[1].matchConditions[1].negateCondition', False),
                       JMESPathCheck('length(@[1].matchConditions[1].matchValue)', 1),
                       JMESPathCheck('@[1].matchConditions[1].matchValue[0]', '/expensive/resource/')]
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy rate-limit-rule show -g {resource_group} --policy-name {policy} -n {rate_limit_rule_1}')
        self.cmd('cdn waf policy rate-limit-rule set -g {resource_group} --policy-name {policy} -n {rate_limit_rule_1} '
                 '--action Block --priority 100 --duration 1 --request-threshold 100 --match-condition '
                 'match-variable=RequestMethod operator=Equal negate=true match-value=GET match-value=HEAD',
                 checks=checks)
        self.cmd('cdn waf policy rate-limit-rule show -g {resource_group} --policy-name {policy} -n {rate_limit_rule_1}',
                 checks=checks)
        self.cmd('cdn waf policy rate-limit-rule set -g {resource_group} --policy-name {policy} -n {rate_limit_rule_2} '
                 '--action Redirect --priority 200 --duration 5 --request-threshold 100 '
                 '-m match-variable=RequestMethod operator=Equal match-value=PUT '
                 '-m match-variable=RequestUri operator=Contains match-value=/expensive/resource/',
                 checks=checks2)
        self.cmd('cdn waf policy rate-limit-rule show -g {resource_group} --policy-name {policy} -n {rate_limit_rule_2}',
                 checks=checks2)
        self.cmd('cdn waf policy rate-limit-rule list -g {resource_group} --policy-name {policy}',
                 checks=list_checks)

        # Update and show policy with custom, rate limit, and managed rules set.
        checks = [JMESPathCheck('name', self.kwargs['policy']),
                  JMESPathCheck('sku.name', SkuName.standard_microsoft.value),
                  JMESPathCheck('length(customRules.rules)', 2),
                  JMESPathCheck('length(rateLimitRules.rules)', 2),
                  JMESPathCheck('length(managedRules.managedRuleSets)', 1),
                  JMESPathCheck('policySettings.enabledState', 'Disabled'),
                  JMESPathCheck('policySettings.defaultRedirectUrl', self.kwargs['redirect_url']),
                  JMESPathCheck('policySettings.defaultCustomBlockResponseStatusCode',
                                self.kwargs['block_response_status_code']),
                  JMESPathCheck('policySettings.defaultCustomBlockResponseBody', self.kwargs['block_response_body']),
                  JMESPathCheck('policySettings.mode', PolicyMode.prevention.value),
                  JMESPathCheck('tags', {}),
                  JMESPathCheck('endpointLinks', [])]
        self.cmd('cdn waf policy set -g {resource_group} '
                 '--name {policy} '
                 '--sku Standard_Microsoft '
                 '--mode Prevention '
                 '--block-response-body {block_response_body} '
                 '--block-response-status-code {block_response_status_code} '
                 '--redirect-url {redirect_url} '
                 '--tags="" '
                 '--disabled',
                 checks=checks)
        self.cmd('cdn waf policy show -g {resource_group} -n {policy}', checks=checks)

        # Remove managed rule group override
        self.cmd('cdn waf policy managed-rule-set rule-group-override delete -y -g {resource_group} --policy-name {policy} '
                 '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version} -n {rule_group}')
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy managed-rule-set rule-group-override show -g {resource_group} '
                     '--policy-name {policy} --rule-set-type {rule_set_type} '
                     '--rule-set-version {rule_set_version} -n {rule_group}')

        # Remove managed rule set
        self.cmd('cdn waf policy managed-rule-set remove -y -g {resource_group} --policy-name {policy} '
                 '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version}')
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy managed-rule-set show -g {resource_group} --policy-name {policy} '
                     '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version}')

        # Remove custom rule
        self.cmd('cdn waf policy custom-rule delete -y -g {resource_group} --policy-name {policy} -n {custom_rule_1}')
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy custom-rule show -g {resource_group} --policy-name {policy} -n {custom_rule_1}')

        # Remove rate limit rule
        self.cmd('cdn waf policy rate-limit-rule delete -y -g {resource_group} --policy-name {policy} -n {rate_limit_rule_1}')
        with self.assertRaises(CLIError):
            self.cmd('cdn waf policy rate-limit-rule show -g {resource_group} --policy-name {policy} -n {rate_limit_rule_1}')

        # Delete policy
        self.cmd('cdn waf policy delete -y -g {resource_group} -n {policy}')


class CdnWafEndpointLinkScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cdn_domain')
    def test_cdn_waf_endpoint_link(self, resource_group):

        policy = 'wafpolicy1'
        profile = 'ps1'
        endpoint1 = self.create_random_name(prefix='ep1', length=13)
        endpoint2 = self.create_random_name(prefix='ep2', length=13)
        policy_id = self.policy_id(resource_group, policy)

        self.kwargs.update({
            'subscription_id': self.get_subscription_id(),
            'resource_group': resource_group,
            'profile': 'ps1',
            'endpoint1': endpoint1,
            'endpoint2': endpoint2,
            'policy': policy,
            'policy_id': policy_id,
        })

        self.cmd('cdn profile create -g {resource_group} -n {profile} --sku=Standard_Microsoft --location=westus')

        # Create WAF policy and linked endpoint.
        policy_checks = [JMESPathCheck('length(endpointLinks)', 0),
                         JMESPathCheck('id', policy_id, case_sensitive=False)]
        self.cmd('cdn waf policy set -g {resource_group} --name {policy}', checks=policy_checks)

        # Create the endpoint.
        endpoint_checks = [JMESPathCheck('webApplicationFirewallPolicyLink', None)]
        self.cmd('cdn endpoint create -g {resource_group} '
                 '--origin www.test.com '
                 '--profile-name {profile} '
                 '-n {endpoint1} ',
                 checks=endpoint_checks)
        with self.assertRaises(CLIError):
            self.cmd('cdn endpoint waf policy show -g {resource_group} --profile-name {profile} --endpoint-name {endpoint1}')

        # Link the endpoint.
        # link_checks = [JMESPathCheck('id', policy_id, case_sensitive=False)]
        endpoint_checks = [JMESPathCheck('webApplicationFirewallPolicyLink.id', policy_id, case_sensitive=False)]
        policy_checks = [JMESPathCheck('length(endpointLinks)', 1),
                         JMESPathCheck('endpointLinks[0].id', self.endpoint_id(resource_group, profile, endpoint1), case_sensitive=False)]
        self.cmd('cdn endpoint waf policy set -g {resource_group} --profile-name {profile} --endpoint-name {endpoint1} '
                 '--waf-policy-subscription-id {subscription_id} --waf-policy-resource-group-name {resource_group} '
                 '--waf-policy-name {policy}')
        # self.cmd('cdn endpoint waf policy show -g {resource_group} --profile-name {profile} --endpoint-name {endpoint1}',
        #          checks=link_checks)
        self.cmd('cdn endpoint show -g {resource_group} '
                 '--profile-name {profile} '
                 '-n {endpoint1}',)
        self.cmd('cdn waf policy show -g {resource_group} -n {policy}')

        # Create and link the second endpoint.
        policy_checks = [JMESPathCheck('length(endpointLinks)', 2),
                         JMESPathCheck('endpointLinks[0].id', self.endpoint_id(resource_group, profile, endpoint1), case_sensitive=False),
                         JMESPathCheck('endpointLinks[1].id', self.endpoint_id(resource_group, profile, endpoint2), case_sensitive=False)]
        self.cmd('cdn endpoint create -g {resource_group} '
                 '--origin www.test.com '
                 '--profile-name {profile} '
                 '-n {endpoint2}')
        self.cmd('cdn endpoint waf policy set -g {resource_group} '
                 '--profile-name {profile} '
                 '--endpoint-name {endpoint2} '
                 '--waf-policy-id {policy_id}')
        # self.cmd('cdn endpoint waf policy show -g {resource_group} --profile-name {profile} --endpoint-name {endpoint2}',
        #          checks=link_checks)
        self.cmd('cdn endpoint show -g {resource_group} '
                 '--profile-name {profile} '
                 '-n {endpoint2}',
                 )
        self.cmd('cdn waf policy show -g {resource_group} -n {policy}')

        # Remove both endpoint links
        policy_checks = [JMESPathCheck('length(endpointLinks)', 0)]
        endpoint_checks = [JMESPathCheck('webApplicationFirewallPolicyLink', None)]
        self.cmd('cdn endpoint waf policy remove -y -g {resource_group} '
                 '--profile-name {profile} '
                 '--endpoint-name {endpoint1}')
        with self.assertRaises(CLIError):
            self.cmd('cdn endpoint waf policy show -g {resource_group} --profile-name {profile} --endpoint-name {endpoint1}')
        self.cmd('cdn endpoint show -g {resource_group} '
                 '--profile-name {profile} '
                 '-n {endpoint1}',
                 checks=endpoint_checks)
        self.cmd('cdn endpoint waf policy remove -y -g {resource_group} '
                 '--profile-name {profile} '
                 '--endpoint-name {endpoint2}')
        with self.assertRaises(CLIError):
            self.cmd('cdn endpoint waf policy show -g {resource_group} --profile-name {profile} --endpoint-name {endpoint2}')
        self.cmd('cdn endpoint show -g {resource_group} '
                 '--profile-name {profile} '
                 '-n {endpoint2}',
                 checks=endpoint_checks)
        self.cmd('cdn waf policy show -g {resource_group} -n {policy}', checks=policy_checks)

    def endpoint_id(self, resource_group, profile, endpoint):
        return f'/subscriptions/{self.get_subscription_id()}' \
               f'/resourcegroups/{resource_group}' \
               f'/providers/Microsoft.Cdn' \
               f'/profiles/{profile}' \
               f'/endpoints/{endpoint}'

    def policy_id(self, resource_group, policy):
        return f'/subscriptions/{self.get_subscription_id()}' \
               f'/resourcegroups/{resource_group}' \
               f'/providers/Microsoft.Cdn' \
               f'/cdnwebapplicationfirewallpolicies/{policy}'


class CdnWafManagedRuleSetTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_cdn_waf_managed_rule_set_crud(self, resource_group):

        rule_set_type = 'DefaultRuleSet'
        rule_set_version = '1.0'

        self.kwargs.update({
            'resource_group': resource_group,
            'rule_set_type': rule_set_type,
            'rule_set_version': rule_set_version,
        })

        checks = [JMESPathCheck('@[0].name', 'DefaultRuleSet_1.0')]
        self.cmd('cdn waf policy managed-rule-set list-available', checks=checks)

        checks = [JMESPathCheck('@[0].ruleGroupName', 'PROTOCOL-ATTACK'),
                  JMESPathCheck('length(@[0].rules)', 7)]
        self.cmd('cdn waf policy managed-rule-set rule-group-override list-available '
                 '--rule-set-type {rule_set_type} --rule-set-version {rule_set_version}',
                 checks=checks)
