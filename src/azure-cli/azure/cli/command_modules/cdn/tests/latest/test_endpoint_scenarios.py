# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
from .scenario_mixin import CdnScenarioMixin

from azure.mgmt.cdn.models import SkuName


class CdnEndpointScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_endpoint_crud(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
        checks = [JMESPathCheck('name', endpoint_name),
                  JMESPathCheck('origins[0].hostName', origin),
                  JMESPathCheck('isHttpAllowed', True),
                  JMESPathCheck('isHttpsAllowed', True),
                  JMESPathCheck('isCompressionEnabled', False),
                  JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin, checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
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

    @ResourceGroupPreparer()
    def test_endpoint_start_and_stop(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        checks = [JMESPathCheck('resourceState', 'Stopped')]
        self.endpoint_stop_cmd(resource_group, endpoint_name, profile_name)
        self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        checks = [JMESPathCheck('resourceState', 'Running')]
        self.endpoint_start_cmd(resource_group, endpoint_name, profile_name)
        self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

    @ResourceGroupPreparer()
    def test_endpoint_load_and_purge(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name, options='--sku Standard_Verizon')

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        content_paths = ['/index.html', '/javascript/app.js']
        self.endpoint_load_cmd(resource_group, endpoint_name, profile_name, content_paths)

        content_paths = ['/index.html', '/javascript/*']
        self.endpoint_purge_cmd(resource_group, endpoint_name, profile_name, content_paths)

    @ResourceGroupPreparer()
    def test_endpoint_different_profiles(self, resource_group):
        origin = 'www.example.com'
        checks = [JMESPathCheck('origins[0].hostName', origin),
                  JMESPathCheck('isHttpAllowed', True),
                  JMESPathCheck('isHttpsAllowed', True),
                  JMESPathCheck('isCompressionEnabled', False),
                  JMESPathCheck('queryStringCachingBehavior', 'IgnoreQueryString')]

        # create an endpoint using the standard_akamai profile
        profile_name = self._create_profile(resource_group, SkuName.standard_akamai.value)
        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin, checks=checks + [JMESPathCheck('name', endpoint_name)])

        # create an endpoint using the standard_verizon profile
        profile_name = self._create_profile(resource_group, SkuName.standard_verizon.value)
        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin, checks=checks + [JMESPathCheck('name', endpoint_name)])

        # create an endpoint using the premium_verizon profile
        profile_name = self._create_profile(resource_group, SkuName.premium_verizon.value)
        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        premium_checks = checks.extend([JMESPathCheck('queryStringCachingBehavior', 'NotSet'), JMESPathCheck('name', endpoint_name)])
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin, checks=premium_checks)

    def _create_profile(self, resource_group, profile_sku):
        profile_name = (profile_sku + "_profile").replace("_", "-")  # profile names must match ^[a-zA-Z0-9]+(-*[a-zA-Z0-9])*$
        check = JMESPathCheck('sku.name', profile_sku)
        self.profile_create_cmd(resource_group, profile_name, sku=profile_sku, checks=check)
        return profile_name

    @ResourceGroupPreparer()
    def test_rule_engine_crud(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, options='--sku Standard_Microsoft')
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.endpoint_list_cmd(resource_group, profile_name, checks=list_checks)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin = 'www.example.com'
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

        update_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules)', 0)]
        self.endpoint_remove_rule_cmd(resource_group,
                                      endpoint_name,
                                      profile_name,
                                      checks=update_checks,
                                      options='--rule-name r1')

        self.endpoint_delete_cmd(resource_group, endpoint_name, profile_name)
