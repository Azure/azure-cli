# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    live_only)
from .constants import SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, DEFAULT_LOCATION


class PostgreSQLFlexibleServerPublicAccessMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @live_only()
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt(resource_group)

    def _test_flexible_server_public_access_mgmt(self, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = DEFAULT_LOCATION

        # flexible-servers
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) for _ in range(5)]

        # Case 1 : Provision a server with public access all
        result = self.cmd('postgres flexible-server create -g {} -n {} --public-access {} -l {}'
                          .format(resource_group, servers[0], 'all', location)).get_output_in_json()

        self.cmd('postgres flexible-server firewall-rule show -g {} -n {} -r {}'
                 .format(resource_group, servers[0], result["firewallName"]),
                 checks=[JMESPathCheck('startIpAddress', '0.0.0.0'),
                         JMESPathCheck('endIpAddress', '255.255.255.255')])

        # Case 2 : Provision a server with public access allowing all azure services
        result = self.cmd('postgres flexible-server create -g {} -n {} --public-access {} -l {}'
                          .format(resource_group, servers[1], '0.0.0.0', location)).get_output_in_json()

        self.cmd('postgres flexible-server firewall-rule show -g {} -n {} -r {}'
                 .format(resource_group, servers[1], result["firewallName"]),
                 checks=[JMESPathCheck('startIpAddress', '0.0.0.0'),
                         JMESPathCheck('endIpAddress', '0.0.0.0')])

        # Case 3 : Provision a server with public access with range
        result = self.cmd('postgres flexible-server create -g {} -n {} --public-access {} -l {}'
                          .format(resource_group, servers[2], '10.0.0.0-12.0.0.0', location)).get_output_in_json()

        self.cmd('postgres flexible-server firewall-rule show -g {} -n {} -r {}'
                 .format(resource_group, servers[2], result["firewallName"]),
                 checks=[JMESPathCheck('startIpAddress', '10.0.0.0'),
                         JMESPathCheck('endIpAddress', '12.0.0.0')])

        # Case 4 : Provision a server with public access with auto-detection
        result = self.cmd('postgres flexible-server create -g {} -n {} -l {} --yes'
                          .format(resource_group, servers[3], location)).get_output_in_json()

        firewall_rule = self.cmd('postgres flexible-server firewall-rule show -g {} -n {} -r {}'
                                 .format(resource_group, servers[3], result["firewallName"])).get_output_in_json()
        self.assertEqual(firewall_rule['startIpAddress'], firewall_rule['endIpAddress'])

        # Case 5 : Update server to have firewall rules
        firewall_rule_name = 'firewall_test_rule'
        start_ip_address = '10.10.10.10'
        end_ip_address = '12.12.12.12'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        self.cmd('postgres flexible-server create -l {} -g {} -n {} --public-access none'
                 .format(location, resource_group, servers[4]))

        self.cmd('postgres flexible-server update -g {} -n {} --public-access Enabled'
                 .format(resource_group, servers[4]),
                 checks=[JMESPathCheck('network.publicNetworkAccess', "Enabled")])

        self.cmd('postgres flexible-server firewall-rule create -g {} --name {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(resource_group, servers[4], firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('postgres flexible-server firewall-rule show -g {} --name {} --rule-name {} '
                 .format(resource_group, servers[4], firewall_rule_name),
                 checks=firewall_rule_checks)

        new_start_ip_address = '9.9.9.9'
        self.cmd('postgres flexible-server firewall-rule update -g {} --name {} --rule-name {} --start-ip-address {}'
                 .format(resource_group, servers[4], firewall_rule_name, new_start_ip_address),
                 checks=[JMESPathCheck('startIpAddress', new_start_ip_address)])

        new_end_ip_address = '13.13.13.13'
        self.cmd('postgres flexible-server firewall-rule update -g {} --name {} --rule-name {} --end-ip-address {}'
                 .format(resource_group, servers[4], firewall_rule_name, new_end_ip_address))

        self.cmd('postgres flexible-server firewall-rule list -g {} -n {}'
                 .format(resource_group, servers[4]), checks=[JMESPathCheck('length(@)', 1)])

        self.cmd('postgres flexible-server firewall-rule delete --rule-name {} -g {} --name {} --yes'
                 .format(firewall_rule_name, resource_group, servers[4]), checks=NoneCheck())

        # delete all servers
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[1]),
                 checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[2]),
                 checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[3]),
                 checks=NoneCheck())
    
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[4]),
                 checks=NoneCheck())