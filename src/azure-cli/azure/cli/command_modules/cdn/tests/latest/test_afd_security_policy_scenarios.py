# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnAfdSecurityPolicyScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_security_policy_crud(self, resource_group):
        profile_name = 'profilesecuritytest'
        self.afd_security_policy_list_cmd(resource_group, profile_name, expect_failure=True)

        # List get empty
        self.afd_profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_security_policy_list_cmd(resource_group, profile_name, checks=list_checks)

        # Create an endpoint
        endpoint1_name = self.create_random_name(prefix='endpoint1', length=24)
        endpoint2_name = self.create_random_name(prefix='endpoint2', length=24)
        origin_response_timeout_seconds = 100
        enabled_state = "Enabled"
        endpoint_checks = [JMESPathCheck('originResponseTimeoutSeconds', 100),
                           JMESPathCheck('enabledState', 'Enabled')]
        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint1_name,
                                     origin_response_timeout_seconds,
                                     enabled_state,
                                     checks=endpoint_checks)

        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint2_name,
                                     origin_response_timeout_seconds,
                                     enabled_state,
                                     checks=endpoint_checks)

        # Create a security policy
        security_policy_name = self.create_random_name(prefix='security', length=24)
        domain_ids = []
        domain_ids.append(f'/subscriptions/{self.get_subscription_id()}/resourcegroups/{resource_group}/providers/Microsoft.Cdn/profiles/{profile_name}/afdEndpoints/{endpoint1_name}')
        domain_ids.append(f'/subscriptions/{self.get_subscription_id()}/resourcegroups/{resource_group}/providers/Microsoft.Cdn/profiles/{profile_name}/afdEndpoints/{endpoint2_name}')
        waf_policy_id = f'/subscriptions/{self.get_subscription_id()}/resourcegroups/CliDevReservedGroup/providers/Microsoft.Network/frontdoorwebapplicationfirewallpolicies/SampleStandard'

        checks = [JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_security_policy_create_cmd(resource_group,
                                            profile_name,
                                            security_policy_name,
                                            domain_ids,
                                            waf_policy_id,
                                            checks=checks)

        show_checks = [JMESPathCheck('name', security_policy_name),
                       JMESPathCheck('parameters.wafPolicy.id', waf_policy_id),
                       JMESPathCheck('length(parameters.associations[0].domains)', 2),
                       JMESPathCheck('parameters.associations[0].domains[0].id', domain_ids[0]),
                       JMESPathCheck('parameters.associations[0].domains[1].id', domain_ids[1]),
                       JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_security_policy_show_cmd(resource_group, profile_name, security_policy_name, checks=show_checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', security_policy_name),
                       JMESPathCheck('@[0].provisioningState', 'Succeeded')]
        self.afd_security_policy_list_cmd(resource_group, profile_name, checks=list_checks)

        # Update the security policy
        update_checks = [JMESPathCheck('name', security_policy_name),
                         JMESPathCheck('parameters.wafPolicy.id', waf_policy_id),
                         JMESPathCheck('length(parameters.associations[0].domains)', 1),
                         JMESPathCheck('parameters.associations[0].domains[0].id', domain_ids[1]),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_security_policy_update_cmd(resource_group,
                                            profile_name,
                                            security_policy_name,
                                            [domain_ids[1]],
                                            waf_policy_id,
                                            checks=update_checks)

        # Delete the security policy
        self.afd_security_policy_delete_cmd(resource_group, profile_name, security_policy_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_security_policy_list_cmd(resource_group, profile_name, checks=list_checks)
