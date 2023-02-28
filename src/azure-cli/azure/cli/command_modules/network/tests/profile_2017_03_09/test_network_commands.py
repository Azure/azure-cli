# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-lines
import os
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import supported_api_version, ResourceType

from azure.cli.testsdk import (
    ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, live_only, record_only)

from knack.util import CLIError

from msrestazure.tools import resource_id

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class NetworkLoadBalancerScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_load_balancer')
    def test_network_lb(self, resource_group):

        self.kwargs.update({
            'lb': 'lb',
            'rt': 'Microsoft.Network/loadBalancers',
            'vnet': 'mytestvnet',
            'pri_ip': '10.0.0.15',
            'pub_ip': 'publicip4'
        })

        # test lb create with min params (new ip)
        self.cmd('network lb create -n {lb}1 -g {rg}', checks=[
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            self.check('loadBalancer.frontendIPConfigurations[0].resourceGroup', '{rg}')
        ])

        # test internet facing load balancer with new static public IP
        self.cmd('network lb create -n {lb}2 -g {rg} --public-ip-address-allocation static --tags foo=doo')
        self.cmd('network public-ip show -g {rg} -n PublicIP{lb}2', checks=[
            self.check('publicIpAllocationMethod', 'Static'),
        ])

        # test internal load balancer create (existing subnet ID)
        self.kwargs['subnet_id'] = self.cmd('network vnet create -n {vnet} -g {rg} --subnet-name default').get_output_in_json()['newVNet']['subnets'][0]['id']
        self.cmd('network lb create -n {lb}3 -g {rg} --subnet {subnet_id} --private-ip-address {pri_ip}', checks=[
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Static'),
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAddress', '{pri_ip}'),
            self.check('loadBalancer.frontendIPConfigurations[0].resourceGroup', '{rg}'),
            self.check("loadBalancer.frontendIPConfigurations[0].properties.subnet.id", '{subnet_id}')
        ])

        # test internet facing load balancer with existing public IP (by name)
        self.cmd('network public-ip create -n {pub_ip} -g {rg}')
        self.cmd('network lb create -n {lb}4 -g {rg} --public-ip-address {pub_ip}', checks=[
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            self.check('loadBalancer.frontendIPConfigurations[0].resourceGroup', '{rg}'),
            self.check("loadBalancer.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{pub_ip}')", True)
        ])

        self.cmd('network lb list', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True)
        ])
        self.cmd('network lb list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
        self.cmd('network lb show --resource-group {rg} --name {lb}1', checks=[
            self.check('type(@)', 'object'),
            self.check('type', '{rt}'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{lb}1')
        ])
        self.cmd('network lb delete --resource-group {rg} --name {lb}1')
        # Expecting no results as we just deleted the only lb in the resource group
        self.cmd('network lb list --resource-group {rg}',
                 checks=self.check('length(@)', 3))


class NetworkLoadBalancerIPConfigScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_load_balancer_ip_config')
    def test_network_load_balancer_ip_config(self, resource_group):

        for i in range(1, 4):  # create 3 public IPs to use for the test
            self.cmd('network public-ip create -g {{rg}} -n publicip{}'.format(i))

        # create internet-facing LB with public IP (lb1)
        self.cmd('network lb create -g {rg} -n lb1 --public-ip-address publicip1')

        # create internal LB (lb2)
        self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1')
        self.cmd('network vnet subnet create -g {rg} --vnet-name vnet1 -n subnet2 --address-prefix 10.0.1.0/24')
        self.cmd('network lb create -g {rg} -n lb2 --subnet subnet1 --vnet-name vnet1')

        # Test frontend IP configuration for internet-facing LB
        self.cmd('network lb frontend-ip create -g {rg} --lb-name lb1 -n ipconfig1 --public-ip-address publicip2')
        self.cmd('network lb frontend-ip list -g {rg} --lb-name lb1',
                 checks=self.check('length(@)', 2))
        self.cmd('network lb frontend-ip update -g {rg} --lb-name lb1 -n ipconfig1 --public-ip-address publicip3')
        self.cmd('network lb frontend-ip show -g {rg} --lb-name lb1 -n ipconfig1',
                 checks=self.check("publicIPAddress.contains(id, 'publicip3')", True))

        # test generic update
        self.kwargs['ip2_id'] = resource_id(subscription=self.get_subscription_id(), resource_group=self.kwargs['rg'], namespace='Microsoft.Network', type='publicIPAddresses', name='publicip2')
        self.cmd('network lb frontend-ip update -g {rg} --lb-name lb1 -n ipconfig1 --set publicIPAddress.id="{ip2_id}"',
                 checks=self.check("publicIPAddress.contains(id, 'publicip2')", True))
        self.cmd('network lb frontend-ip delete -g {rg} --lb-name lb1 -n ipconfig1')
        self.cmd('network lb frontend-ip list -g {rg} --lb-name lb1',
                 checks=self.check('length(@)', 1))

        # Test frontend IP configuration for internal LB
        self.cmd('network lb frontend-ip create -g {rg} --lb-name lb2 -n ipconfig2 --vnet-name vnet1 --subnet subnet1 --private-ip-address 10.0.0.99')
        self.cmd('network lb frontend-ip list -g {rg} --lb-name lb2',
                 checks=self.check('length(@)', 2))
        self.cmd('network lb frontend-ip update -g {rg} --lb-name lb2 -n ipconfig2 --subnet subnet2 --vnet-name vnet1 --private-ip-address 10.0.1.100')
        self.cmd('network lb frontend-ip show -g {rg} --lb-name lb2 -n ipconfig2',
                 checks=self.check("subnet.contains(id, 'subnet2')", True))


class NetworkLoadBalancerSubresourceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_rules')
    def test_network_lb_nat_rules(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.cmd('network lb create -g {rg} -n {lb}')

        for count in range(1, 3):
            self.cmd('network lb inbound-nat-rule create -g {{rg}} --lb-name {{lb}} -n rule{0} --protocol tcp --frontend-port {0} --backend-port {0} --frontend-ip-name LoadBalancerFrontEnd'.format(count))
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule3 --protocol tcp --frontend-port 3 --backend-port 3')
        self.cmd('network lb inbound-nat-rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))
        self.cmd('network lb inbound-nat-rule update -g {rg} --lb-name {lb} -n rule1 --floating-ip true --idle-timeout 10')
        self.cmd('network lb inbound-nat-rule show -g {rg} --lb-name {lb} -n rule1', checks=[
            self.check('enableFloatingIP', True),
            self.check('idleTimeoutInMinutes', 10)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-rule update -g {rg} --lb-name {lb} -n rule1 --set idleTimeoutInMinutes=5',
                 checks=self.check('idleTimeoutInMinutes', 5))

        for count in range(1, 4):
            self.cmd('network lb inbound-nat-rule delete -g {{rg}} --lb-name {{lb}} -n rule{}'.format(count))
        self.cmd('network lb inbound-nat-rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_pools')
    def test_network_lb_nat_pools(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.cmd('network lb create -g {rg} -n {lb}')

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool create -g {{rg}} --lb-name {{lb}} -n rule{0} --protocol tcp --frontend-port-range-start {0}  --frontend-port-range-end {1} --backend-port {0}'.format(count, count + 999))
        self.cmd('network lb inbound-nat-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))
        self.cmd('network lb inbound-nat-pool update -g {rg} --lb-name {lb} -n rule1000 --protocol udp --backend-port 50')
        self.cmd('network lb inbound-nat-pool show -g {rg} --lb-name {lb} -n rule1000', checks=[
            self.check('protocol', 'Udp'),
            self.check('backendPort', 50)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-pool update -g {rg} --lb-name {lb} -n rule1000 --set protocol=Tcp',
                 checks=self.check('protocol', 'Tcp'))

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool delete -g {{rg}} --lb-name {{lb}} -n rule{}'.format(count))
        self.cmd('network lb inbound-nat-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_address_pool')
    def test_network_lb_address_pool(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.cmd('network lb create -g {rg} -n {lb}')

        for i in range(1, 4):
            self.cmd('network lb address-pool create -g {{rg}} --lb-name {{lb}} -n bap{}'.format(i),
                     checks=self.check('name', 'bap{}'.format(i)))
        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 4))
        self.cmd('network lb address-pool show -g {rg} --lb-name {lb} -n bap1',
                 checks=self.check('name', 'bap1'))
        self.cmd('network lb address-pool delete -g {rg} --lb-name {lb} -n bap1',
                 checks=self.is_empty())
        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_probes')
    def test_network_lb_probes(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.kwargs['lb2'] = 'lb2'
        self.cmd('network lb create -g {rg} -n {lb}')

        for i in range(1, 4):
            self.cmd('network lb probe create -g {{rg}} --lb-name {{lb}} -n probe{0} --port {0} --protocol http --path "/test{0}"'.format(i))
        self.cmd('network lb probe list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))
        self.cmd('network lb probe update -g {rg} --lb-name {lb} -n probe1 --interval 20 --threshold 5')
        self.cmd('network lb probe update -g {rg} --lb-name {lb} -n probe2 --protocol tcp --path ""')
        self.cmd('network lb probe show -g {rg} --lb-name {lb} -n probe1', checks=[
            self.check('intervalInSeconds', 20),
            self.check('numberOfProbes', 5)
        ])
        # test generic update
        self.cmd('network lb probe update -g {rg} --lb-name {lb} -n probe1 --set intervalInSeconds=15 --set numberOfProbes=3', checks=[
            self.check('intervalInSeconds', 15),
            self.check('numberOfProbes', 3)
        ])

        self.cmd('network lb probe show -g {rg} --lb-name {lb} -n probe2', checks=[
            self.check('protocol', 'Tcp'),
            self.check('path', None)
        ])
        self.cmd('network lb probe delete -g {rg} --lb-name {lb} -n probe3')
        self.cmd('network lb probe list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_rules')
    def test_network_lb_rules(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.cmd('network lb create -g {rg} -n {lb}')

        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n rule2 --frontend-port 60 --backend-port 60 --protocol tcp')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap1')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap2')
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n rule1 --frontend-ip-name LoadBalancerFrontEnd --frontend-port 40 --backend-pool-name bap1 --backend-port 40 --protocol tcp')

        self.cmd('network lb rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))
        self.cmd('network lb rule update -g {rg} --lb-name {lb} -n rule1 --floating-ip true --idle-timeout 20 --load-distribution sourceip --protocol udp')
        self.cmd('network lb rule update -g {rg} --lb-name {lb} -n rule2 --backend-pool-name bap2 --load-distribution sourceipprotocol')
        self.cmd('network lb rule show -g {rg} --lb-name {lb} -n rule1', checks=[
            self.check('enableFloatingIP', True),
            self.check('idleTimeoutInMinutes', 20),
            self.check('loadDistribution', 'SourceIP'),
            self.check('protocol', 'Udp')
        ])
        # test generic update
        self.cmd('network lb rule update -g {rg} --lb-name {lb} -n rule1 --set idleTimeoutInMinutes=5',
                 checks=self.check('idleTimeoutInMinutes', 5))

        self.cmd('network lb rule show -g {rg} --lb-name {lb} -n rule2', checks=[
            self.check("backendAddressPool.contains(id, 'bap2')", True),
            self.check('loadDistribution', 'SourceIPProtocol')
        ])
        self.cmd('network lb rule delete -g {rg} --lb-name {lb} -n rule1')
        self.cmd('network lb rule delete -g {rg} --lb-name {lb} -n rule2')
        self.cmd('network lb rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 0))


class NetworkLocalGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='local_gateway_scenario')
    def test_network_local_gateway(self, resource_group):

        self.kwargs.update({
            'lgw1': 'lgw1',
            'lgw2': 'lgw2',
            'rt': 'Microsoft.Network/localNetworkGateways'
        })
        self.cmd('network local-gateway create --resource-group {rg} --name {lgw1} --gateway-ip-address 10.1.1.1 --local-address-prefixes 10.0.1.0/24 --tags foo=doo')
        self.cmd('network local-gateway update --resource-group {rg} --name {lgw1} --tags foo=boo',
                 checks=self.check('tags.foo', 'boo'))
        self.cmd('network local-gateway show --resource-group {rg} --name {lgw1}', checks=[
            self.check('type', '{rt}'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{lgw1}')])

        self.cmd('network local-gateway create --resource-group {rg} --name {lgw2} --gateway-ip-address 10.1.1.2 --local-address-prefixes 10.0.2.0/24',
                 checks=self.check('localNetworkAddressSpace.addressPrefixes[0]', '10.0.2.0/24'))

        self.cmd('network local-gateway list --resource-group {rg}',
                 checks=self.check('length(@)', 2))

        self.cmd('network local-gateway delete --resource-group {rg} --name {lgw1}')
        self.cmd('network local-gateway list --resource-group {rg}',
                 checks=self.check('length(@)', 1))


class NetworkVpnGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_gateway')
    def test_network_vpn_gateway(self, resource_group):

        self.kwargs.update({
            'vnet1': 'myvnet1',
            'vnet2': 'myvnet2',
            'vnet3': 'myvnet3',
            'gw1': 'gateway1',
            'gw2': 'gateway2',
            'gw3': 'gateway3',
            'ip1': 'pubip1',
            'ip2': 'pubip2',
            'ip3': 'pubip3'
        })

        self.cmd('network public-ip create -n {ip1} -g {rg}')
        self.cmd('network public-ip create -n {ip2} -g {rg}')
        self.cmd('network public-ip create -n {ip3} -g {rg}')
        self.cmd('network vnet create -g {rg} -n {vnet1} --subnet-name GatewaySubnet --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.0.0/24')
        self.cmd('network vnet create -g {rg} -n {vnet2} --subnet-name GatewaySubnet --address-prefix 10.1.0.0/16')
        self.cmd('network vnet create -g {rg} -n {vnet3} --subnet-name GatewaySubnet --address-prefix 10.2.0.0/16')

        self.kwargs.update({'sub': self.get_subscription_id()})
        self.kwargs.update({
            'vnet1_id': '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet1}'.format(**self.kwargs),
            'vnet2_id': '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet2}'.format(**self.kwargs)
        })

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1_id} --public-ip-address {ip1} --no-wait')
        self.cmd('network vnet-gateway create -g {rg} -n {gw2} --vnet {vnet2_id} --public-ip-address {ip2} --no-wait')
        self.cmd('network vnet-gateway create -g {rg} -n {gw3} --vnet {vnet3} --public-ip-address {ip3} --no-wait --sku standard --asn 12345 --bgp-peering-address 10.2.250.250 --peer-weight 50')

        self.cmd('network vnet-gateway wait -g {rg} -n {gw1} --created')
        self.cmd('network vnet-gateway wait -g {rg} -n {gw2} --created')
        self.cmd('network vnet-gateway wait -g {rg} -n {gw3} --created')

        self.cmd('network vnet-gateway show -g {rg} -n {gw1}', checks=[
            self.check('gatewayType', 'Vpn'),
            self.check('sku.capacity', 2),
            self.check('sku.name', 'Basic'),
            self.check('vpnType', 'RouteBased'),
            self.check('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {rg} -n {gw2}', checks=[
            self.check('gatewayType', 'Vpn'),
            self.check('sku.capacity', 2),
            self.check('sku.name', 'Basic'),
            self.check('vpnType', 'RouteBased'),
            self.check('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {rg} -n {gw3}', checks=[
            self.check('sku.name', 'Standard'),
            self.check('enableBgp', True),
            self.check('bgpSettings.asn', 12345),
            self.check('bgpSettings.bgpPeeringAddress', '10.2.250.250'),
            self.check('bgpSettings.peerWeight', 50)
        ])

        self.kwargs.update({
            'conn12': 'conn1to2',
            'conn21': 'conn2to1',
            'gw1_id': '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworkGateways/{gw1}'.format(**self.kwargs)
        })

        self.cmd('network vpn-connection create -n {conn12} -g {rg} --shared-key 123 --vnet-gateway1 {gw1_id} --vnet-gateway2 {gw2} --tags foo=doo')
        self.cmd('network vpn-connection update -n {conn12} -g {rg} --routing-weight 25 --tags foo=boo',
                 checks=self.check('routingWeight', 25))
        self.cmd('network vpn-connection create -n {conn21} -g {rg} --shared-key 123 --vnet-gateway2 {gw1_id} --vnet-gateway1 {gw2}')


class NetworkVpnClientPackageScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer('cli_test_vpn_client_package')
    def test_vpn_client_package(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1',
            'public_ip': 'pip1',
            'gateway_prefix': '100.1.1.0/24',
            'gateway': 'vgw1',
            'cert': 'cert1',
            'cert_path': os.path.join(TEST_DIR, 'test-root-cert.cer')
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n {public_ip}')
        self.cmd('network vnet-gateway create -g {rg} -n {gateway} --address-prefix {gateway_prefix} --vnet {vnet} --public-ip-address {public_ip}')
        self.cmd('network vnet-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert} --public-cert-data "{cert_path}"')
        output = self.cmd('network vnet-gateway vpn-client generate -g {rg} -n {gateway}').get_output_in_json()
        self.assertTrue('.exe' in output, 'Expected EXE file in output.\nActual: {}'.format(str(output)))


class NetworkVNetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_vnet_test')
    def test_network_vnet(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'rt': 'Microsoft.Network/virtualNetworks'
        })

        self.cmd('network vnet create --resource-group {rg} --name {vnet} --subnet-name default', checks=[
            self.check('newVNet.provisioningState', 'Succeeded'),
            self.check('newVNet.addressSpace.addressPrefixes[0]', '10.0.0.0/16')
        ])

        self.cmd('network vnet list', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True)
        ])
        self.cmd('network vnet list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True),
        ])
        self.cmd('network vnet show --resource-group {rg} --name {vnet}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{vnet}'),
            self.check('type', '{rt}')
        ])
        self.kwargs['prefixes'] = '20.0.0.0/16 10.0.0.0/16'
        self.cmd('network vnet update --resource-group {rg} --name {vnet} --address-prefixes {prefixes} --dns-servers 1.2.3.4', checks=[
            self.check('length(addressSpace.addressPrefixes)', 2),
            self.check('dhcpOptions.dnsServers[0]', '1.2.3.4')
        ])
        self.cmd('network vnet update -g {rg} -n {vnet} --dns-servers ""', checks=[
            self.check('length(addressSpace.addressPrefixes)', 2),
            self.check('dhcpOptions.dnsServers', [])
        ])

        # test generic update
        self.cmd('network vnet update --resource-group {rg} --name {vnet} --set addressSpace.addressPrefixes[0]="20.0.0.0/24"',
                 checks=self.check('addressSpace.addressPrefixes[0]', '20.0.0.0/24'))

        self.cmd('network vnet subnet create --resource-group {rg} --vnet-name {vnet} --name {subnet} --address-prefix 20.0.0.0/24')
        self.cmd('network vnet subnet list --resource-group {rg} --vnet-name {vnet}',
                 checks=self.check('type(@)', 'array'))
        self.cmd('network vnet subnet show --resource-group {rg} --vnet-name {vnet} --name {subnet}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{subnet}'),
        ])

        self.cmd('network vnet subnet delete --resource-group {rg} --vnet-name {vnet} --name {subnet}')
        self.cmd('network vnet subnet list --resource-group {rg} --vnet-name {vnet}',
                 checks=self.check("length([?name == '{subnet}'])", 0))

        self.cmd('network vnet list --resource-group {rg}',
                 checks=self.check("length([?name == '{vnet}'])", 1))
        self.cmd('network vnet delete --resource-group {rg} --name {vnet}')
        self.cmd('network vnet list --resource-group {rg}', checks=self.is_empty())


class NetworkRouteTableOperationScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_route_table')
    def test_network_route_table_operation(self, resource_group):

        self.kwargs.update({
            'table': 'cli-test-route-table',
            'route': 'my-route',
            'rt': 'Microsoft.Network/routeTables'
        })

        self.cmd('network route-table create -n {table} -g {rg} --tags foo=doo',
                 checks=self.check('tags.foo', 'doo'))
        self.cmd('network route-table update -n {table} -g {rg} --tags foo=boo', checks=[
            self.check('tags.foo', 'boo')
        ])
        self.cmd('network route-table route create --address-prefix 10.0.5.0/24 -n {route} -g {rg} --next-hop-type None --route-table-name {table}')

        self.cmd('network route-table list',
                 checks=self.check('type(@)', 'array'))
        self.cmd('network route-table list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{table}'),
            self.check('[0].type', '{rt}')
        ])
        self.cmd('network route-table show --resource-group {rg} --name {table}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{table}'),
            self.check('type', '{rt}')
        ])
        self.cmd('network route-table route list --resource-group {rg} --route-table-name {table}',
                 checks=self.check('type(@)', 'array'))
        self.cmd('network route-table route show --resource-group {rg} --route-table-name {table} --name {route}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{route}'),
        ])
        self.cmd('network route-table route delete --resource-group {rg} --route-table-name {table} --name {route} -y')
        self.cmd('network route-table route list --resource-group {rg} --route-table-name {table}', checks=self.is_empty())
        self.cmd('network route-table delete --resource-group {rg} --name {table} -y')
        self.cmd('network route-table list --resource-group {rg}', checks=self.is_empty())
