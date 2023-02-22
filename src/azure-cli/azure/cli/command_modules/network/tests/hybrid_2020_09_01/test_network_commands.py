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
            self.check('publicIpAllocationMethod', 'Static')
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


class NetworkLoadBalancerOutboundRulesScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_network_lb_outbound_rules', location='eastus2')
    def test_network_load_balancer_outbound_rules(self, resource_group, resource_group_location):

        self.kwargs.update({
            'loc': resource_group_location,
            'lb': 'lb1',
            'prefix': 'prefix1',
            'frontend1': 'LoadBalancerFrontEnd',
            'frontend2': 'prefixFrontEnd',
            'backend': 'lb1bepool',
            'rule1': 'rule1',
            'rule2': 'rule2'
        })

        self.cmd('network lb create -g {rg} -n {lb} --sku Standard')
        self.cmd('network public-ip prefix create -g {rg} -n {prefix} --length 30')
        self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb} -n {frontend2} --public-ip-prefix {prefix}')
        self.cmd('network lb outbound-rule create -g {rg} --lb-name {lb} -n {rule1} --address-pool {backend} --enable-tcp-reset --frontend-ip-configs {frontend1} --outbound-ports 512 --protocol Tcp', checks=[
            self.check('enableTcpReset', True),
            self.check('protocol', 'Tcp'),
            self.check('allocatedOutboundPorts', 512),
            self.check("contains(backendAddressPool.id, '{backend}')", True),
            self.check("contains(frontendIPConfigurations[0].id, '{frontend1}')", True)
        ])
        self.cmd('network lb outbound-rule create -g {rg} --lb-name {lb} -n {rule2} --address-pool {backend} --frontend-ip-configs {frontend2} --idle-timeout 20 --protocol all', checks=[
            self.check('idleTimeoutInMinutes', 20),
            self.check("contains(backendAddressPool.id, '{backend}')", True),
            self.check("contains(frontendIPConfigurations[0].id, '{frontend2}')", True)
        ])
        self.cmd('network lb outbound-rule update -g {rg} --lb-name {lb} -n {rule2} --idle-timeout 25',
                 checks=self.check('idleTimeoutInMinutes', 25))
        self.cmd('network lb outbound-rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))
        self.cmd('network lb outbound-rule show -g {rg} --lb-name {lb} -n {rule1}', checks=[
            self.check('enableTcpReset', True),
            self.check('protocol', 'Tcp'),
            self.check('allocatedOutboundPorts', 512),
            self.check("contains(backendAddressPool.id, '{backend}')", True),
            self.check("contains(frontendIPConfigurations[0].id, '{frontend1}')", True)
        ])
        self.cmd('network lb outbound-rule delete -g {rg} --lb-name {lb} -n {rule1}')
        self.cmd('network lb outbound-rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 1))


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
