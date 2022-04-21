# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from knack.util import CLIError

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


class NWConnectionMonitorScenarioTest(ScenarioTest):

    def _prepare_vm(self, resource_group, vm):
        vm_create_cmd_tpl = 'vm create -g {rg} --name {vm} ' \
                            '--image UbuntuLTS ' \
                            '--nsg {vm} ' \
                            '--nsg-rule None '
        vm_info = self.cmd(vm_create_cmd_tpl.format(rg=resource_group, vm=vm)).get_output_in_json()

        vm_enable_ext_tpl = 'vm extension set -g {rg} ' \
                            '--vm-name {vm} ' \
                            '--name NetworkWatcherAgentLinux ' \
                            '--publisher Microsoft.Azure.NetworkWatcher '
        self.cmd(vm_enable_ext_tpl.format(rg=resource_group, vm=vm))

        return vm_info

    def _prepare_connection_monitor_v2_env(self, resource_group, location):
        self.kwargs.update({
            'rg': resource_group,
            'location': location,
            'cmv2': 'CMv2-01',
            'test_group': 'DefaultTestGroup'
        })

        vm1_info = self._prepare_vm(resource_group, 'vm1')
        vm2_info = self._prepare_vm(resource_group, 'vm2')

        self.kwargs.update({
            'vm1_id': vm1_info['id'],
            'vm2_id': vm2_info['id'],
        })

        # create a connection monitor v2 with TCP monitoring
        self.cmd('network watcher connection-monitor create '
                 '--location {location} '
                 '--name {cmv2} '
                 '--endpoint-source-name vm1 '
                 '--endpoint-source-resource-id {vm1_id} '
                 '--endpoint-dest-name bing '
                 '--endpoint-dest-address bing.com '
                 '--test-config-name DefaultTestConfig '
                 '--protocol Tcp '
                 '--tcp-port 2048 ')

    @ResourceGroupPreparer(name_prefix='cli_test_nw_connection_monitor', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v1(self, resource_group, resource_group_location):
        """
        This is copied from Azure/azure-cli,
        src/azure-cli/azure/cli/command_modules/network/tests/latest/test_network_commands.py,
        test_network_watcher_connection_monitor()
        """
        import time
        self.kwargs.update({
            'loc': resource_group_location,
            'vm2': 'vm2',
            'vm3': 'vm3',
            'cm': 'cm1'
        })

        self.cmd('vm create -g {rg} -n {vm2} '
                 '--image UbuntuLTS '
                 '--authentication-type password '
                 '--admin-username deploy '
                 '--admin-password PassPass10!) '
                 '--nsg {vm2} '
                 '--nsg-rule None')
        self.cmd('vm extension set -g {rg} '
                 '--vm-name {vm2} '
                 '-n NetworkWatcherAgentLinux '
                 '--publisher Microsoft.Azure.NetworkWatcher')
        self.cmd('vm create -g {rg} -n {vm3} '
                 '--image UbuntuLTS '
                 '--authentication-type password '
                 '--admin-username deploy '
                 '--admin-password PassPass10!) '
                 '--nsg {vm3} '
                 '--nsg-rule None')
        self.cmd('vm extension set -g {rg} '
                 '--vm-name {vm3} '
                 '-n NetworkWatcherAgentLinux '
                 '--publisher Microsoft.Azure.NetworkWatcher')
        time.sleep(20)
        self.cmd('network watcher connection-monitor create '
                 '-n {cm} '
                 '--source-resource {vm2} '
                 '-g {rg} '
                 '--dest-resource {vm3} '
                 '--dest-port 80 '
                 '--tags foo=doo')
        self.cmd('network watcher connection-monitor list -l {loc}')
        self.cmd('network watcher connection-monitor show -l {loc} -n {cm}')
        try:
            self.cmd('network watcher connection-monitor stop -l {loc} -n {cm}')
            self.cmd('network watcher connection-monitor start -l {loc} -n {cm}')
        except CLIError:
            pass
        self.cmd('network watcher connection-monitor query -l {loc} -n {cm}')
        self.cmd('network watcher connection-monitor delete -l {loc} -n {cm}')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_creation(self, resource_group, resource_group_location):
        # create a V2 connection monitor with --location and TCP configuration
        self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        # create a v2 connection monitor without --location and ICMP configuration
        self.cmd('network watcher connection-monitor create '
                 '--name cmv2-01 '
                 '--endpoint-source-name vm2 '
                 '--endpoint-source-resource-id {vm2_id} '
                 '--endpoint-dest-name bing '
                 '--endpoint-dest-address bing.com '
                 '--test-config-name DefaultIcmp '
                 '--protocol Icmp ')

        self.cmd('network watcher connection-monitor list -l {location}')
        self.cmd('network watcher connection-monitor show -l {location} -n {cmv2}')
        self.cmd('network watcher connection-monitor show -l {location} -n cmv2-01')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_endpoint(self, resource_group, resource_group_location):
        self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        self.cmd('network vnet create -g {rg} --name cmv2-vnet --subnet-name subnet1 --address-prefix 10.0.0.0/24')
        subnet = self.cmd('network vnet subnet show -g {rg} --vnet-name cmv2-vnet --name subnet1').get_output_in_json()
        self.kwargs.update({
            'cm_subnet_endpoint': 'cm_subnet_endpoint',
            'subnet_id': subnet['id']
        })

        # add an endpoint as source
        self.cmd('network watcher connection-monitor endpoint add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--source-test-groups {test_group} '
                 '--name {cm_subnet_endpoint} '
                 '--resource-id {subnet_id} '
                 '--type AzureSubnet '
                 '--address-exclude 10.0.0.25 '
                 '--coverage-level BelowAverage')

        # add an endpoint as destination
        self.cmd('network watcher connection-monitor endpoint add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--dest-test-groups {test_group} '
                 '--name Github '
                 '--address github.com '
                 '--type ExternalAddress')

        self.cmd('network watcher connection-monitor endpoint list --connection-monitor {cmv2} --location {location}',
                 checks=self.check('length(@)', 4))
        self.cmd('network watcher connection-monitor endpoint show '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name Github')

        # remove one
        self.cmd('network watcher connection-monitor endpoint remove '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name {cm_subnet_endpoint} '
                 '--test-groups DefaultTestGroup ')
        self.cmd('network watcher connection-monitor endpoint list --connection-monitor {cmv2} --location {location}',
                 checks=self.check('length(@)', 3))

    @unittest.skip('PathNotSupportedInBothHTTPConfigurationAndAddress')
    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_test_configuration(self, resource_group, resource_group_location):
        self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        # add a TCP test configuration
        self.cmd('network watcher connection-monitor test-configuration add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name TCPConfig '
                 '--protocol Tcp '
                 '--test-groups DefaultTestGroup '
                 '--tcp-port 8080 '
                 '--tcp-port-behavior ListenIfAvailable '
                 '--tcp-disable-trace-route true '
                 '--frequency 120 '
                 '--threshold-round-trip-time 1200')

        # add a HTTP test configuration
        self.cmd('network watcher connection-monitor test-configuration add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name HTTPConfig '
                 '--test-groups DefaultTestGroup '
                 '--protocol Http '
                 '--frequency 90 '
                 '--http-method Get '
                 '--http-path "/" '
                 '--http-valid-status-codes 200 301 '
                 '--http-request-header name=Host value=azure.com '
                 '--http-request-header name=UserAgent value=AzureCLITest ')
        self.cmd('network watcher connection-monitor test-configuration list '
                 '--connection-monitor {cmv2} '
                 '--location {location} ',
                 checks=self.check('length(@)', 3))
        self.cmd('network watcher connection-monitor test-configuration show '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name HTTPConfig ')

        # add a ICMP test configuration
        self.cmd('network watcher connection-monitor test-configuration add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name ICMPConfig '
                 '--test-groups DefaultTestGroup '
                 '--protocol Icmp ')
        self.cmd('network watcher connection-monitor test-configuration list '
                 '--connection-monitor {cmv2} '
                 '--location {location} ',
                 checks=self.check('length(@)', 4))
        self.cmd('network watcher connection-monitor test-configuration show '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name ICMPConfig ')

        self.cmd('network watcher connection-monitor test-configuration remove '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name HTTPConfig ')
        self.cmd('network watcher connection-monitor test-configuration list '
                 '--connection-monitor {cmv2} '
                 '--location {location} ',
                 checks=self.check('length(@)', 3))

    @unittest.skip('PathNotSupportedInBothHTTPConfigurationAndAddress')
    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_connection_monitor_v2_test_group(self, resource_group, resource_group_location):
        self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        # add an endpoint as source for later use
        self.cmd('network watcher connection-monitor endpoint add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--source-test-groups {test_group} '
                 '--name vm02 '
                 '--resource-id {vm2_id} '
                 '--filter-type Include '
                 '--filter-item type=AgentAddress address=10.0.0.1 '
                 '--filter-item type=AgentAddress address=10.0.0.2 ')

        # add an endpoint as destination for later use
        self.cmd('network watcher connection-monitor endpoint add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--dest-test-groups {test_group} '
                 '--name Github '
                 '--address github.com ')

        # add a HTTP test configuration for later use
        self.cmd('network watcher connection-monitor test-configuration add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name HTTPConfig '
                 '--test-groups DefaultTestGroup '
                 '--protocol Http '
                 '--frequency 90 '
                 '--http-method Get '
                 '--http-path "/" '
                 '--http-valid-status-codes 200 301 '
                 '--http-request-header name=Host value=azure.com '
                 '--http-request-header name=UserAgent value=AzureCLITest ')

        # add a ICMP test configuration
        self.cmd('network watcher connection-monitor test-configuration add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name ICMPConfig '
                 '--test-groups DefaultTestGroup '
                 '--protocol Icmp ')
        self.cmd('network watcher connection-monitor test-configuration list '
                 '--connection-monitor {cmv2} '
                 '--location {location} ',
                 checks=self.check('length(@)', 3))
        self.cmd('network watcher connection-monitor test-configuration show '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name ICMPConfig ')

        # add a test group with existing source endpoint, new-added destination endpoints and existing test config
        self.cmd('network watcher connection-monitor test-group add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name RouteTestGroup '
                 '--disable false '
                 '--endpoint-source-name vm1 '
                 '--endpoint-dest-name aks.ms '
                 '--endpoint-dest-address aks.ms '
                 '--test-config-name ICMPConfig ')
        self.cmd('network watcher connection-monitor test-group list '
                 '--connection-monitor {cmv2} '
                 '--location {location} ',
                 checks=self.check('length(@)', 2))
        self.cmd('network watcher connection-monitor test-group show '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name RouteTestGroup ')

        self.cmd('network watcher connection-monitor test-group remove '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--name DefaultTestGroup ')
        self.cmd('network watcher connection-monitor test-group list '
                 '--connection-monitor {cmv2} '
                 '--location {location} ',
                 checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_output(self, resource_group, resource_group_location):
        self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        self.kwargs.update({
            'workspace_name': self.create_random_name('clitest', 20)
        })

        workspace = self.cmd('monitor log-analytics workspace create '
                             '-g {rg} '
                             '--location {location} '
                             '--workspace-name {workspace_name} ').get_output_in_json()

        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        self.cmd('network watcher connection-monitor output list '
                 '--location {location} '
                 '--connection-monitor {cmv2} ')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_output_type_as_workspace(self, resource_group, resource_group_location):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'cmv2': 'CMv2-01',
            'test_group': 'DefaultTestGroup',
            'workspace_name': self.create_random_name('clitest', 20)
        })

        vm1_info = self._prepare_vm(resource_group, 'vm1')

        workspace = self.cmd('monitor log-analytics workspace create '
                             '-g {rg} '
                             '--location {location} '
                             '--workspace-name {workspace_name} ').get_output_in_json()

        self.kwargs.update({
            'vm1_id': vm1_info['id'],
            'workspace_id': workspace['id']
        })

        # create a connection monitor v2 with TCP monitoring
        self.cmd('network watcher connection-monitor create '
                    '--location {location} '
                    '--name {cmv2} '
                    '--endpoint-source-name vm1 '
                    '--endpoint-source-resource-id {vm1_id} '
                    '--endpoint-dest-name bing '
                    '--endpoint-dest-address bing.com '
                    '--test-config-name DefaultTestConfig '
                    '--protocol Tcp '
                    '--tcp-port 2048 '
                    '--workspace-ids {workspace_id} ', checks=[
                        self.check('name', '{cmv2}'),
                        self.check('outputs[0].workspaceSettings.workspaceResourceId', '{workspace_id}')
                    ])
