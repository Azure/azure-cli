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

from azure.mgmt.core.tools import resource_id

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class NetworkLoadBalancerWithSku(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_sku')
    def test_network_lb_sku(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'sku': 'standard',
            'location': 'eastus2',
            'ip': 'pubip1'
        })

        self.cmd('network lb create -g {rg} -l {location} -n {lb} --sku {sku} --public-ip-address {ip}')
        self.cmd('network lb show -g {rg} -n {lb}', checks=[
            self.check('sku.name', 'Standard')
        ])
        self.cmd('network public-ip show -g {rg} -n {ip}', checks=[
            self.check('sku.name', 'Standard'),
            self.check('publicIPAllocationMethod', 'Static')
        ])


class NetworkLoadBalancerWithZone(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_zone')
    def test_network_lb_zone(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'sku': 'standard',
            'zone': '2',
            'location': 'eastus2',
            'ip': 'pubip1'
        })

        # LB with public ip
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --sku {sku} --public-ip-zone {zone} --public-ip-address {ip}')
        # No zone on LB and its front-ip-config
        self.cmd('network lb show -g {rg} -n {lb}', checks=[
            self.check("frontendIPConfigurations[0].zones", None),
            self.check("zones", None)
        ])
        # Zone on public-ip which LB uses to infer the zone
        self.cmd('network public-ip show -g {rg} -n {ip}', checks=[
            self.check('zones[0]', self.kwargs['zone'])
        ])

        # LB w/o public ip, so called ILB
        self.kwargs['lb'] = 'lb2'
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --sku {sku} --frontend-ip-zone {zone} --public-ip-address "" --vnet-name vnet1 --subnet subnet1')
        # Zone on front-ip-config, and still no zone on LB resource
        self.cmd('network lb show -g {rg} -n {lb}', checks=[
            self.check("frontendIPConfigurations[0].zones[0]", self.kwargs['zone']),
            self.check("zones", None)
        ])
        # add a second frontend ip configuration
        self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb} -n LoadBalancerFrontEnd2 -z {zone}  --vnet-name vnet1 --subnet subnet1', checks=[
            self.check("zones", [self.kwargs['zone']])
        ])


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
            self.check('publicIPAllocationMethod', 'Static'),
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


class NetworkVpnConnectionIpSecPolicy(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_connection_ipsec')
    def test_network_vpn_connection_ipsec(self, resource_group):

        self.kwargs.update({
            'vnet1': 'vnet1',
            'vnet_prefix1': '10.11.0.0/16',
            'vnet_prefix2': '10.12.0.0/16',
            'fe_sub1': 'FrontEnd',
            'fe_sub_prefix1': '10.11.0.0/24',
            'be_sub1': 'BackEnd',
            'be_sub_prefix1': '10.12.0.0/24',
            'gw_sub1': 'GatewaySubnet',
            'gw_sub_prefix1': '10.12.255.0/27',
            'gw1ip': 'pip1',
            'gw1': 'gw1',
            'gw1_sku': 'Standard',
            'lgw1': 'lgw1',
            'lgw1ip': '131.107.72.22',
            'lgw1_prefix1': '10.61.0.0/16',
            'lgw1_prefix2': '10.62.0.0/16',
            'conn1': 'conn1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet1} --address-prefix {vnet_prefix1} {vnet_prefix2}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet1} -n {fe_sub1} --address-prefix {fe_sub_prefix1}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet1} -n {be_sub1} --address-prefix {be_sub_prefix1}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet1} -n {gw_sub1} --address-prefix {gw_sub_prefix1}')
        self.cmd('network public-ip create -g {rg} -n {gw1ip}')

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --public-ip-address {gw1ip} --vnet {vnet1} --sku {gw1_sku}')
        self.cmd('network local-gateway create -g {rg} -n {lgw1} --gateway-ip-address {lgw1ip} --local-address-prefixes {lgw1_prefix1} {lgw1_prefix2}')
        self.cmd('network vpn-connection create -g {rg} -n {conn1} --vnet-gateway1 {gw1} --local-gateway2 {lgw1} --shared-key AzureA1b2C3')

        self.cmd('network vpn-connection ipsec-policy add -g {rg} --connection-name {conn1} --ike-encryption AES256 --ike-integrity SHA384 --dh-group DHGroup24 --ipsec-encryption GCMAES256 --ipsec-integrity GCMAES256 --pfs-group PFS24 --sa-lifetime 7200 --sa-max-size 2048')
        self.cmd('network vpn-connection ipsec-policy list -g {rg} --connection-name {conn1}', checks=self.check('length(@)', 1))
        self.cmd('network vpn-connection ipsec-policy clear -g {rg} --connection-name {conn1}')
        self.cmd('network vpn-connection ipsec-policy list -g {rg} --connection-name {conn1}', checks=self.check('length(@)', 0))


class NetworkActiveActiveCrossPremiseScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_active_active_cross_premise_connection')
    def test_network_active_active_cross_premise_connection(self, resource_group):

        self.kwargs.update({
            'vnet1': 'vnet1',
            'vnet_prefix1': '10.11.0.0/16',
            'vnet_prefix2': '10.12.0.0/16',
            'vnet1_asn': 65010,
            'gw_subnet': 'GatewaySubnet',
            'gw_subnet_prefix': '10.12.255.0/27',
            'gw_ip1': 'gwip1',
            'gw_ip2': 'gwip2',
            'gw1': 'gw1',
            'lgw2': 'lgw2',
            'lgw_ip': '131.107.72.22',
            'lgw_prefix': '10.52.255.253/32',
            'bgp_peer1': '10.52.255.253',
            'lgw_asn': 65050,
            'lgw_loc': 'eastus',
            'conn_151': 'Vnet1toSite5_1',
            'conn_152': 'Vnet1toSite5_2',
            'shared_key': 'abc123',
            'shared_key2': 'a1b2c3',
            'lgw3': 'lgw3',
            'lgw3_ip': '131.107.72.23',
            'lgw3_prefix': '10.52.255.254/32',
            'bgp_peer2': '10.52.255.254'
        })

        self.cmd('network vnet create -g {rg} -n {vnet1} --address-prefix {vnet_prefix1} {vnet_prefix2} --subnet-name {gw_subnet} --subnet-prefix {gw_subnet_prefix}')
        self.cmd('network public-ip create -g {rg} -n {gw_ip1}')
        self.cmd('network public-ip create -g {rg} -n {gw_ip2}')

        # create the vnet gateway with active-active feature
        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1} --sku HighPerformance --asn {vnet1_asn} --public-ip-addresses {gw_ip1} {gw_ip2} --tags foo=doo')

        # switch to active-standby
        self.cmd('network vnet-gateway update -g {rg} -n {gw1} --vnet {vnet1} --sku HighPerformance --asn {vnet1_asn} --public-ip-addresses {gw_ip1} --no-wait --tags foo=boo')

        # create and connect first local-gateway
        self.cmd('network local-gateway create -g {rg} -n {lgw2} -l {lgw_loc} --gateway-ip-address {lgw_ip} --local-address-prefixes {lgw_prefix} --asn {lgw_asn} --bgp-peering-address {bgp_peer1}')
        self.cmd('network vpn-connection create -g {rg} -n {conn_151} --vnet-gateway1 {gw1} --local-gateway2 {lgw2} --shared-key {shared_key} --enable-bgp')
        self.cmd('network vpn-connection shared-key reset -g {rg} --connection-name {conn_151} --key-length 128')
        sk1 = self.cmd('network vpn-connection shared-key show -g {rg} --connection-name {conn_151}').get_output_in_json()
        self.cmd('network vpn-connection shared-key update -g {rg} --connection-name {conn_151} --value {shared_key2}').get_output_in_json()
        sk2 = self.cmd('network vpn-connection shared-key show -g {rg} --connection-name {conn_151}',
                       checks=self.check('value', '{shared_key2}'))
        self.assertNotEqual(sk1, sk2)

        # create and connect second local-gateway
        self.cmd('network local-gateway create -g {rg} -n {lgw3} -l {lgw_loc} --gateway-ip-address {lgw3_ip} --local-address-prefixes {lgw3_prefix} --asn {lgw_asn} --bgp-peering-address {bgp_peer2}')
        self.cmd('network vpn-connection create -g {rg} -n {conn_152} --vnet-gateway1 {gw1} --local-gateway2 {lgw3} --shared-key {shared_key} --enable-bgp')


class NetworkActiveActiveVnetScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_active_active_vnet_vnet_connection')
    def test_network_active_active_vnet_connection(self, resource_group):

        self.kwargs.update({
            'subnet': 'GatewaySubnet',
            'vnet1': 'vnet1',
            'vnet1_prefix': '10.21.0.0/16',
            'vnet1_asn': 65010,
            'gw1': 'vgw1',
            'gw1_prefix': '10.21.255.0/27',
            'gw1_ip1': 'gw1ip1',
            'gw1_ip2': 'gw1ip2',
            'vnet2': 'vnet2',
            'vnet2_prefix': '10.22.0.0/16',
            'vnet2_asn': 65020,
            'gw2': 'vgw2',
            'gw2_prefix': '10.22.255.0/27',
            'gw2_ip1': 'gw2ip1',
            'gw2_ip2': 'gw2ip2',
            'key': 'abc123',
            'conn12': 'vnet1to2',
            'conn21': 'vnet2to1'
        })

        # Create one VNet with two public IPs
        self.cmd('network vnet create -g {rg} -n {vnet1} --address-prefix {vnet1_prefix} --subnet-name {subnet} --subnet-prefix {gw1_prefix}')
        self.cmd('network public-ip create -g {rg} -n {gw1_ip1}')
        self.cmd('network public-ip create -g {rg} -n {gw1_ip2}')

        # Create second VNet with two public IPs
        self.cmd('network vnet create -g {rg} -n {vnet2} --address-prefix {vnet2_prefix} --subnet-name {subnet} --subnet-prefix {gw2_prefix}')
        self.cmd('network public-ip create -g {rg} -n {gw2_ip1}')
        self.cmd('network public-ip create -g {rg} -n {gw2_ip2}')

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1} --sku HighPerformance --asn {vnet1_asn} --public-ip-addresses {gw1_ip1} {gw1_ip2} --no-wait')
        self.cmd('network vnet-gateway create -g {rg} -n {gw2} --vnet {vnet2} --sku HighPerformance --asn {vnet2_asn} --public-ip-addresses {gw2_ip1} {gw2_ip2} --no-wait')

        # wait for gateway completion to finish
        self.cmd('network vnet-gateway wait -g {rg} -n {gw1} --created')
        self.cmd('network vnet-gateway wait -g {rg} -n {gw2} --created')

        # create and connect the VNet gateways
        self.cmd('network vpn-connection create -g {rg} -n {conn12} --vnet-gateway1 {gw1} --vnet-gateway2 {gw2} --shared-key {key} --enable-bgp')
        self.cmd('network vpn-connection create -g {rg} -n {conn21} --vnet-gateway1 {gw2} --vnet-gateway2 {gw1} --shared-key {key} --enable-bgp')


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

        self.cmd('network vnet-gateway list-learned-routes -g {rg} -n {gw1}')
        self.cmd('network vnet-gateway list-advertised-routes -g {rg} -n {gw1} --peer 10.1.1.1')
        self.cmd('network vnet-gateway list-bgp-peer-status -g {rg} -n {gw1} --peer 10.1.1.1')


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
        self.assertTrue('.zip' in output, 'Expected ZIP file in output.\nActual: {}'.format(str(output)))
        output = self.cmd('network vnet-gateway vpn-client show-url -g {rg} -n {gateway}').get_output_in_json()
        self.assertTrue('.zip' in output, 'Expected ZIP file in output.\nActual: {}'.format(str(output)))


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
        self.cmd('network vnet check-ip-address -g {rg} -n {vnet} --ip-address 10.0.0.50',
                 checks=self.check('available', True))

        self.cmd('network vnet check-ip-address -g {rg} -n {vnet} --ip-address 10.0.0.0',
                 checks=self.check('available', False))

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


class NetworkVNetPeeringScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vnet_peering')
    def test_network_vnet_peering(self, resource_group):

        # create two vnets with non-overlapping prefixes
        self.cmd('network vnet create -g {rg} -n vnet1')
        self.cmd('network vnet create -g {rg} -n vnet2 --subnet-name GatewaySubnet --address-prefix 11.0.0.0/16 --subnet-prefix 11.0.0.0/24')
        # create supporting resources for gateway
        self.cmd('network public-ip create -g {rg} -n ip1')
        ip_id = self.cmd('network public-ip show -g {rg} -n ip1 --query id').get_output_in_json()
        vnet_id = self.cmd('network vnet show -g {rg} -n vnet2 --query id').get_output_in_json()

        self.kwargs.update({
            'ip_id': ip_id,
            'vnet_id': vnet_id
        })
        # create the gateway on vnet2
        self.cmd('network vnet-gateway create -g {rg} -n gateway1 --public-ip-address {ip_id} --vnet {vnet_id} --tags foo=doo')

        vnet1_id = self.cmd('network vnet show -g {rg} -n vnet1 --query id').get_output_in_json()
        vnet2_id = self.cmd('network vnet show -g {rg} -n vnet2 --query id').get_output_in_json()

        self.kwargs.update({
            'vnet1_id': vnet1_id,
            'vnet2_id': vnet2_id
        })
        # set up gateway sharing from vnet1 to vnet2
        self.cmd('network vnet peering create -g {rg} -n peering2 --vnet-name vnet2 --remote-vnet {vnet1_id} --allow-gateway-transit', checks=[
            self.check('allowGatewayTransit', True),
            self.check('remoteVirtualNetwork.id', '{vnet1_id}'),
            self.check('peeringState', 'Initiated')
        ])
        self.cmd('network vnet peering create -g {rg} -n peering1 --vnet-name vnet1 --remote-vnet {vnet2_id} --use-remote-gateways --allow-forwarded-traffic', checks=[
            self.check('useRemoteGateways', True),
            self.check('remoteVirtualNetwork.id', '{vnet2_id}'),
            self.check('peeringState', 'Connected'),
            self.check('allowVirtualNetworkAccess', False)
        ])
        self.cmd('network vnet peering show -g {rg} -n peering1 --vnet-name vnet1',
                 checks=self.check('name', 'peering1'))
        self.cmd('network vnet peering list -g {rg} --vnet-name vnet2', checks=[
            self.check('[0].name', 'peering2'),
            self.check('length(@)', 1)
        ])
        self.cmd('network vnet peering update -g {rg} -n peering1 --vnet-name vnet1 --set useRemoteGateways=false', checks=[
            self.check('useRemoteGateways', False),
            self.check('allowForwardedTraffic', True)
        ])
        self.cmd('network vnet peering delete -g {rg} -n peering1 --vnet-name vnet1')
        self.cmd('network vnet peering list -g {rg} --vnet-name vnet1',
                 checks=self.is_empty())
        # must delete the second peering and the gateway or the resource group delete will fail
        self.cmd('network vnet peering delete -g {rg} -n peering2 --vnet-name vnet2')
        self.cmd('network vnet-gateway delete -g {rg} -n gateway1')


class NetworkSubnetEndpointServiceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_subnet_endpoint_service_test')
    def test_network_subnet_endpoint_service(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1'
        })
        self.cmd('network vnet list-endpoint-services -l westus', checks=[
            self.check('length(@)', 12),
            self.check('@[0].name', 'Microsoft.Storage')
        ])

        result = self.cmd('network vnet list-endpoint-services -l westus').get_output_in_json()
        self.assertGreaterEqual(len(result), 2)
        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.1.0/24 --service-endpoints Microsoft.Storage',
                 checks=self.check('serviceEndpoints[0].service', 'Microsoft.Storage'))
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints ""',
                 checks=self.check('serviceEndpoints', None))


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
        self.cmd('network route-table update -n {table} -g {rg} --tags foo=boo --disable-bgp-route-propagation', checks=[
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


class NetworkUsageListScenarioTest(ScenarioTest):

    def test_network_usage_list(self):
        self.cmd('network list-usages --location westus', checks=self.check('type(@)', 'array'))


class NetworkNicScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_nic_scenario')
    def test_network_nic(self, resource_group):

        self.kwargs.update({
            'nic': 'cli-test-nic',
            'rt': 'Microsoft.Network/networkInterfaces',
            'subnet': 'mysubnet',
            'vnet': 'myvnet',
            'nsg1': 'mynsg',
            'nsg2': 'myothernsg',
            'lb': 'mylb',
            'pri_ip': '10.0.0.15',
            'pub_ip': 'publicip1'
        })

        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}').get_output_in_json()['newVNet']['subnets'][0]['id']
        self.cmd('network nsg create -g {rg} -n {nsg1}')
        self.kwargs['nsg_id'] = self.cmd('network nsg show -g {rg} -n {nsg1}').get_output_in_json()['id']
        self.cmd('network nsg create -g {rg} -n {nsg2}')
        self.cmd('network public-ip create -g {rg} -n {pub_ip}')
        self.kwargs['pub_ip_id'] = self.cmd('network public-ip show -g {rg} -n {pub_ip}').get_output_in_json()['id']
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule1 --protocol tcp --frontend-port 100 --backend-port 100 --frontend-ip-name LoadBalancerFrontEnd')
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule2 --protocol tcp --frontend-port 200 --backend-port 200 --frontend-ip-name LoadBalancerFrontEnd')
        self.kwargs['rule_ids'] = ' '.join(self.cmd('network lb inbound-nat-rule list -g {rg} --lb-name {lb} --query "[].id"').get_output_in_json())
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap1')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap2')
        self.kwargs['address_pool_ids'] = ' '.join(self.cmd('network lb address-pool list -g {rg} --lb-name {lb} --query "[].id"').get_output_in_json())

        # create with minimum parameters
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet} --vnet-name {vnet}', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIPAllocationMethod', 'Dynamic'),
            self.check('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise optional parameters
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet_id} --ip-forwarding --private-ip-address {pri_ip} --public-ip-address {pub_ip} --internal-dns-name test --dns-servers 100.1.2.3 --lb-address-pools {address_pool_ids} --lb-inbound-nat-rules {rule_ids} --accelerated-networking --tags foo=doo', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIPAllocationMethod', 'Static'),
            self.check('NewNIC.ipConfigurations[0].privateIPAddress', '{pri_ip}'),
            self.check('NewNIC.enableIPForwarding', True),
            self.check('NewNIC.enableAcceleratedNetworking', True),
            self.check('NewNIC.provisioningState', 'Succeeded'),
            self.check('NewNIC.dnsSettings.internalDnsNameLabel', 'test'),
            self.check('length(NewNIC.dnsSettings.dnsServers)', 1)
        ])
        # exercise creating with NSG
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet} --vnet-name {vnet} --network-security-group {nsg1}', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIPAllocationMethod', 'Dynamic'),
            self.check('NewNIC.enableIPForwarding', False),
            self.check("NewNIC.networkSecurityGroup.contains(id, '{nsg1}')", True),
            self.check('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise creating with NSG and Public IP
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet} --vnet-name {vnet} --network-security-group {nsg_id} --public-ip-address {pub_ip_id}', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIPAllocationMethod', 'Dynamic'),
            self.check('NewNIC.enableIPForwarding', False),
            self.check("NewNIC.networkSecurityGroup.contains(id, '{nsg1}')", True),
            self.check('NewNIC.provisioningState', 'Succeeded')
        ])
        self.cmd('network nic list', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?contains(id, 'networkInterfaces')]) == length(@)", True)
        ])
        self.cmd('network nic list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
        self.cmd('network nic show --resource-group {rg} --name {nic}', checks=[
            self.check('type(@)', 'object'),
            self.check('type', '{rt}'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{nic}')
        ])
        self.cmd('network nic update -g {rg} -n {nic} --internal-dns-name noodle --ip-forwarding true --accelerated-networking false --dns-servers "" --network-security-group {nsg2}', checks=[
            self.check('enableIPForwarding', True),
            self.check('enableAcceleratedNetworking', False),
            self.check('dnsSettings.internalDnsNameLabel', 'noodle'),
            self.check('length(dnsSettings.dnsServers)', 0),
            self.check("networkSecurityGroup.contains(id, '{nsg2}')", True)
        ])
        # test generic update
        self.cmd('network nic update -g {rg} -n {nic} --set dnsSettings.internalDnsNameLabel=doodle --set enableIPForwarding=false', checks=[
            self.check('enableIPForwarding', False),
            self.check('dnsSettings.internalDnsNameLabel', 'doodle')
        ])

        self.cmd('network nic delete --resource-group {rg} --name {nic}')
        self.cmd('network nic list -g {rg}', checks=self.is_empty())


class NetworkNicSubresourceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_nic_subresource')
    def test_network_nic_subresources(self, resource_group):

        self.kwargs['nic'] = 'nic1'

        self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1')
        self.cmd('network nic create -g {rg} -n {nic} --subnet subnet1 --vnet-name vnet1')
        self.cmd('network nic ip-config list -g {rg} --nic-name {nic}',
                 checks=self.check('length(@)', 1))
        self.cmd('network nic ip-config show -g {rg} --nic-name {nic} -n ipconfig1', checks=[
            self.check('name', 'ipconfig1'),
            self.check('privateIPAllocationMethod', 'Dynamic')
        ])
        self.cmd('network nic ip-config create -g {rg} --nic-name {nic} -n ipconfig2 --make-primary',
                 checks=self.check('primary', True))
        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n ipconfig1 --make-primary',
                 checks=self.check('primary', True))
        self.cmd('network nic ip-config delete -g {rg} --nic-name {nic} -n ipconfig2')

        # test various sets
        self.kwargs.update({
            'vnet': 'vnet2',
            'subnet': 'subnet2',
            'ip': 'publicip2',
            'lb': 'lb1',
            'config': 'ipconfig1'
        })
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.cmd('network public-ip create -g {rg} -n {ip}')
        self.kwargs['ip_id'] = self.cmd('network public-ip show -g {rg} -n {ip}').get_output_in_json()['id']
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule1 --protocol tcp --frontend-port 100 --backend-port 100 --frontend-ip-name LoadBalancerFrontEnd')
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule2 --protocol tcp --frontend-port 200 --backend-port 200 --frontend-ip-name LoadBalancerFrontEnd')
        self.kwargs['rule1_id'] = self.cmd('network lb inbound-nat-rule show -g {rg} --lb-name {lb} -n rule1').get_output_in_json()['id']
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap1')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap2')
        self.kwargs['bap1_id'] = self.cmd('network lb address-pool show -g {rg} --lb-name {lb} -n bap1').get_output_in_json()['id']

        self.kwargs['private_ip'] = '10.0.0.15'
        # test ability to set load balancer IDs
        # includes the default backend pool
        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --lb-name {lb} --lb-address-pools {bap1_id} bap2 --lb-inbound-nat-rules {rule1_id} rule2 --private-ip-address {private_ip}', checks=[
            self.check('length(loadBalancerBackendAddressPools)', 2),
            self.check('length(loadBalancerInboundNatRules)', 2),
            self.check('privateIPAddress', '{private_ip}'),
            self.check('privateIPAllocationMethod', 'Static')])
        # test generic update
        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --set privateIPAddress=10.0.0.50',
                 checks=self.check('privateIPAddress', '10.0.0.50'))

        # test ability to add and remove IDs one at a time with subcommands
        self.cmd('network nic ip-config inbound-nat-rule remove -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --inbound-nat-rule rule1')
        self.cmd('network nic ip-config inbound-nat-rule add -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --inbound-nat-rule rule1',
                 checks=self.check('length(loadBalancerInboundNatRules)', 2))

        self.cmd('network nic ip-config address-pool remove -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --address-pool bap1')
        self.cmd('network nic ip-config address-pool add -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --address-pool bap1',
                 checks=self.check('length(loadBalancerBackendAddressPools)', 2))

        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --private-ip-address "" --public-ip-address {ip_id}', checks=[
            self.check('privateIPAllocationMethod', 'Dynamic'),
            self.check("publicIPAddress.contains(id, '{ip_id}')", True)
        ])

        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --subnet {subnet} --vnet-name {vnet}',
                 checks=self.check("subnet.contains(id, '{subnet}')", True))


class NetworkNicConvenienceCommandsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_nic_convenience_test', location='eastus')
    def test_network_nic_convenience_commands(self, resource_group):

        self.kwargs['vm'] = 'conveniencevm1'
        self.cmd('vm create -g {rg} -n {vm} --image Canonical:UbuntuServer:18.04-LTS:latest --admin-username myusername --admin-password aBcD1234!@#$ --authentication-type password')
        self.kwargs['nic_id'] = self.cmd('vm show -g {rg} -n {vm} --query "networkProfile.networkInterfaces[0].id"').get_output_in_json()
        self.cmd('network nic list-effective-nsg --ids {nic_id}',
                 checks=self.greater_than('length(@)', 0))
        self.cmd('network nic show-effective-route-table --ids {nic_id}',
                 checks=self.greater_than('length(@)', 0))


class NetworkPublicIpWithSku(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_sku')
    def test_network_public_ip_sku(self, resource_group):

        self.kwargs.update({
            'standard_sku': 'Standard',
            'basic_sku': 'Basic',
            'location': 'eastus2',
            'ip1': 'pubip1',
            'ip2': 'pubip2',
            'ip3': 'pubip3',
            'ip4': 'pubip4'
        })

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip1}')
        self.cmd('network public-ip show -g {rg} -n {ip1}', checks=[
            self.check('sku.name', self.kwargs.get('basic_sku')),
            self.check('publicIPAllocationMethod', 'Dynamic')
        ])

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip2} --sku {standard_sku} --tags foo=doo')
        self.cmd('network public-ip show -g {rg} -n {ip2}', checks=[
            self.check('sku.name', self.kwargs.get('standard_sku')),
            self.check('publicIPAllocationMethod', 'Static'),
            self.check('tags.foo', 'doo')
        ])

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip3} --sku {standard_sku}')
        self.cmd('network public-ip show -g {rg} -n {ip3}', checks=[
            self.check('sku.name', self.kwargs.get('standard_sku')),
            self.check('publicIPAllocationMethod', 'Static')
        ])


class NetworkZonedPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_zoned_public_ip')
    def test_network_zoned_public_ip(self, resource_group):
        self.kwargs['ip'] = 'pubip'
        self.cmd('network public-ip create -g {rg} -n {ip} -l centralus -z 2 --sku standard',
                 checks=self.check('publicIp.zones[0]', '2'))

        self.cmd(
            'network public-ip show -g {rg} -n {ip}',
            checks=[
                self.check('name', '{ip}'),
                self.check('publicIPAddressVersion', 'IPv4')
            ]
        )


class NetworkPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_public_ip')
    def test_network_public_ip(self, resource_group):
        self.kwargs.update({
            'ip1': 'pubipdns',
            'ip2': 'pubipnodns',
            'ip3': 'pubip3',
            'dns': 'woot1',
            'zone': '1',
            'location': 'eastus2',
            'ip_tags': 'RoutingPreference=Internet',
            'version': 'ipv4',
            'sku': 'standard'
        })
        self.cmd('network public-ip create -g {rg} -n {ip1} --dns-name {dns} --allocation-method static', checks=[
            self.check('publicIp.provisioningState', 'Succeeded'),
            self.check('publicIp.publicIPAllocationMethod', 'Static'),
            self.check('publicIp.dnsSettings.domainNameLabel', '{dns}')
        ])
        self.cmd('network public-ip create -g {rg} -n {ip2}', checks=[
            self.check('publicIp.provisioningState', 'Succeeded'),
            self.check('publicIp.publicIPAllocationMethod', 'Dynamic'),
            self.check('publicIp.dnsSettings', None)
        ])

        self.cmd(
            'network public-ip update -g {rg} -n {ip2} --allocation-method static --dns-name wowza2 --idle-timeout 10 --tags foo=doo',
            checks=[
                self.check('publicIPAllocationMethod', 'Static'),
                self.check('dnsSettings.domainNameLabel', 'wowza2'),
                self.check('idleTimeoutInMinutes', 10),
                self.check('tags.foo', 'doo')
            ])

        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])

        self.cmd('network public-ip show -g {rg} -n {ip1}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{ip1}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('network public-ip delete -g {rg} -n {ip1}')
        self.cmd('network public-ip list -g {rg}',
                 checks=self.check("length[?name == '{ip1}']", None))

    @ResourceGroupPreparer(name_prefix='cli_test_public_ip_zone', location='eastus2')
    def test_network_public_ip_zone(self, resource_group):
        self.cmd('network public-ip create -g {rg} -n ip --sku Standard -z 1', checks=[
            self.check('length(publicIp.zones)', 1)
        ])


class NetworkExtendedNSGScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_extended_nsg')
    def test_network_extended_nsg(self, resource_group):

        self.kwargs.update({
            'nsg': 'nsg1',
            'rule': 'rule1'
        })
        self.cmd('network nsg create --name {nsg} -g {rg}')
        self.cmd('network nsg rule create --access allow --destination-address-prefixes 10.0.0.0/24 11.0.0.0/24 --direction inbound --nsg-name {nsg} -g {rg} --source-address-prefixes * -n {rule} --source-port-ranges 700-900 1000-1100 --priority 1000', checks=[
            self.check('length(destinationAddressPrefixes)', 2),
            self.check('destinationAddressPrefix', None),
            self.check('length(sourceAddressPrefixes)', 0),
            self.check('sourceAddressPrefix', '*'),
            self.check('length(sourcePortRanges)', 2),
            self.check('sourcePortRange', None),
            self.check('length(destinationPortRanges)', 0),
            self.check('destinationPortRange', '80')
        ])
        self.cmd('network nsg rule update --destination-address-prefixes Internet --nsg-name {nsg} -g {rg} --source-address-prefixes 10.0.0.0/24 11.0.0.0/24 -n {rule} --source-port-ranges * --destination-port-ranges 500-1000 2000 3000', checks=[
            self.check('length(destinationAddressPrefixes)', 0),
            self.check('destinationAddressPrefix', 'Internet'),
            self.check('length(sourceAddressPrefixes)', 2),
            self.check('sourceAddressPrefix', None),
            self.check('length(sourcePortRanges)', 0),
            self.check('sourcePortRange', '*'),
            self.check('length(destinationPortRanges)', 3),
            self.check('destinationPortRange', None)
        ])


class NetworkSecurityGroupScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_nsg')
    def test_network_nsg(self, resource_group):

        self.kwargs.update({
            'nsg': 'test-nsg1',
            'rule': 'web',
            'rt': 'Microsoft.Network/networkSecurityGroups'
        })

        self.cmd('network nsg create --name {nsg} -g {rg} --tags foo=doo')
        self.cmd('network nsg rule create --access allow --destination-address-prefixes 1234 --direction inbound --nsg-name {nsg} --protocol * -g {rg} --source-address-prefixes 789 -n {rule} --source-port-ranges * --destination-port-ranges 4444 --priority 1000')

        self.cmd('network nsg list', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True)
        ])
        self.cmd('network nsg list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
        self.cmd('network nsg show --resource-group {rg} --name {nsg}', checks=[
            self.check('type(@)', 'object'),
            self.check('type', '{rt}'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{nsg}')
        ])
        # Test for the manually added nsg rule
        self.cmd('network nsg rule list --resource-group {rg} --nsg-name {nsg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
        self.cmd('network nsg rule list --resource-group {rg} --nsg-name {nsg} -o table')
        self.cmd('network nsg rule show --resource-group {rg} --nsg-name {nsg} --name {rule}', checks=[
            self.check('type(@)', 'object'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{rule}')
        ])

        self.kwargs.update({
            'access': 'DENY',
            'prefix': '111',
            'dir': 'Outbound',
            'protocol': 'Tcp',
            'ports': '1234-1235',
            'desc': 'greatrule',
            'priority': 888
        })
        self.cmd('network nsg rule update -g {rg} --nsg-name {nsg} -n {rule} --direction {dir} --access {access} --destination-address-prefixes {prefix} --protocol {protocol} --source-address-prefixes {prefix} --source-port-ranges {ports} --destination-port-ranges {ports} --priority {priority} --description {desc}', checks=[
            self.check('access', 'Deny'),
            self.check('direction', '{dir}'),
            self.check('destinationAddressPrefix', '{prefix}'),
            self.check('protocol', '{protocol}'),
            self.check('sourceAddressPrefix', '{prefix}'),
            self.check('sourcePortRange', '{ports}'),
            self.check('priority', '{priority}'),
            self.check('description', '{desc}')
        ])

        # test generic update
        self.cmd('network nsg rule update -g {rg} --nsg-name {nsg} -n {rule} --set description="cool"',
                 checks=self.check('description', 'cool'))
