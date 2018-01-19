# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
from .scenario_mixin import CdnScenarioMixin


class CdnEndpointScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_endpoint_crud(self, resource_group):
        from knack.util import CLIError

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
