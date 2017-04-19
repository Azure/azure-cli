# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
#pylint: disable=too-many-lines
import os
import unittest

from azure.cli.core.util import CLIError
from azure.cli.core.commands.arm import resource_id
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.test_utils.vcr_test_base import (VCRTestBase, ResourceGroupVCRTestBase, JMESPathCheck,
                                           NoneCheck, MOCKED_SUBSCRIPTION_ID)
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class NetworkMultiIdsShowScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkMultiIdsShowScenarioTest, self).__init__(__file__, test_method, resource_group='test_multi_id')

    def test_multi_id_show(self):
        self.execute()

    def set_up(self):
        super(NetworkMultiIdsShowScenarioTest, self).set_up()
        rg = self.resource_group

        self.cmd('network public-ip create -g {} -n pip1'.format(rg))
        self.cmd('network public-ip create -g {} -n pip2'.format(rg))

    def body(self):
        rg = self.resource_group

        pip1 = self.cmd('network public-ip show -g {} -n pip1'.format(rg))
        pip2 = self.cmd('network public-ip show -g {} -n pip2'.format(rg))
        self.cmd('network public-ip show --ids {} {}'.format(pip1['id'], pip2['id']),
            checks=JMESPathCheck('length(@)', 2))

class NetworkUsageListScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkUsageListScenarioTest, self).__init__(__file__, test_method)

    def test_network_usage_list(self):
        self.execute()

    def body(self):
        self.cmd('network list-usages --location westus', checks=JMESPathCheck('type(@)', 'array'))

class NetworkAppGatewayDefaultScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayDefaultScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_basic')

    def test_network_app_gateway_with_defaults(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        self.cmd('network application-gateway create -g {} -n ag1 --no-wait'.format(rg))
        self.cmd('network application-gateway wait -g {} -n ag1 --exists'.format(rg))
        self.cmd('network application-gateway update -g {} -n ag1 --no-wait --capacity 3 --sku standard_small --tags foo=doo'.format(rg))
        self.cmd('network application-gateway wait -g {} -n ag1 --created'.format(rg))
        self.cmd('network application-gateway list')

        ag_list = self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        ag_count = len(ag_list)

        self.cmd('network application-gateway show --resource-group {} --name ag1'.format(rg), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', 'ag1'),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('frontendIpConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheck("frontendIpConfigurations[0].subnet.contains(id, 'default')", True)
        ])
        self.cmd('network application-gateway show-backend-health -g {} -n ag1'.format(rg))
        self.cmd('network application-gateway stop --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway start --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway delete --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=JMESPathCheck('length(@)', ag_count - 1))

class NetworkAppGatewayExistingSubnetScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayExistingSubnetScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_existing_subnet')

    def test_network_app_gateway_with_existing_subnet(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        vnet = self.cmd('network vnet create -g {} -n vnet2 --subnet-name subnet1'.format(rg))
        subnet_id = vnet['newVNet']['subnets'][0]['id']

        with self.assertRaises(CLIError):
            # make sure it fails
            self.cmd('network application-gateway create -g {} -n ag2 --subnet {} --subnet-address-prefix 10.0.0.0/28'.format(rg, subnet_id), checks=[
                JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
                JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
            ])
        # now verify it succeeds
        self.cmd('network application-gateway create -g {} -n ag2 --subnet {} --servers 172.0.0.1 www.mydomain.com'.format(rg, subnet_id), checks=[
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
        ])

class NetworkAppGatewayNoWaitScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayNoWaitScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_no_wait')

    def test_network_app_gateway_no_wait(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        self.cmd('network application-gateway create -g {} -n ag1 --no-wait'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway create -g {} -n ag2 --no-wait'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway wait -g {} -n ag1 --created --interval 120'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway wait -g {} -n ag2 --created --interval 120'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway show -g {} -n ag1'.format(rg), checks=[
            JMESPathCheck('provisioningState', 'Succeeded')
            ])
        self.cmd('network application-gateway show -g {} -n ag2'.format(rg), checks=[
            JMESPathCheck('provisioningState', 'Succeeded')
            ])
        self.cmd('network application-gateway delete -g {} -n ag2 --no-wait'.format(rg))
        self.cmd('network application-gateway wait -g {} -n ag2 --deleted'.format(rg))

class NetworkAppGatewayPrivateIpScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayPrivateIpScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_private_ip')

    def test_network_app_gateway_with_private_ip(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        private_ip = '10.0.0.15'
        cert_path = os.path.join(TEST_DIR, 'TestCert.pfx')
        cert_pass = 'password'
        self.cmd('network application-gateway create -g {} -n ag3 --subnet subnet1 --private-ip-address {} --cert-file "{}" --cert-password {} --no-wait'.format(rg, private_ip, cert_path, cert_pass))
        self.cmd('network application-gateway wait -g {} -n ag3 --exists'.format(rg))
        self.cmd('network application-gateway show -g {} -n ag3'.format(rg), checks=[
            JMESPathCheck('frontendIpConfigurations[0].privateIpAddress', private_ip),
            JMESPathCheck('frontendIpConfigurations[0].privateIpAllocationMethod', 'Static')
        ])
        cert_path = os.path.join(TEST_DIR, 'TestCert2.pfx')
        self.cmd('network application-gateway ssl-cert update -g {} --gateway-name ag3 -n ag3SslCert --cert-file "{}" --cert-password {}'.format(rg, cert_path, cert_pass))
        self.cmd('network application-gateway wait -g {} -n ag3 --updated'.format(rg))
        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 --disabled-ssl-protocols tlsv1_0 tlsv1_1 --no-wait'.format(rg))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg),
            checks=JMESPathCheck('disabledSslProtocols.length(@)', 2))
        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 --clear --no-wait'.format(rg))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg),
            checks=NoneCheck())

class NetworkAppGatewayPublicIpScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayPublicIpScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_public_ip')

    def test_network_app_gateway_with_public_ip(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        public_ip_name = 'publicip4'
        self.cmd('network application-gateway create -g {} -n test4 --subnet subnet1 --vnet-name vnet4 --vnet-address-prefix 10.0.0.1/16 --subnet-address-prefix 10.0.0.1/28 --public-ip-address {}'.format(rg, public_ip_name), checks=[
            JMESPathCheck("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(public_ip_name), True),
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')
        ])

class NetworkAppGatewayWafScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayWafScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_waf')

    def test_network_app_gateway_waf(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        public_ip_name = 'pip1'
        self.cmd('network application-gateway create -g {} -n ag1 --subnet subnet1 --vnet-name vnet4 --public-ip-address {} --sku WAF_Medium'.format(rg, public_ip_name), checks=[
            JMESPathCheck("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(public_ip_name), True),
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')
        ])
        self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled true --firewall-mode detection --no-wait'.format(rg))
        self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[
            JMESPathCheck('enabled', True),
            JMESPathCheck('firewallMode', 'Detection')
        ])
        self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled true --firewall-mode prevention --no-wait'.format(rg))
        self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[
            JMESPathCheck('enabled', True),
            JMESPathCheck('firewallMode', 'Prevention')
        ])
        self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled false --no-wait'.format(rg))
        self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[
            JMESPathCheck('enabled', False),
            JMESPathCheck('firewallMode', 'Detection')
        ])

class NetworkPublicIpScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkPublicIpScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_public_ip')

    def test_network_public_ip(self):
        self.execute()

    def body(self):
        s = self
        public_ip_dns = 'pubipdns'
        public_ip_no_dns = 'pubipnodns'
        dns = 'woot'
        rg = s.resource_group
        s.cmd('network public-ip create -g {} -n {} --dns-name {} --allocation-method static'.format(rg, public_ip_dns, dns), checks=[
            JMESPathCheck('publicIp.provisioningState', 'Succeeded'),
            JMESPathCheck('publicIp.publicIpAllocationMethod', 'Static'),
            JMESPathCheck('publicIp.dnsSettings.domainNameLabel', dns)
        ])
        s.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip_no_dns), checks=[
            JMESPathCheck('publicIp.provisioningState', 'Succeeded'),
            JMESPathCheck('publicIp.publicIpAllocationMethod', 'Dynamic'),
            JMESPathCheck('publicIp.dnsSettings', None)
        ])
        s.cmd('network public-ip update -g {} -n {} --allocation-method static --dns-name wowza --idle-timeout 10'.format(rg, public_ip_no_dns), checks=[
            JMESPathCheck('publicIpAllocationMethod', 'Static'),
            JMESPathCheck('dnsSettings.domainNameLabel', 'wowza'),
            JMESPathCheck('idleTimeoutInMinutes', 10)
        ])

        s.cmd('network public-ip list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])

        s.cmd('network public-ip show -g {} -n {}'.format(rg, public_ip_dns), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', public_ip_dns),
            JMESPathCheck('resourceGroup', rg),
        ])

        s.cmd('network public-ip delete -g {} -n {}'.format(rg, public_ip_dns))
        s.cmd('network public-ip list -g {}'.format(rg),
            checks=JMESPathCheck("length[?name == '{}']".format(public_ip_dns), None))

class NetworkExpressRouteScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkExpressRouteScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_express_route')
        self.circuit_name = 'circuit1'
        self.resource_type = 'Microsoft.Network/expressRouteCircuits'

    def test_network_express_route(self):
        self.execute()

    def _test_express_route_peering(self):
        rg = self.resource_group
        circuit = self.circuit_name

        def _create_peering(peering, peer_asn, vlan, primary_prefix, seconary_prefix):
            self.cmd('network express-route peering create -g {} --circuit-name {} --peering-type {} --peer-asn {} --vlan-id {} --primary-peer-subnet {} --secondary-peer-subnet {}'.format(rg, circuit, peering, peer_asn, vlan, primary_prefix, seconary_prefix))

        # create public and private peerings
        _create_peering('AzurePublicPeering', 10000, 100, '100.0.0.0/30', '101.0.0.0/30')
        _create_peering('AzurePrivatePeering', 10001, 101, '102.0.0.0/30', '103.0.0.0/30')

        self.cmd('network express-route peering create -g {} --circuit-name {} --peering-type MicrosoftPeering --peer-asn 10002 --vlan-id 103 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30 --advertised-public-prefixes 104.0.0.0/30 --customer-asn 10000 --routing-registry-name level3'.format(rg, circuit),
            allowed_exceptions='not authorized for creating Microsoft Peering')
        self.cmd('network express-route peering show -g {} --circuit-name {} -n MicrosoftPeering'.format(rg, circuit), checks=[
            JMESPathCheck('microsoftPeeringConfig.advertisedPublicPrefixes[0]', '104.0.0.0/30'),
            JMESPathCheck('microsoftPeeringConfig.customerAsn', 10000),
            JMESPathCheck('microsoftPeeringConfig.routingRegistryName', 'LEVEL3')
        ])

        self.cmd('network express-route peering delete -g {} --circuit-name {} -n MicrosoftPeering'.format(rg, circuit))

        self.cmd('network express-route peering list --resource-group {} --circuit-name {}'.format(rg, circuit),
            checks=JMESPathCheck('length(@)', 2))

        self.cmd('network express-route peering update -g {} --circuit-name {} -n AzurePublicPeering --set vlanId=200'.format(rg, circuit),
                 checks=JMESPathCheck('vlanId', 200))

    def _test_express_route_auth(self):
        rg = self.resource_group
        circuit = self.circuit_name

        self.cmd('network express-route auth create -g {} --circuit-name {} -n auth1'.format(rg, circuit),
            checks=JMESPathCheck('authorizationUseStatus', 'Available'))

        self.cmd('network express-route auth list --resource-group {} --circuit-name {}'.format(rg, circuit),
            checks=JMESPathCheck('length(@)', 1))

        self.cmd('network express-route auth show -g {} --circuit-name {} -n auth1'.format(rg, circuit),
            checks=JMESPathCheck('authorizationUseStatus', 'Available'))

        self.cmd('network express-route auth delete -g {} --circuit-name {} -n auth1'.format(rg, circuit))

        self.cmd('network express-route auth list --resource-group {} --circuit-name {}'.format(rg, circuit), checks=NoneCheck())

    def body(self):

        rg = self.resource_group
        circuit = self.circuit_name

        self.cmd('network express-route list-service-providers', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format('Microsoft.Network/expressRouteServiceProviders'), True)
        ])

        # Premium SKU required to create MicrosoftPeering settings
        self.cmd('network express-route create -g {} -n {} --bandwidth 50 --provider "Microsoft ER Test" --peering-location Area51 --sku-tier Premium'.format(rg, circuit))
        self.cmd('network express-route list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)
        ])
        self.cmd('network express-route list --resource-group {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        self.cmd('network express-route show --resource-group {} --name {}'.format(rg, circuit), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', self.resource_type),
            JMESPathCheck('name', circuit),
            JMESPathCheck('resourceGroup', rg),
        ])
        self.cmd('network express-route get-stats --resource-group {} --name {}'.format(rg, circuit),
            checks=JMESPathCheck('type(@)', 'object'))

        self.cmd('network express-route update -g {} -n {} --set tags.test=Test'.format(rg, circuit),
            checks=JMESPathCheck('tags', {'test': 'Test'}))

        self._test_express_route_auth()

        self._test_express_route_peering()

        # because the circuit isn't actually provisioned, these commands will not return anything useful
        # so we will just verify that the command makes it through the SDK without error.
        self.cmd('network express-route list-arp-tables --resource-group {} --name {} --peering-name azureprivatepeering --path primary'.format(rg, circuit))
        self.cmd('network express-route list-route-tables --resource-group {} --name {} --peering-name azureprivatepeering --path primary'.format(rg, circuit))

        self.cmd('network express-route delete --resource-group {} --name {}'.format(rg, circuit))
        # Expecting no results as we just deleted the only express route in the resource group
        self.cmd('network express-route list --resource-group {}'.format(rg), checks=NoneCheck())

class NetworkLoadBalancerScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkLoadBalancerScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_load_balancer')
        self.lb_name = 'lb'
        self.resource_type = 'Microsoft.Network/loadBalancers'

    def test_network_load_balancer(self):
        self.execute()

    def body(self):
        # test lb create with min params (new ip)
        self.cmd('network lb create -n {}1 -g {}'.format(self.lb_name, self.resource_group), checks=[
            JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('loadBalancer.frontendIPConfigurations[0].resourceGroup', self.resource_group)
        ])

        # test internet facing load balancer with new static public IP
        self.cmd('network lb create -n {}2 -g {} --public-ip-address-allocation static'.format(self.lb_name, self.resource_group))
        self.cmd('network public-ip show -g {} -n PublicIP{}2'.format(self.resource_group, self.lb_name),
            checks=JMESPathCheck('publicIpAllocationMethod', 'Static'))

        # test internal load balancer create (existing subnet ID)
        vnet_name = 'mytestvnet'
        private_ip = '10.0.0.15'
        vnet = self.cmd('network vnet create -n {} -g {} --subnet-name default'.format(vnet_name, self.resource_group))
        subnet_id = vnet['newVNet']['subnets'][0]['id']
        self.cmd('network lb create -n {}3 -g {} --subnet {} --private-ip-address {}'.format(
            self.lb_name, self.resource_group, subnet_id, private_ip), checks=[
                JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Static'),
                JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAddress', private_ip),
                JMESPathCheck('loadBalancer.frontendIPConfigurations[0].resourceGroup', self.resource_group),
                JMESPathCheck("loadBalancer.frontendIPConfigurations[0].properties.subnet.id", subnet_id)
            ])

        # test internet facing load balancer with existing public IP (by name)
        pub_ip_name = 'publicip4'
        self.cmd('network public-ip create -n {} -g {}'.format(pub_ip_name, self.resource_group))
        self.cmd('network lb create -n {}4 -g {} --public-ip-address {}'.format(
            self.lb_name, self.resource_group, pub_ip_name), checks=[
                JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
                JMESPathCheck('loadBalancer.frontendIPConfigurations[0].resourceGroup', self.resource_group),
                JMESPathCheck("loadBalancer.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(pub_ip_name), True)
            ])

        self.cmd('network lb list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)
        ])
        self.cmd('network lb list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network lb show --resource-group {} --name {}1'.format(self.resource_group, self.lb_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', self.resource_type),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('name', '{}1'.format(self.lb_name))
        ])
        self.cmd('network lb delete --resource-group {} --name {}1'.format(self.resource_group, self.lb_name))
        # Expecting no results as we just deleted the only lb in the resource group
        self.cmd('network lb list --resource-group {}'.format(self.resource_group), checks=JMESPathCheck('length(@)', 3))

class NetworkLoadBalancerIpConfigScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkLoadBalancerIpConfigScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_load_balancer_ip_config')

    def test_network_load_balancer_ip_config(self):
        self.execute()

    def set_up(self):
        super(NetworkLoadBalancerIpConfigScenarioTest, self).set_up()

        rg = self.resource_group

        for i in range(1, 4): # create 3 public IPs to use for the test
            self.cmd('network public-ip create -g {} -n publicip{}'.format(rg, i))

        # create internet-facing LB with public IP (lb1)
        self.cmd('network lb create -g {} -n lb1 --public-ip-address publicip1'.format(rg))

        # create internal LB (lb2)
        self.cmd('network vnet create -g {} -n vnet1 --subnet-name subnet1'.format(rg))
        self.cmd('network vnet subnet create -g {} --vnet-name vnet1 -n subnet2 --address-prefix 10.0.1.0/24'.format(rg))
        self.cmd('network lb create -g {} -n lb2 --subnet subnet1 --vnet-name vnet1'.format(rg))

    def body(self):
        rg = self.resource_group

        # Test frontend IP configuration for internet-facing LB
        self.cmd('network lb frontend-ip create -g {} --lb-name lb1 -n ipconfig1 --public-ip-address publicip2'.format(rg))
        self.cmd('network lb frontend-ip list -g {} --lb-name lb1'.format(rg), checks=JMESPathCheck('length(@)', 2))
        self.cmd('network lb frontend-ip update -g {} --lb-name lb1 -n ipconfig1 --public-ip-address publicip3'.format(rg))
        self.cmd('network lb frontend-ip show -g {} --lb-name lb1 -n ipconfig1'.format(rg),
            checks=JMESPathCheck("publicIpAddress.contains(id, 'publicip3')", True))

        # test generic update
        subscription_id = MOCKED_SUBSCRIPTION_ID if self.playback else get_subscription_id()
        ip2_id = resource_id(subscription=subscription_id, resource_group=self.resource_group, namespace='Microsoft.Network', type='publicIPAddresses', name='publicip2')
        self.cmd('network lb frontend-ip update -g {} --lb-name lb1 -n ipconfig1 --set publicIpAddress.id="{}"'.format(rg, ip2_id),
            checks=JMESPathCheck("publicIpAddress.contains(id, 'publicip2')", True))
        self.cmd('network lb frontend-ip delete -g {} --lb-name lb1 -n ipconfig1'.format(rg))
        self.cmd('network lb frontend-ip list -g {} --lb-name lb1'.format(rg), checks=JMESPathCheck('length(@)', 1))

        # Test frontend IP configuration for internal LB
        self.cmd('network lb frontend-ip create -g {} --lb-name lb2 -n ipconfig2 --vnet-name vnet1 --subnet subnet1 --private-ip-address 10.0.0.99'.format(rg))
        self.cmd('network lb frontend-ip list -g {} --lb-name lb2'.format(rg), checks=JMESPathCheck('length(@)', 2))
        self.cmd('network lb frontend-ip update -g {} --lb-name lb2 -n ipconfig2 --subnet subnet2 --vnet-name vnet1 --private-ip-address 10.0.1.100'.format(rg))
        self.cmd('network lb frontend-ip show -g {} --lb-name lb2 -n ipconfig2'.format(rg),
            checks=JMESPathCheck("subnet.contains(id, 'subnet2')", True))

class NetworkLoadBalancerSubresourceScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkLoadBalancerSubresourceScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_load_balancer_subresource')
        self.lb_name = 'lb1'

    def test_network_load_balancer_subresources(self):
        self.execute()

    def set_up(self):
        super(NetworkLoadBalancerSubresourceScenarioTest, self).set_up()
        rg = self.resource_group
        lb = self.lb_name
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

    def body(self): # pylint: disable=too-many-statements
        rg = self.resource_group
        lb = self.lb_name
        lb_rg = '-g {} --lb-name {}'.format(rg, lb)

        # Test inbound NAT rules
        for count in range(1, 4):
            self.cmd('network lb inbound-nat-rule create {} -n rule{} --protocol tcp --frontend-port {} --backend-port {} --frontend-ip-name LoadBalancerFrontEnd'.format(lb_rg, count, count, count))
        self.cmd('network lb inbound-nat-rule list {}'.format(lb_rg),
            checks=JMESPathCheck('length(@)', 3))
        self.cmd('network lb inbound-nat-rule update {} -n rule1 --floating-ip true --idle-timeout 10'.format(lb_rg))
        self.cmd('network lb inbound-nat-rule show {} -n rule1'.format(lb_rg), checks=[
            JMESPathCheck('enableFloatingIp', True),
            JMESPathCheck('idleTimeoutInMinutes', 10)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-rule update {} -n rule1 --set idleTimeoutInMinutes=5'.format(lb_rg),
            checks=JMESPathCheck('idleTimeoutInMinutes', 5))

        for count in range(1, 4):
            self.cmd('network lb inbound-nat-rule delete {} -n rule{}'.format(lb_rg, count))
        self.cmd('network lb inbound-nat-rule list {}'.format(lb_rg),
            checks=JMESPathCheck('length(@)', 0))

        # Test inbound NAT pools
        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool create {} -n rule{} --protocol tcp --frontend-port-range-start {}  --frontend-port-range-end {} --backend-port {}'.format(lb_rg, count, count, count+999, count))
        self.cmd('network lb inbound-nat-pool list {}'.format(lb_rg),
            checks=JMESPathCheck('length(@)', 3))
        self.cmd('network lb inbound-nat-pool update {} -n rule1000 --protocol udp --backend-port 50'.format(lb_rg))
        self.cmd('network lb inbound-nat-pool show {} -n rule1000'.format(lb_rg), checks=[
            JMESPathCheck('protocol', 'Udp'),
            JMESPathCheck('backendPort', 50)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-pool update {} -n rule1000 --set protocol=Tcp'.format(lb_rg),
            checks=JMESPathCheck('protocol', 'Tcp'))

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool delete {} -n rule{}'.format(lb_rg, count))
        self.cmd('network lb inbound-nat-pool list {}'.format(lb_rg),
            checks=JMESPathCheck('length(@)', 0))

        # Test backend address pool
        for i in range(1, 4):
            self.cmd('network lb address-pool create {} -n bap{}'.format(lb_rg, i),
                checks=JMESPathCheck('name', 'bap{}'.format(i)))
        self.cmd('network lb address-pool list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 4))
        self.cmd('network lb address-pool show {} -n bap1'.format(lb_rg),
            checks=JMESPathCheck('name', 'bap1'))
        self.cmd('network lb address-pool delete {} -n bap3'.format(lb_rg), checks=NoneCheck())
        self.cmd('network lb address-pool list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 3))

        # Test probes
        for i in range(1, 4):
            self.cmd('network lb probe create {} -n probe{} --port {} --protocol http --path "/test{}"'.format(lb_rg, i, i, i))
        self.cmd('network lb probe list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 3))
        self.cmd('network lb probe update {} -n probe1 --interval 20 --threshold 5'.format(lb_rg))
        self.cmd('network lb probe update {} -n probe2 --protocol tcp --path ""'.format(lb_rg))
        self.cmd('network lb probe show {} -n probe1'.format(lb_rg), checks=[
            JMESPathCheck('intervalInSeconds', 20),
            JMESPathCheck('numberOfProbes', 5)
        ])
        # test generic update
        self.cmd('network lb probe update {} -n probe1 --set intervalInSeconds=15 --set numberOfProbes=3'.format(lb_rg), checks=[
            JMESPathCheck('intervalInSeconds', 15),
            JMESPathCheck('numberOfProbes', 3)
        ])

        self.cmd('network lb probe show {} -n probe2'.format(lb_rg), checks=[
            JMESPathCheck('protocol', 'Tcp'),
            JMESPathCheck('path', None)
        ])
        self.cmd('network lb probe delete {} -n probe3'.format(lb_rg))
        self.cmd('network lb probe list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 2))

        # Test load balancing rules
        self.cmd('network lb rule create {} -n rule1 --frontend-ip-name LoadBalancerFrontEnd --frontend-port 40 --backend-pool-name bap1 --backend-port 40 --protocol tcp'.format(lb_rg))
        self.cmd('network lb rule create {} -n rule2 --frontend-ip-name LoadBalancerFrontEnd --frontend-port 60 --backend-pool-name bap1 --backend-port 60 --protocol tcp'.format(lb_rg))
        self.cmd('network lb rule list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 2))
        self.cmd('network lb rule update {} -n rule1 --floating-ip true --idle-timeout 20 --load-distribution sourceip --protocol udp'.format(lb_rg))
        self.cmd('network lb rule update {} -n rule2 --backend-pool-name bap2 --load-distribution sourceipprotocol'.format(lb_rg))
        self.cmd('network lb rule show {} -n rule1'.format(lb_rg), checks=[
            JMESPathCheck('enableFloatingIp', True),
            JMESPathCheck('idleTimeoutInMinutes', 20),
            JMESPathCheck('loadDistribution', 'SourceIP'),
            JMESPathCheck('protocol', 'Udp')
        ])
        # test generic update
        self.cmd('network lb rule update {} -n rule1 --set idleTimeoutInMinutes=5'.format(lb_rg),
            checks=JMESPathCheck('idleTimeoutInMinutes', 5))

        self.cmd('network lb rule show {} -n rule2'.format(lb_rg), checks=[
            JMESPathCheck("backendAddressPool.contains(id, 'bap2')", True),
            JMESPathCheck('loadDistribution', 'SourceIPProtocol')
        ])
        self.cmd('network lb rule delete {} -n rule1'.format(lb_rg))
        self.cmd('network lb rule delete {} -n rule2'.format(lb_rg))
        self.cmd('network lb rule list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 0))

class NetworkLocalGatewayScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkLocalGatewayScenarioTest, self).__init__(__file__, test_method, resource_group='local_gateway_scenario')
        self.name = 'cli-test-loc-gateway'
        self.resource_type = 'Microsoft.Network/localNetworkGateways'

    def test_network_local_gateway(self):
        self.execute()

    def body(self):
        self.cmd('network local-gateway create --resource-group {} --name {} --gateway-ip-address 10.1.1.1'.format(self.resource_group, self.name))
        self.cmd('network local-gateway list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network local-gateway show --resource-group {} --name {}'.format(self.resource_group, self.name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', self.resource_type),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('name', self.name)
        ])
        try:
            self.cmd('network local-gateway delete --resource-group {} --name {}'.format(self.resource_group, self.name))
            # Expecting no results as we just deleted the only local gateway in the resource group
            self.cmd('network local-gateway list --resource-group {}'.format(self.resource_group), checks=NoneCheck())
        except CLIError:
            # TODO: Remove this once https://github.com/Azure/azure-cli/issues/2373 is fixed
            pass

class NetworkNicScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_nic_scenario')

    def test_network_nic(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        nic = 'cli-test-nic'
        rt = 'Microsoft.Network/networkInterfaces'
        subnet = 'mysubnet'
        vnet = 'myvnet'
        nsg = 'mynsg'
        alt_nsg = 'myothernsg'
        lb = 'mylb'
        private_ip = '10.0.0.15'
        public_ip_name = 'publicip1'

        subnet_id = self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, vnet, subnet))['newVNet']['subnets'][0]['id']
        self.cmd('network nsg create -g {} -n {}'.format(rg, nsg))
        nsg_id = self.cmd('network nsg show -g {} -n {}'.format(rg, nsg))['id']
        self.cmd('network nsg create -g {} -n {}'.format(rg, alt_nsg))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip_name))
        public_ip_id = self.cmd('network public-ip show -g {} -n {}'.format(rg, public_ip_name))['id']
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule1 --protocol tcp --frontend-port 100 --backend-port 100 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule2 --protocol tcp --frontend-port 200 --backend-port 200 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        rule_ids = ' '.join(self.cmd('network lb inbound-nat-rule list -g {} --lb-name {} --query "[].id"'.format(rg, lb)))
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap1'.format(rg, lb))
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap2'.format(rg, lb))
        address_pool_ids = ' '.join(self.cmd('network lb address-pool list -g {} --lb-name {} --query "[].id"'.format(rg, lb)))

        # create with minimum parameters
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {}'.format(rg, nic, subnet, vnet), checks=[
            JMESPathCheck('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheck('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise optional parameters
        self.cmd('network nic create -g {} -n {} --subnet {} --ip-forwarding --private-ip-address {} --public-ip-address {} --internal-dns-name test --lb-address-pools {} --lb-inbound-nat-rules {}'.format(rg, nic, subnet_id, private_ip, public_ip_name, address_pool_ids, rule_ids), checks=[
            JMESPathCheck('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Static'),
            JMESPathCheck('NewNIC.ipConfigurations[0].privateIpAddress', private_ip),
            JMESPathCheck('NewNIC.enableIpForwarding', True),
            JMESPathCheck('NewNIC.provisioningState', 'Succeeded'),
            JMESPathCheck('NewNIC.dnsSettings.internalDnsNameLabel', 'test')
        ])
        # exercise creating with NSG
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {} --network-security-group {}'.format(rg, nic, subnet, vnet, nsg), checks=[
            JMESPathCheck('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheck('NewNIC.enableIpForwarding', False),
            JMESPathCheck("NewNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheck('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise creating with NSG and Public IP
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {} --network-security-group {} --public-ip-address {}'.format(rg, nic, subnet, vnet, nsg_id, public_ip_id), checks=[
            JMESPathCheck('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheck('NewNIC.enableIpForwarding', False),
            JMESPathCheck("NewNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheck('NewNIC.provisioningState', 'Succeeded')
        ])
        self.cmd('network nic list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?contains(id, 'networkInterfaces')]) == length(@)", True)
        ])
        self.cmd('network nic list --resource-group {}'.format(rg), checks=[

            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(rt), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        self.cmd('network nic show --resource-group {} --name {}'.format(rg, nic), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', rt),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('name', nic)
        ])
        self.cmd('network nic update -g {} -n {} --internal-dns-name noodle --ip-forwarding true --network-security-group {}'.format(rg, nic, alt_nsg), checks=[
            JMESPathCheck('enableIpForwarding', True),
            JMESPathCheck('dnsSettings.internalDnsNameLabel', 'noodle'),
            JMESPathCheck("networkSecurityGroup.contains(id, '{}')".format(alt_nsg), True),
        ])
        # test generic update
        self.cmd('network nic update -g {} -n {} --set dnsSettings.internalDnsNameLabel=doodle --set enableIpForwarding=false'.format(rg, nic), checks=[
            JMESPathCheck('enableIpForwarding', False),
            JMESPathCheck('dnsSettings.internalDnsNameLabel', 'doodle')
        ])

        self.cmd('network nic delete --resource-group {} --name {}'.format(rg, nic))
        self.cmd('network nic list -g {}'.format(rg), checks=NoneCheck())

class NetworkNicSubresourceScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicSubresourceScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_nic_subresource')

    def test_network_nic_subresources(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        nic = 'nic1'

        self.cmd('network vnet create -g {} -n vnet1 --subnet-name subnet1'.format(rg))
        self.cmd('network nic create -g {} -n {} --subnet subnet1 --vnet-name vnet1'.format(rg, nic))
        self.cmd('network nic ip-config list -g {} --nic-name {}'.format(rg, nic),
            checks=JMESPathCheck('length(@)', 1))
        self.cmd('network nic ip-config show -g {} --nic-name {} -n ipconfig1'.format(rg, nic), checks=[
            JMESPathCheck('name', 'ipconfig1'),
            JMESPathCheck('privateIpAllocationMethod', 'Dynamic')
        ])
        self.cmd('network nic ip-config create -g {} --nic-name {} -n ipconfig2 --make-primary'.format(rg, nic), checks=[
            JMESPathCheck('primary', True)
        ])
        self.cmd('network nic ip-config update -g {} --nic-name {} -n ipconfig1 --make-primary'.format(rg, nic), checks=[
            JMESPathCheck('primary', True)
        ])
        self.cmd('network nic ip-config delete -g {} --nic-name {} -n ipconfig2'.format(rg, nic))

        # test various sets
        vnet = 'vnet2'
        subnet = 'subnet2'
        public_ip = 'publicip2'
        lb = 'lb1'
        config = 'ipconfig1'
        self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, vnet, subnet))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip))
        public_ip_id = self.cmd('network public-ip show -g {} -n {}'.format(rg, public_ip))['id']
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule1 --protocol tcp --frontend-port 100 --backend-port 100 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule2 --protocol tcp --frontend-port 200 --backend-port 200 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        rule1_id = self.cmd('network lb inbound-nat-rule show -g {} --lb-name {} -n rule1'.format(rg, lb))['id']
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap1'.format(rg, lb))
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap2'.format(rg, lb))
        bap1_id = self.cmd('network lb address-pool show -g {} --lb-name {} -n bap1'.format(rg, lb))['id']

        private_ip = '10.0.0.15'
        # test ability to set load balancer IDs
        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --lb-name {} --lb-address-pools {} bap2 --lb-inbound-nat-rules {} rule2 --private-ip-address {}'.format(rg, nic, config, lb, bap1_id, rule1_id, private_ip), checks=[
            JMESPathCheck('length(loadBalancerBackendAddressPools)', 2), # includes the default backend pool
            JMESPathCheck('length(loadBalancerInboundNatRules)', 2),
            JMESPathCheck('privateIpAddress', private_ip),
            JMESPathCheck('privateIpAllocationMethod', 'Static')
        ])
        # test generic update
        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --set privateIpAddress=10.0.0.50'.format(rg, nic, config),
            checks=JMESPathCheck('privateIpAddress', '10.0.0.50'))

        # test ability to add and remove IDs one at a time with subcommands
        self.cmd('network nic ip-config inbound-nat-rule remove -g {} --lb-name {} --nic-name {} --ip-config-name {} --inbound-nat-rule rule1'.format(rg, lb, nic, config),
            checks=JMESPathCheck('length(loadBalancerInboundNatRules)', 1))
        self.cmd('network nic ip-config inbound-nat-rule add -g {} --lb-name {} --nic-name {} --ip-config-name {} --inbound-nat-rule rule1'.format(rg, lb, nic, config),
            checks=JMESPathCheck('length(loadBalancerInboundNatRules)', 2))

        self.cmd('network nic ip-config address-pool remove -g {} --lb-name {} --nic-name {} --ip-config-name {} --address-pool bap1'.format(rg, lb, nic, config),
            checks=JMESPathCheck('length(loadBalancerBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool add -g {} --lb-name {} --nic-name {} --ip-config-name {} --address-pool bap1'.format(rg, lb, nic, config),
            checks=JMESPathCheck('length(loadBalancerBackendAddressPools)', 2))

        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --private-ip-address "" --public-ip-address {}'.format(rg, nic, config, public_ip_id), checks=[
            JMESPathCheck('privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheck("publicIpAddress.contains(id, '{}')".format(public_ip), True)
        ])

        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --subnet {} --vnet-name {}'.format(rg, nic, config, subnet, vnet),
            checks=JMESPathCheck("subnet.contains(id, '{}')".format(subnet), True))

class NetworkNicConvenienceCommandsScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicConvenienceCommandsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_nic_convenience_test')
        self.vm_name = 'conveniencevm1'

    def test_network_nic_convenience_commands(self):
        self.execute()

    def set_up(self):
        super(NetworkNicConvenienceCommandsScenarioTest, self).set_up()
        rg = self.resource_group
        vm = self.vm_name
        self.cmd('vm create -g {} -n {} --image UbuntuLTS --admin-username myusername --admin-password aBcD1234!@#$ --authentication-type password'.format(rg, vm))

    def body(self):
        rg = self.resource_group
        vm = self.vm_name
        nic_id = self.cmd('vm show -g {} -n {} --query "networkProfile.networkInterfaces[0].id"'.format(rg, vm))
        result = self.cmd('network nic list-effective-nsg --ids {}'.format(nic_id))
        self.assertTrue(len(result['value']) > 0)
        result = self.cmd('network nic show-effective-route-table --ids {}'.format(nic_id))
        self.assertTrue(len(result['value']) > 0)

class NetworkSecurityGroupScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkSecurityGroupScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_nsg')
        self.nsg_name = 'test-nsg1'
        self.nsg_rule_name = 'web'
        self.resource_type = 'Microsoft.Network/networkSecurityGroups'

    def test_network_nsg(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        nsg = self.nsg_name
        nrn = self.nsg_rule_name
        rt = self.resource_type

        self.cmd('network nsg create --name {} -g {}'.format(nsg, rg))
        self.cmd('network nsg rule create --access allow --destination-address-prefix 1234 --direction inbound --nsg-name {} --protocol * -g {} --source-address-prefix 789 -n {} --source-port-range * --destination-port-range 4444 --priority 1000'.format(nsg, rg, nrn))

        self.cmd('network nsg list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(rt), True)
        ])
        self.cmd('network nsg list --resource-group {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(rt), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        self.cmd('network nsg show --resource-group {} --name {}'.format(rg, nsg), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('type', rt),
                JMESPathCheck('resourceGroup', rg),
                JMESPathCheck('name', nsg)
        ])
        # Test for the manually added nsg rule
        self.cmd('network nsg rule list --resource-group {} --nsg-name {}'.format(rg, nsg), checks=[
                JMESPathCheck('type(@)', 'array'),
                JMESPathCheck('length(@)', 1),
                JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        self.cmd('network nsg rule show --resource-group {} --nsg-name {} --name {}'.format(rg, nsg, nrn), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('resourceGroup', rg),
                JMESPathCheck('name', nrn)
        ])

        #Test for updating the rule
        new_access = 'DENY'
        new_addr_prefix = '111'
        new_direction = 'Outbound'
        new_protocol = 'Tcp'
        new_port_range = '1234-1235'
        description = 'greatrule'
        priority = 888
        self.cmd('network nsg rule update -g {} --nsg-name {} -n {} --direction {} --access {} --destination-address-prefix {} --protocol {} --source-address-prefix {} --source-port-range {} --destination-port-range {} --priority {} --description {}'.format(
            rg, nsg, nrn, new_direction, new_access, new_addr_prefix, new_protocol, new_addr_prefix, new_port_range, new_port_range, priority, description),
                 checks=[
                     JMESPathCheck('access', 'Deny'),
                     JMESPathCheck('direction', new_direction),
                     JMESPathCheck('destinationAddressPrefix', new_addr_prefix),
                     JMESPathCheck('protocol', new_protocol),
                     JMESPathCheck('sourceAddressPrefix', new_addr_prefix),
                     JMESPathCheck('sourcePortRange', new_port_range),
                     JMESPathCheck('priority', priority),
                     JMESPathCheck('description', description),
                     ])

        # test generic update
        self.cmd('network nsg rule update -g {} --nsg-name {} -n {} --set description="cool"'.format(rg, nsg, nrn),
            checks=JMESPathCheck('description', 'cool'))

        self.cmd('network nsg rule delete --resource-group {} --nsg-name {} --name {}'.format(rg, nsg, nrn))
        # Delete the network security group
        self.cmd('network nsg delete --resource-group {} --name {}'.format(rg, nsg))
        # Expecting no results as we just deleted the only security group in the resource group
        self.cmd('network nsg list --resource-group {}'.format(rg), checks=NoneCheck())

class NetworkRouteTableOperationScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkRouteTableOperationScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_route_table')
        self.route_table_name = 'cli-test-route-table'
        self.route_name = 'my-route'
        self.resource_type = 'Microsoft.Network/routeTables'

    def test_network_route_table_operation(self):
        self.execute()

    def body(self):
        self.cmd('network route-table create -n {} -g {}'.format(self.route_table_name, self.resource_group))
        self.cmd('network route-table route create --address-prefix 10.0.5.0/24 -n {} -g {} --next-hop-type None'
                 ' --route-table-name {}'.format(self.route_name, self.resource_group, self.route_table_name))

        self.cmd('network route-table list',
            checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network route-table list --resource-group {}'.format(self.resource_group), checks=[
                JMESPathCheck('type(@)', 'array'),
                JMESPathCheck('length(@)', 1),
                JMESPathCheck('[0].name', self.route_table_name),
                JMESPathCheck('[0].resourceGroup', self.resource_group),
                JMESPathCheck('[0].type', self.resource_type)
        ])
        self.cmd('network route-table show --resource-group {} --name {}'.format(self.resource_group, self.route_table_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.route_table_name),
                JMESPathCheck('resourceGroup', self.resource_group),
                JMESPathCheck('type', self.resource_type)
        ])
        self.cmd('network route-table route list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name),
            checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network route-table route show --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.route_name),
                JMESPathCheck('resourceGroup', self.resource_group)
        ])
        self.cmd('network route-table route delete --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_name))
        # Expecting no results as the route operation was just deleted
        self.cmd('network route-table route list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name),
            checks=NoneCheck())
        self.cmd('network route-table delete --resource-group {} --name {}'.format(self.resource_group, self.route_table_name))
        # Expecting no results as the route table was just deleted
        self.cmd('network route-table list --resource-group {}'.format(self.resource_group), checks=NoneCheck())

class NetworkVNetScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkVNetScenarioTest, self).__init__(__file__, test_method, resource_group='cli_vnet_test')
        self.vnet_name = 'test-vnet'
        self.vnet_subnet_name = 'test-subnet1'
        self.resource_type = 'Microsoft.Network/virtualNetworks'

    def test_network_vnet(self):
        self.execute()

    def body(self):
        self.cmd('network vnet create --resource-group {} --name {} --subnet-name default'.format(self.resource_group, self.vnet_name), checks=[
            JMESPathCheck('newVNet.provisioningState', 'Succeeded'), # verify the deployment result
            JMESPathCheck('newVNet.addressSpace.addressPrefixes[0]', '10.0.0.0/16')
        ])

        self.cmd('network vnet check-ip-address -g {} -n {} --ip-address 10.0.0.50'.format(self.resource_group, self.vnet_name),
            checks=JMESPathCheck('available', True))

        self.cmd('network vnet check-ip-address -g {} -n {} --ip-address 10.0.0.0'.format(self.resource_group, self.vnet_name),
            checks=JMESPathCheck('available', False))

        self.cmd('network vnet list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)
        ])
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network vnet show --resource-group {} --name {}'.format(self.resource_group, self.vnet_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', self.vnet_name),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('type', self.resource_type)
        ])

        vnet_addr_prefixes = '20.0.0.0/16 10.0.0.0/16'
        self.cmd('network vnet update --resource-group {} --name {} --address-prefixes {}'.format(
            self.resource_group, self.vnet_name, vnet_addr_prefixes),
                checks=JMESPathCheck('length(addressSpace.addressPrefixes)', 2))

        # test generic update
        self.cmd('network vnet update --resource-group {} --name {} --set addressSpace.addressPrefixes[0]="20.0.0.0/24"'.format(
            self.resource_group, self.vnet_name), checks=JMESPathCheck('addressSpace.addressPrefixes[0]', '20.0.0.0/24'))

        self.cmd('network vnet subnet create --resource-group {} --vnet-name {} --name {} --address-prefix {}'.format(
            self.resource_group, self.vnet_name, self.vnet_subnet_name, '20.0.0.0/24'))

        self.cmd('network vnet subnet list --resource-group {} --vnet-name {}'.format(self.resource_group, self.vnet_name),
            checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network vnet subnet show --resource-group {} --vnet-name {} --name {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', self.vnet_subnet_name),
            JMESPathCheck('resourceGroup', self.resource_group)
        ])

        # Test delete subnet
        self.cmd('network vnet subnet delete --resource-group {} --vnet-name {} --name {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name))
        # Expecting the subnet to not be listed after delete
        self.cmd('network vnet subnet list --resource-group {} --vnet-name {}'.format(self.resource_group, self.vnet_name),
                  checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_subnet_name), 0))

        # Test delete vnet
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group),
            checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_name), 1))
        self.cmd('network vnet delete --resource-group {} --name {}'.format(self.resource_group, self.vnet_name))
        # Expecting the vnet we deleted to not be listed after delete
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group), NoneCheck())

class NetworkVNetPeeringScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(NetworkVNetPeeringScenarioTest, self).__init__(__file__, test_method, resource_group='cli_vnet_peering_test')

    def test_network_vnet_peering(self):
        self.execute()

    def set_up(self):
        super(NetworkVNetPeeringScenarioTest, self).set_up()
        rg = self.resource_group
        # create two vnets with non-overlapping prefixes
        self.cmd('network vnet create -g {} -n vnet1'.format(rg))
        self.cmd('network vnet create -g {} -n vnet2 --subnet-name GatewaySubnet --address-prefix 11.0.0.0/16 --subnet-prefix 11.0.0.0/24'.format(rg))
        # create supporting resources for gateway
        self.cmd('network public-ip create -g {} -n ip1'.format(rg))
        ip_id = self.cmd('network public-ip show -g {} -n ip1 --query id'.format(rg))
        vnet_id = self.cmd('network vnet show -g {} -n vnet2 --query id'.format(rg))
        # create the gateway on vnet2
        self.cmd('network vnet-gateway create -g {} -n gateway1 --public-ip-address {} --vnet {}'.format(rg, ip_id, vnet_id))

    def body(self):
        rg = self.resource_group
        vnet1_id = self.cmd('network vnet show -g {} -n vnet1 --query id'.format(rg))
        vnet2_id = self.cmd('network vnet show -g {} -n vnet2 --query id'.format(rg))
        # set up gateway sharing from vnet1 to vnet2
        self.cmd('network vnet peering create -g {} -n peering2 --vnet-name vnet2 --remote-vnet-id {} --allow-gateway-transit'.format(rg, vnet1_id), checks=[
            JMESPathCheck('allowGatewayTransit', True),
            JMESPathCheck('remoteVirtualNetwork.id', vnet1_id),
            JMESPathCheck('peeringState', 'Initiated')
        ])
        self.cmd('network vnet peering create -g {} -n peering1 --vnet-name vnet1 --remote-vnet-id {} --use-remote-gateways --allow-forwarded-traffic'.format(rg, vnet2_id), checks=[
            JMESPathCheck('useRemoteGateways', True),
            JMESPathCheck('remoteVirtualNetwork.id', vnet2_id),
            JMESPathCheck('peeringState', 'Connected'),
            JMESPathCheck('allowVirtualNetworkAccess', False)
        ])
        self.cmd('network vnet peering show -g {} -n peering1 --vnet-name vnet1'.format(rg),
            checks=JMESPathCheck('name', 'peering1'))
        self.cmd('network vnet peering list -g {} --vnet-name vnet2'.format(rg), checks=[
            JMESPathCheck('[0].name', 'peering2'),
            JMESPathCheck('length(@)', 1)
        ])
        self.cmd('network vnet peering update -g {} -n peering1 --vnet-name vnet1 --set useRemoteGateways=false'.format(rg), checks=[
            JMESPathCheck('useRemoteGateways', False),
            JMESPathCheck('allowForwardedTraffic', True)
        ])
        self.cmd('network vnet peering delete -g {} -n peering1 --vnet-name vnet1'.format(rg))
        self.cmd('network vnet peering list -g {} --vnet-name vnet1'.format(rg), checks=NoneCheck())
        # must delete the second peering and the gateway or the resource group delete will fail
        self.cmd('network vnet peering delete -g {} -n peering2 --vnet-name vnet2'.format(rg))
        self.cmd('network vnet-gateway delete -g {} -n gateway1'.format(rg))

class NetworkSubnetSetScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(NetworkSubnetSetScenarioTest, self).__init__(__file__, test_method, resource_group='cli_subnet_set_test')
        self.vnet_name = 'test-vnet2'

    def test_network_subnet_set(self):
        self.execute()

    def body(self):
        vnet_addr_prefix = '123.0.0.0/16'
        subnet_name = 'default'
        subnet_addr_prefix = '123.0.0.0/24'
        subnet_addr_prefix_new = '123.0.5.0/24'
        nsg_name = 'test-vnet-nsg'

        self.cmd('network vnet create --resource-group {} --name {} --address-prefix {} --subnet-name {} --subnet-prefix {}'.format(
            self.resource_group, self.vnet_name, vnet_addr_prefix, subnet_name, subnet_addr_prefix))
        self.cmd('network nsg create --resource-group {} --name {}'.format(self.resource_group, nsg_name))

        # Test we can update the address space and nsg
        self.cmd('network vnet subnet update --resource-group {} --vnet-name {} --name {} --address-prefix {} --network-security-group {}'.format(self.resource_group, self.vnet_name, subnet_name, subnet_addr_prefix_new, nsg_name), checks=[
            JMESPathCheck('addressPrefix', subnet_addr_prefix_new),
            JMESPathCheck('ends_with(@.networkSecurityGroup.id, `{}`)'.format('/' + nsg_name), True)
        ])

        # test generic update
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --set addressPrefix=123.0.0.0/24'.format(self.resource_group, self.vnet_name, subnet_name),
            checks=JMESPathCheck('addressPrefix', '123.0.0.0/24'))

        #Test we can get rid of the nsg.
        self.cmd('network vnet subnet update --resource-group {} --vnet-name {} --name {} --address-prefix {} --network-security-group {}'.format(self.resource_group, self.vnet_name, subnet_name, subnet_addr_prefix_new, '\"\"'),
            checks=JMESPathCheck('networkSecurityGroup', None))

        self.cmd('network vnet delete --resource-group {} --name {}'.format(self.resource_group, self.vnet_name))
        self.cmd('network nsg delete --resource-group {} --name {}'.format(self.resource_group, nsg_name))

class NetworkActiveActiveCrossPremiseScenarioTest(ResourceGroupVCRTestBase): # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(NetworkActiveActiveCrossPremiseScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_active_active_cross_premise_connection')
        self.vnet1 = 'vnet1'
        self.gw_subnet = 'GatewaySubnet'
        self.vnet_prefix1 = '10.11.0.0/16'
        self.vnet_prefix2 = '10.12.0.0/16'
        self.gw_subnet_prefix = '10.12.255.0/27'
        self.gw_ip1 = 'gwip1'
        self.gw_ip2 = 'gwip2'

    def test_network_active_active_cross_premise_connection(self):
        self.execute()

    def set_up(self):
        super(NetworkActiveActiveCrossPremiseScenarioTest, self).set_up()
        rg = self.resource_group

        self.cmd('network vnet create -g {} -n {} --address-prefix {} {} --subnet-name {} --subnet-prefix {}'.format(rg, self.vnet1, self.vnet_prefix1, self.vnet_prefix2, self.gw_subnet, self.gw_subnet_prefix))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, self.gw_ip1))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, self.gw_ip2))

    def body(self):
        rg = self.resource_group
        vnet1 = self.vnet1
        vnet1_asn = 65010
        gw1 = 'gw1'

        lgw2 = 'lgw2'
        lgw_ip = '131.107.72.22'
        lgw_prefix = '10.52.255.253/32'
        bgp_peer1 = '10.52.255.253'
        lgw_asn = 65050
        lgw_loc = 'eastus'
        conn_151 = 'Vnet1toSite5_1'
        conn_152 = 'Vnet1toSite5_2'
        shared_key = 'abc123'
        shared_key2 = 'a1b2c3'

        # create the vnet gateway with active-active feature
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --sku HighPerformance --asn {} --public-ip-addresses {} {}'.format(rg, gw1, vnet1, vnet1_asn, self.gw_ip1, self.gw_ip2))

        # create and connect first local-gateway
        self.cmd('network local-gateway create -g {} -n {} -l {} --gateway-ip-address {} --local-address-prefixes {} --asn {} --bgp-peering-address {}'.format(rg, lgw2, lgw_loc, lgw_ip, lgw_prefix, lgw_asn, bgp_peer1))
        self.cmd('network vpn-connection create -g {} -n {} --vnet-gateway1 {} --local-gateway2 {} --shared-key {} --enable-bgp'.format(rg, conn_151, gw1, lgw2, shared_key))
        self.cmd('network vpn-connection shared-key reset -g {} --connection-name {} --key-length 128'.format(rg, conn_151))
        sk1 = self.cmd('network vpn-connection shared-key show -g {} --connection-name {}'.format(rg, conn_151))
        self.cmd('network vpn-connection shared-key update -g {} --connection-name {} --value {}'.format(rg, conn_151, shared_key2))
        sk2 = self.cmd('network vpn-connection shared-key show -g {} --connection-name {}'.format(rg, conn_151),
            checks=JMESPathCheck('value', shared_key2))
        self.assertNotEqual(sk1, sk2)

        lgw3 = 'lgw3'
        lgw3_ip = '131.107.72.23'
        lgw3_prefix = '10.52.255.254/32'
        bgp_peer2 = '10.52.255.254'

        # create and connect second local-gateway
        self.cmd('network local-gateway create -g {} -n {} -l {} --gateway-ip-address {} --local-address-prefixes {} --asn {} --bgp-peering-address {}'.format(rg, lgw3, lgw_loc, lgw3_ip, lgw3_prefix, lgw_asn, bgp_peer2))
        self.cmd('network vpn-connection create -g {} -n {} --vnet-gateway1 {} --local-gateway2 {} --shared-key {} --enable-bgp'.format(rg, conn_152, gw1, lgw3, shared_key))


class NetworkActiveActiveVnetVnetScenarioTest(ResourceGroupVCRTestBase): # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(NetworkActiveActiveVnetVnetScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_active_active_vnet_vnet_connection')
        self.gw_subnet = 'GatewaySubnet'

        # First VNet
        self.vnet1 = 'vnet1'
        self.vnet1_prefix = '10.21.0.0/16'
        self.gw1_subnet_prefix = '10.21.255.0/27'
        self.gw1_ip1 = 'gw1ip1'
        self.gw1_ip2 = 'gw1ip2'

        # Second VNet
        self.vnet2 = 'vnet2'
        self.vnet2_prefix = '10.22.0.0/16'
        self.gw2_subnet_prefix = '10.22.255.0/27'
        self.gw2_ip1 = 'gw2ip1'
        self.gw2_ip2 = 'gw2ip2'

    def test_network_active_active_vnet_vnet_connection(self):
        self.execute()

    def set_up(self):
        super(NetworkActiveActiveVnetVnetScenarioTest, self).set_up()
        rg = self.resource_group

        # Create one VNet with two public IPs
        self.cmd('network vnet create -g {} -n {} --address-prefix {} --subnet-name {} --subnet-prefix {}'.format(rg, self.vnet1, self.vnet1_prefix, self.gw_subnet, self.gw1_subnet_prefix))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, self.gw1_ip1))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, self.gw1_ip2))

        # Create second VNet with two public IPs
        self.cmd('network vnet create -g {} -n {} --address-prefix {} --subnet-name {} --subnet-prefix {}'.format(rg, self.vnet2, self.vnet2_prefix, self.gw_subnet, self.gw2_subnet_prefix))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, self.gw2_ip1))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, self.gw2_ip2))

    def body(self):
        rg = self.resource_group
        vnet1 = self.vnet1
        vnet1_asn = 65010
        gw1 = 'vgw1'
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --sku HighPerformance --asn {} --public-ip-addresses {} {} --no-wait'.format(rg, gw1, vnet1, vnet1_asn, self.gw1_ip1, self.gw1_ip2))

        vnet2 = self.vnet2
        vnet2_asn = 65020
        gw2 = 'vgw2'
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --sku HighPerformance --asn {} --public-ip-addresses {} {} --no-wait'.format(rg, gw2, vnet2, vnet2_asn, self.gw2_ip1, self.gw2_ip2))

        # wait for gateway completion to finish
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gw1))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gw2))

        conn12 = 'vnet1to2'
        conn21 = 'vnet2to1'
        shared_key = 'abc123'

        # create and connect the VNet gateways
        self.cmd('network vpn-connection create -g {} -n {} --vnet-gateway1 {} --vnet-gateway2 {} --shared-key {} --enable-bgp'.format(rg, conn12, gw1, gw2, shared_key))
        self.cmd('network vpn-connection create -g {} -n {} --vnet-gateway1 {} --vnet-gateway2 {} --shared-key {} --enable-bgp'.format(rg, conn21, gw2, gw1, shared_key))


class NetworkVpnGatewayScenarioTest(ResourceGroupVCRTestBase): # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(NetworkVpnGatewayScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vpn_gateway')
        self.vnet1_name = 'myvnet1'
        self.vnet2_name = 'myvnet2'
        self.vnet3_name = 'myvnet3'
        self.gateway1_name = 'gateway1'
        self.gateway2_name = 'gateway2'
        self.gateway3_name = 'gateway3'
        self.ip1_name = 'pubip1'
        self.ip2_name = 'pubip2'
        self.ip3_name = 'pubip3'

    def test_network_vpn_gateway(self):
        self.execute()

    def set_up(self):
        super(NetworkVpnGatewayScenarioTest, self).set_up()
        rg = self.resource_group
        self.cmd('network public-ip create -n {} -g {}'.format(self.ip1_name, rg))
        self.cmd('network public-ip create -n {} -g {}'.format(self.ip2_name, rg))
        self.cmd('network public-ip create -n {} -g {}'.format(self.ip3_name, rg))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.0.0/24'.format(rg, self.vnet1_name))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.1.0.0/16'.format(rg, self.vnet2_name))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.2.0.0/16'.format(rg, self.vnet3_name))

    def body(self):
        rg = self.resource_group

        subscription_id = MOCKED_SUBSCRIPTION_ID \
            if self.playback \
            else self.cmd('account list --query "[?isDefault].id" -o tsv')

        vnet1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(subscription_id, rg, self.vnet1_name)
        vnet2_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(subscription_id, rg, self.vnet2_name)

        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait'.format(rg, self.gateway1_name, vnet1_id, self.ip1_name))
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait'.format(rg, self.gateway2_name, vnet2_id, self.ip2_name))
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait --sku standard --asn 12345 --bgp-peering-address 10.2.250.250 --peer-weight 50'.format(rg, self.gateway3_name, self.vnet3_name, self.ip3_name))

        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, self.gateway1_name))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, self.gateway2_name))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, self.gateway3_name))

        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, self.gateway1_name), checks=[
            JMESPathCheck('gatewayType', 'Vpn'),
            JMESPathCheck('sku.capacity', 2),
            JMESPathCheck('sku.name', 'Basic'),
            JMESPathCheck('vpnType', 'RouteBased'),
            JMESPathCheck('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, self.gateway2_name), checks=[
            JMESPathCheck('gatewayType', 'Vpn'),
            JMESPathCheck('sku.capacity', 2),
            JMESPathCheck('sku.name', 'Basic'),
            JMESPathCheck('vpnType', 'RouteBased'),
            JMESPathCheck('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, self.gateway3_name), checks=[
            JMESPathCheck('sku.name', 'Standard'),
            JMESPathCheck('enableBgp', True),
            JMESPathCheck('bgpSettings.asn', 12345),
            JMESPathCheck('bgpSettings.bgpPeeringAddress', '10.2.250.250'),
            JMESPathCheck('bgpSettings.peerWeight', 50)
        ])

        conn12 = 'conn1to2'
        gateway1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworkGateways/{}'.format(subscription_id, rg, self.gateway1_name)
        self.cmd('network vpn-connection create -n {} -g {} --shared-key 123 --vnet-gateway1 {} --vnet-gateway2 {}'.format(conn12, rg, gateway1_id, self.gateway2_name))
        self.cmd('network vpn-connection update -n {} -g {} --routing-weight 25'.format(conn12, rg),
            checks=JMESPathCheck('routingWeight', 25))

        # test network watcher troubleshooting commands
        storage_account = 'clitestnwstorage2'
        container_name = 'troubleshooting-results'
        self.cmd('storage account create -g {} -l westus --sku Standard_LRS -n {}'.format(rg, storage_account))
        self.cmd('storage container create --account-name {} -n {}'.format(storage_account, container_name))
        storage_path = 'https://{}.blob.core.windows.net/{}'.format(storage_account, container_name)
        self.cmd('network watcher configure -g {} --locations westus --enabled'.format(rg))
        self.cmd('network watcher troubleshooting start -g {} --resource {} --resource-type vpnConnection --storage-account {} --storage-path {}'.format(rg, conn12, storage_account, storage_path))
        self.cmd('network watcher troubleshooting show -g {} --resource {} --resource-type vpnConnection'.format(rg, conn12))


class NetworkTrafficManagerScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkTrafficManagerScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_traffic_manager')

    def test_network_traffic_manager(self):
        self.execute()

    def body(self):
        tm_name = 'mytmprofile'
        endpoint_name = 'myendpoint'
        unique_dns_name = 'mytrafficmanager001100a'

        self.cmd('network traffic-manager profile check-dns -n myfoobar1')
        self.cmd('network traffic-manager profile create -n {} -g {} --routing-method priority --unique-dns-name {}'.format(tm_name, self.resource_group, unique_dns_name),
            checks=JMESPathCheck('TrafficManagerProfile.trafficRoutingMethod', 'Priority'))
        self.cmd('network traffic-manager profile show -g {} -n {}'.format(self.resource_group, tm_name),
            checks=JMESPathCheck('dnsConfig.relativeName', unique_dns_name))
        self.cmd('network traffic-manager profile update -n {} -g {} --routing-method weighted'.format(tm_name, self.resource_group),
            checks=JMESPathCheck('trafficRoutingMethod', 'Weighted'))
        self.cmd('network traffic-manager profile list -g {}'.format(self.resource_group))

        # Endpoint tests
        self.cmd('network traffic-manager endpoint create -n {} --profile-name {} -g {} --type externalEndpoints --weight 50 --target www.microsoft.com'.format(endpoint_name, tm_name, self.resource_group),
            checks=JMESPathCheck('type', 'Microsoft.Network/trafficManagerProfiles/externalEndpoints'))
        self.cmd('network traffic-manager endpoint update -n {} --profile-name {} -g {} --type externalEndpoints --weight 25 --target www.contoso.com'.format(endpoint_name, tm_name, self.resource_group), checks=[
            JMESPathCheck('weight', 25),
            JMESPathCheck('target', 'www.contoso.com')
        ])
        self.cmd('network traffic-manager endpoint show -g {} --profile-name {} -t externalEndpoints -n {}'.format(self.resource_group, tm_name, endpoint_name))
        self.cmd('network traffic-manager endpoint list -g {} --profile-name {} -t externalEndpoints'.format(self.resource_group, tm_name),
            checks=JMESPathCheck('length(@)', 1))
        self.cmd('network traffic-manager endpoint delete -g {} --profile-name {} -t externalEndpoints -n {}'.format(self.resource_group, tm_name, endpoint_name))
        self.cmd('network traffic-manager endpoint list -g {} --profile-name {} -t externalEndpoints'.format(self.resource_group, tm_name),
            checks=JMESPathCheck('length(@)', 0))

        self.cmd('network traffic-manager profile delete -g {} -n {}'.format(self.resource_group, tm_name))


class NetworkDnsScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkDnsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_dns')

    def test_network_dns(self):
        self.execute()

    def body(self):
        zone_name = 'myzone.com'
        rg = self.resource_group

        self.cmd('network dns zone list')  # just verify is works (no Exception raised)
        self.cmd('network dns zone create -n {} -g {}'.format(zone_name, rg))
        self.cmd('network dns zone list -g {}'.format(rg),
            checks=JMESPathCheck('length(@)', 1))

        base_record_sets = 2
        self.cmd('network dns zone show -n {} -g {}'.format(zone_name, rg), checks=[
            JMESPathCheck('numberOfRecordSets', base_record_sets)
        ])

        args = {
            'a': '--ipv4-address 10.0.0.10',
            'aaaa': '--ipv6-address 2001:db8:0:1:1:1:1:1',
            'cname': '--cname mycname',
            'mx': '--exchange 12 --preference 13',
            'ns': '--nsdname foobar.com',
            'ptr': '--ptrdname foobar.com',
            'soa': '--email foo.com --expire-time 30 --minimum-ttl 20 --refresh-time 60 --retry-time 90 --serial-number 123',
            'srv': '--port 1234 --priority 1 --target target.com --weight 50',
            'txt': '--value some_text'
        }

        record_types = ['a', 'aaaa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']

        for t in record_types:
            # test creating the record set and then adding records
            self.cmd('network dns record-set {0} create -n myrs{0} -g {1} --zone-name {2}'
                     .format(t, rg, zone_name))
            add_command = 'set-record' if t == 'cname' else 'add-record'
            self.cmd('network dns record-set {0} {4} -g {1} --zone-name {2} --record-set-name myrs{0} {3}'
                     .format(t, rg, zone_name, args[t], add_command))
            # test creating the record set at the same time you add records
            self.cmd('network dns record-set {0} {4} -g {1} --zone-name {2} --record-set-name myrs{0}alt {3}'
                     .format(t, rg, zone_name, args[t], add_command))

        self.cmd('network dns record-set {0} add-record -g {1} --zone-name {2} --record-set-name myrs{0} {3}'
                 .format('a', rg, zone_name, '--ipv4-address 10.0.0.11'))
        self.cmd('network dns record-set soa update -g {0} --zone-name {1} {2}'
                     .format(rg, zone_name, args['soa']))

        long_value = '0123456789' * 50
        self.cmd('network dns record-set txt add-record -g {} -z {} -n longtxt -v {}'.format(rg, zone_name, long_value))

        typed_record_sets = 2 * len(record_types) + 1
        self.cmd('network dns zone show -n {} -g {}'.format(zone_name, rg), checks=[
            JMESPathCheck('numberOfRecordSets', base_record_sets + typed_record_sets)
            ])
        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'
                 .format('a', rg, zone_name), checks=[
                     JMESPathCheck('length(arecords)', 2)
                     ])

        # test list vs. list type
        self.cmd('network dns record-set list -g {} -z {}'.format(rg, zone_name),
            checks=JMESPathCheck('length(@)', base_record_sets + typed_record_sets))

        self.cmd('network dns record-set txt list -g {} -z {}'.format(rg, zone_name),
            checks=JMESPathCheck('length(@)', 3))

        for t in record_types:
            self.cmd('network dns record-set {0} remove-record -g {1} --zone-name {2} --record-set-name myrs{0} {3}'
                     .format(t, rg, zone_name, args[t]))
        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'
                 .format('a', rg, zone_name), checks=[
                     JMESPathCheck('length(arecords)', 1)
                     ])

        self.cmd('network dns record-set {0} remove-record -g {1} --zone-name {2} --record-set-name myrs{0} {3}'
                     .format('a', rg, zone_name, '--ipv4-address 10.0.0.11'))

        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'.format('a', rg, zone_name),
            checks=NoneCheck())

        self.cmd('network dns record-set {0} delete -n myrs{0} -g {1} --zone-name {2} -y'
                 .format('a', rg, zone_name))
        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'
                 .format('a', rg, zone_name), allowed_exceptions='does not exist in resource group')

        self.cmd('network dns zone delete -g {} -n {} -y'.format(rg, zone_name),
            checks=JMESPathCheck('status', 'Succeeded'))

class NetworkZoneImportExportTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkZoneImportExportTest, self).__init__(__file__, test_method, resource_group='cli_dns_zone_import_export')

    def test_network_dns_zone_import_export(self):
        self.execute()

    def body(self):
        zone_name = 'myzone.com'
        zone_file_path = os.path.join(TEST_DIR, 'zone_files', 'zone1.txt')

        self.cmd('network dns zone import -n {} -g {} --file-name "{}"'
                 .format(zone_name, self.resource_group, zone_file_path))
        self.cmd('network dns zone export -n {} -g {}'.format(zone_name, self.resource_group))

class NetworkWatcherScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkWatcherScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_network_watcher')

    def test_network_watcher(self):
        self.execute()

    def body(self):

        resource_group = self.resource_group
        storage_account = 'clitestnwstorage1'

        self.cmd('network watcher configure -g {} --locations westus westus2 --enabled'.format(resource_group))
        self.cmd('network watcher configure --locations westus westus2 --tags foo=doo')
        self.cmd('network watcher configure -l westus2 --enabled false')
        self.cmd('network watcher list')

        vm = 'vm1'
        # create VM with NetworkWatcher extension
        self.cmd('storage account create -g {} -l westus --sku Standard_LRS -n {}'.format(resource_group, storage_account))
        self.cmd('vm create -g {} -n {} --image UbuntuLTS --authentication-type password --admin-password PassPass10!)'.format(resource_group, vm))
        self.cmd('vm extension set -g {} --vm-name {} -n NetworkWatcherAgentLinux --publisher Microsoft.Azure.NetworkWatcher'.format(resource_group, vm))

        self.cmd('network watcher show-topology -g {} -l westus'.format(resource_group))

        self.cmd('network watcher test-ip-flow -g {} --vm {} --direction inbound --local 10.0.0.4:22 --protocol tcp --remote 100.1.2.3:*'.format(resource_group, vm))
        self.cmd('network watcher test-ip-flow -g {} --vm {} --direction outbound --local 10.0.0.4:* --protocol tcp --remote 100.1.2.3:80'.format(resource_group, vm))

        self.cmd('network watcher show-security-group-view -g {} --vm {}'.format(resource_group, vm))

        self.cmd('network watcher show-next-hop -g {} --vm {} --source-ip 123.4.5.6 --dest-ip 10.0.0.6'.format(resource_group, vm))

        capture = 'capture1'
        location = 'westus'
        self.cmd('network watcher packet-capture create -g {} --vm {} -n {} --file-path capture/capture.cap'.format(resource_group, vm, capture))
        self.cmd('network watcher packet-capture show -l {} -n {}'.format(location, capture))
        self.cmd('network watcher packet-capture stop -l {} -n {}'.format(location, capture))
        self.cmd('network watcher packet-capture show-status -l {} -n {}'.format(location, capture))
        self.cmd('network watcher packet-capture list -l {}'.format(location, capture))
        self.cmd('network watcher packet-capture delete -l {} -n {}'.format(location, capture))
        self.cmd('network watcher packet-capture list -l {}'.format(location, capture))

        nsg = '{}NSG'.format(vm)
        self.cmd('network watcher flow-log configure -g {} --nsg {} --enabled --retention 5 --storage-account {}'.format(resource_group, nsg, storage_account))
        self.cmd('network watcher flow-log configure -g {} --nsg {} --retention 0'.format(resource_group, nsg))
        self.cmd('network watcher flow-log show -g {} --nsg {}'.format(resource_group, nsg))


if __name__ == '__main__':
    unittest.main()
