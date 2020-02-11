# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


class NWConnectionMonitorScenarioTest(ScenarioTest):

    def _prepare_vm(self, resource_group, vm):
        vm_create_cmd_tpl = 'vm create -g {rg} --name {vm} ' \
                            '--image UbuntuLTS ' \
                            '--authentication-type password ' \
                            '--admin-username deploy ' \
                            '--admin-password PassPass10!) ' \
                            '--nsg {vm} '
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

        # add an endpoint as source
        self.cmd('network watcher connection-monitor endpoint add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--source-test-groups {test_group} '
                 '--name vm02 '
                 '--resource-id {vm2_id} '
                 '--filter-type Include '
                 '--filter-item type=AgentAddress address=10.0.0.1 '
                 '--filter-item type=AgentAddress address=10.0.0.2 ')

        # add an endpoint as destination
        self.cmd('network watcher connection-monitor endpoint add '
                 '--connection-monitor {cmv2} '
                 '--location {location} '
                 '--dest-test-groups {test_group} '
                 '--name Github '
                 '--address github.com ')

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
                 '--name vm02 '
                 '--test-groups DefaultTestGroup ')
        self.cmd('network watcher connection-monitor endpoint list --connection-monitor {cmv2} --location {location}',
                 checks=self.check('length(@)', 3))
