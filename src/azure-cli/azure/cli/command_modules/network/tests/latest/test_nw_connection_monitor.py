# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import sys


from knack.util import CLIError

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


class NWConnectionMonitorScenarioTest(ScenarioTest):

    def _prepare_vm(self, resource_group, vm):
        vm_create_cmd_tpl = 'vm create -g {rg} --name {vm} ' \
                            '--image Canonical:UbuntuServer:18.04-LTS:latest ' \
                            '--nsg {vm} ' \
                            '--generate-ssh-keys '\
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

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
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
                 '--protocol Icmp --tags tag=test',
                 checks=[
                     self.check('tags', {'tag': 'test'})
                 ])

        self.cmd('network watcher connection-monitor list -l {location}')
        self.cmd('network watcher connection-monitor show -l {location} -n {cmv2}')
        self.cmd('network watcher connection-monitor show -l {location} -n cmv2-01')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
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
        
#   ------------------------------ My Tests --------------------------------------------
        

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_output1(self, resource_group, resource_group_location):
        #self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)
        
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'cmv2': 'CMv2-01',
            'test_group': 'DefaultTestGroup',
            'workspace_name': self.create_random_name('clitest', 20)
        })
        
        #vm1_info = self._prepare_vm(resource_group, 'vm1')

        workspace = self.cmd('monitor log-analytics workspace create '
                             '-g {rg} '
                             '--location {location} '
                             '--workspace-name {workspace_name} ').get_output_in_json()
        
        print(workspace)

        self.kwargs.update({
            #'vm1_id': vm1_info['id'],
            'workspace_id': workspace['id']
        })

        #create an output ob
        # value returned after creation is equal to the workspace_id or not
        output=self.cmd('network watcher connection-monitor output add '
                '--type Workspace '
                '--workspace-id {workspace_id} ').get_output_in_json()
        
        print(output)
        print(type(output))
        
        self.check('output.workspaceResourceId', '{workspace_id}')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_endpoint1(self, resource_group, resource_group_location):

        self.cmd('network watcher connection-monitor endpoint add '
                '--name CdmTest '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/srisa-rg/providers/Microsoft.Compute/virtualMachines/CdmTest '
                '--type AzureVM ').get_output_in_json()
        self.check('name','CdmTest')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_endpoint2(self, resource_group, resource_group_location):
        
        #test endpoint add command with scope included in endpoint
        self.kwargs.update({
            'val1':{'address':'10.0.0.25'},
            'val2':{'address':'10.0.0.30'}
        })
        self.cmd('network watcher connection-monitor endpoint add '
                '--name CdmTest '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/srisa-rg/providers/Microsoft.Compute/virtualMachines/CdmTest '
                '--type AzureVM '
                '--scope-exclude "[{val1},{val2}]" ').get_output_in_json()

        self.check('name','CdmTest')

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_test_configuration1(self, resource_group, resource_group_location):
        #self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        self.kwargs.update({
            'location':'eastus',
             'header1': {'name':'UserAgent','value':'Edge'},
             'header2':{'name':'UserAgent','value':'Chrome'}
        })

        output = self.cmd('network watcher connection-monitor test-configuration add '
                 '--name testconfig '
                 '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 '
                  '--http-request-headers "[{header1},{header2}]" ').get_output_in_json()
        
        
        self.check('name', 'testconfig')
                

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_test_group1(self, resource_group, resource_group_location):

        endpoint1=self.cmd('network watcher connection-monitor endpoint add '
                '--name Bing '
                '--address bing.com '
                '--type ExternalAddress ').get_output_in_json()
        print("e1=",endpoint1)
        
        endpoint2=self.cmd('network watcher connection-monitor endpoint add '
                '--name Github '
                '--address github.com '
                '--type ExternalAddress ').get_output_in_json()
        
        #creating a test configuration

        self.kwargs.update({
             'header1': {'name':'UserAgent','value':'Edge'},
             'header2':{'name':'UserAgent','value':'Chrome'}
        })

        tc1 = self.cmd('network watcher connection-monitor test-configuration add '
                 '--name testconfig1 '
                 '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 '
                  '--http-request-headers "[{header1},{header2}]" ').get_output_in_json()
        
        tc2 = self.cmd('network watcher connection-monitor test-configuration add '
                 '--name testconfig2 '
                 '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 84 ').get_output_in_json()
        
        self.kwargs.update({
            'endpoint1': endpoint1,
            'endpoint2': endpoint2,
            'tc1': tc1,
            'tc2':tc2,
        })

        # Backup sys.argv
        original_argv = sys.argv

        # Set sys.argv to your test case
        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint1,endpoint2], '--destinations', [endpoint2], '--test-configurations', [tc1,tc2]]

        tg1=self.cmd("network watcher connection-monitor test-group add "
         '--name tg1 '
         "--sources [{endpoint1},{endpoint2}] "
         "--destinations [{endpoint2}] "
         "--test-configurations [{tc1},{tc2}] ")
        
        print("tg1=",tg1)
        self.check('name','tg1')

        # Restore sys.argv
        sys.argv = original_argv

    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='eastus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_test_group2(self, resource_group, resource_group_location):
        #test test group add command with scope included in endpoint
        self.kwargs.update({
            'val1':{'address':'10.0.0.25'},
            'val2':{'address':'10.0.0.30'}
        })
        

        endpoint1=self.cmd('network watcher connection-monitor endpoint add '
                '--name CdmTest '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/srisa-rg/providers/Microsoft.Compute/virtualMachines/CdmTest '
                '--type AzureVM '
                '--scope-exclude "[{val1},{val2}]" ').get_output_in_json()
        
        endpoint2=self.cmd('network watcher connection-monitor endpoint add '
                '--name Github '
                '--address github.com '
                '--type ExternalAddress ').get_output_in_json()
        
        #creating a test configuration

        self.kwargs.update({
             'header1': {'name':'UserAgent','value':'Edge'},
             'header2':{'name':'UserAgent','value':'Chrome'}
        })

        tc1 = self.cmd('network watcher connection-monitor test-configuration add '
                 '--name testconfig1 '
                 '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 '
                  '--http-request-headers "[{header1},{header2}]" ').get_output_in_json()
        
        tc2 = self.cmd('network watcher connection-monitor test-configuration add '
                 '--name testconfig2 '
                 '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 84 ').get_output_in_json()
        
        self.kwargs.update({
            'endpoint1': endpoint1,
            'endpoint2': endpoint2,
            'tc1': tc1,
            'tc2':tc2,
        })

        # Backup sys.argv
        original_argv = sys.argv

        # Set sys.argv to your test case
        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint1,endpoint2], '--destinations', [endpoint2], '--test-configurations', [tc1,tc2]]

        tg1=self.cmd("network watcher connection-monitor test-group add "
         '--name tg1 '
         "--sources [{endpoint1},{endpoint2}] "
         "--destinations [{endpoint2}] "
         "--test-configurations [{tc1},{tc2}] ")
        
        print("tg1=",tg1)
        self.check('name','tg1')

        # Restore sys.argv
        sys.argv = original_argv



    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_creation1(self, resource_group, resource_group_location):
    # create a V2 connection monitor with --location and TCP configuration
    #self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        endpoint1=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-azure-cni-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-azure-cni-rg/providers/Microsoft.Network/virtualNetworks/aks-azure-cni-vnet '
                '--type AzureVNet ').get_output_in_json()
        

        endpoint2=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-private-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-private-rg/providers/Microsoft.Network/virtualNetworks/aks-private-vnet '
                '--type AzureVNet ').get_output_in_json()
        
        endpoint3=self.cmd('network watcher connection-monitor endpoint add '
                '--name Google1 '
                '--address google.com '
                '--type ExternalAddress ').get_output_in_json()
        
        print("e1=",endpoint1)
        print("e2=",endpoint2)
        
        
        #creating a test configuration

        tc1 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name testconfig2 '
                '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 ').get_output_in_json()
        
        tc2 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name testconfig1 '
                '--frequency 120 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 ').get_output_in_json()

        self.kwargs.update({
            'endpoint1': endpoint1,
            'endpoint2': endpoint2,
            'endpoint3': endpoint3,
            'tc1': tc1,
            'tc2': tc2
        })
        
        # Backup sys.argv
        original_argv = sys.argv

        # Set sys.argv to your test case
        
        
        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint1,endpoint2], '--destinations', [endpoint2,endpoint3], '--test-configurations', [tc1,tc2]]
        
        tg1=self.cmd("network watcher connection-monitor test-group add "
        '--name tg1 '
        '--sources "[{endpoint1},{endpoint2}]" '
        '--destinations "[{endpoint2},{endpoint3}]" '
        '--test-configurations "[{tc1},{tc2}]" ').get_output_in_json()

        tg2=self.cmd("network watcher connection-monitor test-group add "
        '--name tg2 '
        '--sources "[{endpoint1},{endpoint3}]" '
        '--destinations "[{endpoint2},{endpoint3}]" '
        '--test-configurations "[{tc1},{tc2}]" ').get_output_in_json()
        
        print("tg1=",tg1)
        print("tg2=",tg2)

        # Restore sys.argv
        sys.argv = original_argv

        self.kwargs.update({
            'tg1': tg1,
            'tg2': tg2
        })


        original_argv = sys.argv
        sys.argv = ['network watcher connection-monitor create', '--test-groups', [tg1,tg2]]

        cm=self.cmd('network watcher connection-monitor create '
                '--name cmv2-01 '
                '--network-watcher-name kumamtestnw '
                '--resource-group kumamtestrg '
                '--location eastus2 '
                '--test-groups  "[{tg1},{tg2}]" ').get_output_in_json()
        

        sys.argv = original_argv

        self.check('name','cmv2-01')
        self.check('location','eastus2')
        self.check('testGroups[0].name','tg1')



    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_creation2(self, resource_group, resource_group_location):
    # create a V2 connection monitor with --location and TCP configuration
    #self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        endpoint12=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-private-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-private-rg/providers/Microsoft.Network/virtualNetworks/aks-private-vnet '
                '--type AzureVNet ').get_output_in_json()
        

        endpoint22=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-azure-cni-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-azure-cni-rg/providers/Microsoft.Network/virtualNetworks/aks-azure-cni-vnet '
                '--type AzureVNet ').get_output_in_json()
        
        endpoint32=self.cmd('network watcher connection-monitor endpoint add '
                '--name Github '
                '--address github.com '
                '--type ExternalAddress ').get_output_in_json()
        
        print("e1=",endpoint12)
        print("e2=",endpoint22)
        
        
        #creating a test configuration

        tc12 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name httptestconfig1 '
                '--frequency 60 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 ').get_output_in_json()
        
        tc22 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name httptestconfig2 '
                '--frequency 60 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 '
                  '--http-request-headers [{name=UserAgent value=Edge}] ').get_output_in_json()

        self.kwargs.update({
            'endpoint12': endpoint12,
            'endpoint22': endpoint22,
            'endpoint32': endpoint32,
            'tc1': tc12,
            'tc2': tc22
        })
        
        # Backup sys.argv
        original_argv = sys.argv

        # Set sys.argv to your test case
        
        
        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint12,endpoint22], '--destinations', [endpoint22,endpoint32], '--test-configurations', [tc12,tc22]]
        
        tg12=self.cmd("network watcher connection-monitor test-group add "
        '--name tg12 '
        '--sources "[{endpoint12},{endpoint22}]" '
        '--destinations "[{endpoint22},{endpoint32}]" '
        '--test-configurations "[{tc1},{tc2}]" ').get_output_in_json()
        
        #Restore sys.argv
        sys.argv = original_argv

        #backup sys.argv
        original_argv = sys.argv

        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint12], '--destinations', [endpoint22,endpoint32], '--test-configurations', [tc12,tc22]]


        tg22=self.cmd("network watcher connection-monitor test-group add "
        '--name tg22 '
        '--sources "[{endpoint12}]" '
        '--destinations "[{endpoint22},{endpoint32}]" '
        '--test-configurations "[{tc1},{tc2}]" ').get_output_in_json()
        
        print("tg1=",tg12)
        print("tg2=",tg22)

        # Restore sys.argv
        sys.argv = original_argv

        self.kwargs.update({
            'tg1': tg12,
            'tg2': tg22
        })


        original_argv = sys.argv
        sys.argv = ['network watcher connection-monitor create', '--test-groups', [tg12,tg22]]

        cm=self.cmd('network watcher connection-monitor create '
                '--name cmv2-05 '
                '--network-watcher-name kumamtestnw '
                '--resource-group kumamtestrg '
                '--location eastus2 '
                '--test-groups  "[{tg1},{tg2}]" ').get_output_in_json()
        

        sys.argv = original_argv

        self.check('name','cmv2-05')
        self.check('location','eastus2')
        self.check('testGroups[0].name','tg11')



    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_creation3(self, resource_group, resource_group_location):
    # create a V2 connection monitor with HTTP, TCP and ICMP configuration
    #self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)

        endpoint13=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-private-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-private-rg/providers/Microsoft.Network/virtualNetworks/aks-private-vnet '
                '--type AzureVNet ').get_output_in_json()
        

        endpoint23=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-azure-cni-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-azure-cni-rg/providers/Microsoft.Network/virtualNetworks/aks-azure-cni-vnet '
                '--type AzureVNet ').get_output_in_json()
        
        endpoint33=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-vnet-29306067 '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/MC_aks-managed-natgw-rg_aks-managed-natgw_eastus2/providers/Microsoft.Network/virtualNetworks/aks-vnet-29306067 '
                '--type AzureVNet ').get_output_in_json()
        
        # print("e1=",endpoint12)
        # print("e2=",endpoint22)
        
        
        #creating a test configuration

        tc13 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name httptestconfig '
                '--frequency 60 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 ').get_output_in_json()
        
        tc23 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name tcptestconfig '
                '--frequency 60 '
                 '--protocol Tcp '
                  '--tcp-port 80 ').get_output_in_json()
        
        tc33 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name icmptestconfig '
                '--frequency 60 '
                 '--protocol Icmp ').get_output_in_json()

        self.kwargs.update({
            'endpoint13': endpoint13,
            'endpoint23': endpoint23,
            'endpoint33': endpoint33,
            'tc13': tc13,
            'tc23': tc23,
            'tc33': tc33
        })
        
        # Backup sys.argv
        original_argv = sys.argv

        # Set sys.argv to your test case
        
        
        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint13,endpoint33], '--destinations', [endpoint23,endpoint33], '--test-configurations', [tc13,tc23]]
        
        tg13=self.cmd("network watcher connection-monitor test-group add "
        '--name tg13 '
        '--sources "[{endpoint13},{endpoint33}]" '
        '--destinations "[{endpoint23},{endpoint33}]" '
        '--test-configurations "[{tc13},{tc23}]" ').get_output_in_json()


        #Restore sys.argv
        sys.argv = original_argv

        #backup sys.argv
        original_argv = sys.argv

        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint13,endpoint23], '--destinations', [endpoint23,endpoint33], '--test-configurations', [tc23,tc33]]

        tg23=self.cmd("network watcher connection-monitor test-group add "
        '--name tg23 '
        '--sources "[{endpoint13},{endpoint23}]" '
        '--destinations "[{endpoint23},{endpoint33}]" '
        '--test-configurations "[{tc23},{tc33}]" ').get_output_in_json()
        
        print("tg1=",tg13)
        print("tg2=",tg23)

        # Restore sys.argv
        sys.argv = original_argv

        self.kwargs.update({
            'tg1': tg13,
            'tg2': tg23
        })


        original_argv = sys.argv
        sys.argv = ['network watcher connection-monitor create', '--test-groups', [tg13,tg23]]

        cm=self.cmd('network watcher connection-monitor create '
                '--name cmv2-06 '
                '--network-watcher-name kumamtestnw '
                '--resource-group kumamtestrg '
                '--location eastus2 '
                '--test-groups  "[{tg1},{tg2}]" ').get_output_in_json()
        

        sys.argv = original_argv

        self.check('name','cmv2-06')
        self.check('location','eastus2')
        self.check('testGroups[0].name','tg13')

    
    @ResourceGroupPreparer(name_prefix='connection_monitor_v2_test_', location='westus')
    @AllowLargeResponse()
    def test_nw_connection_monitor_v2_creation4(self, resource_group, resource_group_location):
    # create a V2 connection monitor with HTTP, TCP and ICMP configuration and request headers in http test configuration
    #self._prepare_connection_monitor_v2_env(resource_group, resource_group_location)


        endpoint14=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-private-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-private-rg/providers/Microsoft.Network/virtualNetworks/aks-private-vnet '
                '--type AzureVNet '
                '--coverage-level BelowAverage ').get_output_in_json()
        

        endpoint24=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-azure-cni-vnet '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/aks-azure-cni-rg/providers/Microsoft.Network/virtualNetworks/aks-azure-cni-vnet '
                '--type AzureVNet ').get_output_in_json()
        
        endpoint34=self.cmd('network watcher connection-monitor endpoint add '
                '--name aks-vnet-29306067 '
                '--resource-id /subscriptions/9cece3e3-0f7d-47ca-af0e-9772773f90b7/resourceGroups/MC_aks-managed-natgw-rg_aks-managed-natgw_eastus2/providers/Microsoft.Network/virtualNetworks/aks-vnet-29306067 '
                '--type AzureVNet ').get_output_in_json()
        
        # print("e1=",endpoint12)
        # print("e2=",endpoint22)
        
        
        #creating a test configuration
        self.kwargs.update({
            'header1': {'name':'UserAgent','value':'Edge'},
            'header2':{'name':'UserAgent','value':'Chrome'}
        })

        tc14 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name httptestconfig '
                '--frequency 60 '
                 '--protocol Http '
                  '--http-method Get '
                  '--http-valid-status-codes [200,201] '
                  '--http-port 80 '
                  '--http-request-headers "[{header1},{header2}]" ').get_output_in_json()
        
        tc24 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name tcptestconfig '
                '--frequency 60 '
                 '--protocol Tcp '
                  '--tcp-port 80 ').get_output_in_json()
        
        tc34 = self.cmd('network watcher connection-monitor test-configuration add '
                '--name icmptestconfig '
                '--frequency 60 '
                 '--protocol Icmp ').get_output_in_json()

        self.kwargs.update({
            'endpoint14': endpoint14,
            'endpoint24': endpoint24,
            'endpoint34': endpoint34,
            'tc14': tc14,
            'tc24': tc24,
            'tc34': tc34
        })
        
        # Backup sys.argv
        original_argv = sys.argv

        # Set sys.argv to your test case
        
        
        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint14,endpoint34], '--destinations', [endpoint24,endpoint34], '--test-configurations', [tc14,tc24]]
        
        tg14=self.cmd("network watcher connection-monitor test-group add "
        '--name tg13 '
        '--sources "[{endpoint14},{endpoint34}]" '
        '--destinations "[{endpoint24},{endpoint34}]" '
        '--test-configurations "[{tc14},{tc24}]" ').get_output_in_json()


        #Restore sys.argv
        sys.argv = original_argv

        #backup sys.argv
        original_argv = sys.argv

        sys.argv = ['network watcher connection-monitor test-group add', '--sources', [endpoint14,endpoint24], '--destinations', [endpoint24,endpoint34], '--test-configurations', [tc24,tc34]]

        tg24=self.cmd("network watcher connection-monitor test-group add "
        '--name tg23 '
        '--sources "[{endpoint14},{endpoint24}]" '
        '--destinations "[{endpoint24},{endpoint34}]" '
        '--test-configurations "[{tc24},{tc34}]" ').get_output_in_json()
        
        print("tg1=",tg14)
        print("tg2=",tg24)

        # Restore sys.argv
        sys.argv = original_argv

        self.kwargs.update({
            'tg1': tg14,
            'tg2': tg24
        })


        original_argv = sys.argv
        sys.argv = ['network watcher connection-monitor create', '--test-groups', [tg14,tg24]]

        cm=self.cmd('network watcher connection-monitor create '
                '--name cmv2-07 '
                '--network-watcher-name kumamtestnw '
                '--resource-group kumamtestrg '
                '--location eastus2 '
                '--test-groups  "[{tg1},{tg2}]" ').get_output_in_json()
        

        sys.argv = original_argv

        self.check('name','cmv2-07')
        self.check('location','eastus2')
        self.check('testGroups[0].name','tg14')

    