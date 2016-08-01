#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
import os

from azure.cli.utils.vcr_test_base import (VCRTestBase, ResourceGroupVCRTestBase, JMESPathCheck,
                                           NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class NetworkUsageListScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkUsageListScenarioTest, self).__init__(__file__, test_method)

    def test_network_usage_list(self):
        self.execute()

    def body(self):
        self.cmd('network list-usages --location westus', checks=JMESPathCheck('type(@)', 'array'))

class NetworkAppGatewayDefaultScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayDefaultScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'ag1rg'

    def test_network_app_gateway_with_defaults(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        self.cmd('network application-gateway create -g {} -n ag1'.format(rg), checks=[
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck("applicationGateway.frontendIPConfigurations[0].properties.subnet.contains(id, 'default')", True)
        ])

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
        ])

        self.cmd('network application-gateway stop --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway start --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway delete --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=JMESPathCheck('length(@)', ag_count - 1))

class NetworkAppGatewayExistingSubnetScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayExistingSubnetScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'ag2rg'

    def test_network_app_gateway_with_existing_subnet(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        vnet = self.cmd('network vnet create -g {} -n vnet2 --subnet-name subnet1'.format(rg))
        subnet_id = vnet['newVNet']['subnets'][0]['id']
        self.cmd('network application-gateway create -g {} -n ag2 --subnet {}'.format(rg, subnet_id), checks=[
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
        ])

class NetworkAppGatewayPrivateIpScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayPrivateIpScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'ag3rg'

    def test_network_app_gateway_with_private_ip(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        private_ip = '10.0.0.15'
        cert_path = os.path.join(TEST_DIR, 'TestCert.pfx')
        cert_pass = 'password'
        self.cmd('network application-gateway create -g {} -n ag3 --subnet subnet1 --private-ip-address {} --cert-file "{}" --cert-password {}'.format(rg, private_ip, cert_path, cert_pass), checks=[
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAddress', private_ip),
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Static')
        ])

class NetworkAppGatewayPublicIpScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayPublicIpScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'ag4rg'

    def test_network_app_gateway_with_public_ip(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        public_ip_name = 'publicip4'
        self.cmd('network application-gateway create -g {} -n test4 --subnet subnet1 --vnet-name vnet4 --public-ip {}'.format(rg, public_ip_name), checks=[
            JMESPathCheck("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(public_ip_name), True),
            JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')
        ])

class NetworkPublicIpScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkPublicIpScenarioTest, self).__init__(__file__, test_method)
        self.public_ip_name = 'pubipdns'
        self.public_ip_no_dns_name = 'pubipnodns'
        self.dns = 'woot'

    def test_network_public_ip(self):
        self.execute()

    def body(self):
        s = self
        rg = s.resource_group
        s.cmd('network public-ip create -g {} -n {} --dns-name {} --allocation-method static'.format(rg, s.public_ip_name, s.dns), checks=[
            JMESPathCheck('publicIp.provisioningState', 'Succeeded'),
            JMESPathCheck('publicIp.publicIPAllocationMethod', 'Static'),
            JMESPathCheck('publicIp.dnsSettings.domainNameLabel', s.dns)
        ])
        s.cmd('network public-ip create -g {} -n {}'.format(rg, s.public_ip_no_dns_name), checks=[
            JMESPathCheck('publicIp.provisioningState', 'Succeeded'),
            JMESPathCheck('publicIp.publicIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('publicIp.dnsSettings', None)
        ])
        s.cmd('network public-ip list', checks=JMESPathCheck('type(@)', 'array'))
        ip_list = s.cmd('network public-ip list -g {}'.format(rg))
        assert not [x for x in ip_list if x['resourceGroup'].lower() != rg]

        s.cmd('network public-ip show -g {} -n {}'.format(rg, s.public_ip_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', s.public_ip_name),
            JMESPathCheck('resourceGroup', rg),
        ])
        s.cmd('network public-ip delete -g {} -n {}'.format(rg, s.public_ip_name))
        s.cmd('network public-ip list -g {}'.format(rg),
            checks=JMESPathCheck("length[?name == '{}']".format(s.public_ip_name), None))

class NetworkExpressRouteScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkExpressRouteScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.express_route_name = 'test_route'
        self.resource_type = 'Microsoft.Network/expressRouteCircuits'

    def test_network_express_route(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network express-route circuit show --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name)):
            raise RuntimeError('Express route must be manually created in order to support this test.')

    def body(self):
        self.cmd('network express-route circuit list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network express-route circuit list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network express-route circuit show --resource-group {} --name {}'.format(self.resource_group, self.express_route_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', self.resource_type),
            JMESPathCheck('name', self.express_route_name),
            JMESPathCheck('resourceGroup', self.resource_group),
        ])
        self.cmd('network express-route circuit get-stats --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name), checks=JMESPathCheck('type(@)', 'object'))
        self.cmd('network express-route circuit-auth list --resource-group {} --circuit-name {}'.format(
            self.resource_group, self.express_route_name), checks=NoneCheck())
        self.cmd('network express-route circuit-peering list --resource-group {} --circuit-name {}'.format(
            self.resource_group, self.express_route_name), checks=NoneCheck())
        self.cmd('network express-route service-provider list', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format('Microsoft.Network/expressRouteServiceProviders'), True)
        ])
        self.cmd('network express-route circuit delete --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name), checks=NoneCheck())
        # Expecting no results as we just deleted the only express route in the resource group
        self.cmd('network express-route circuit list --resource-group {}'.format(self.resource_group),
            checks=NoneCheck())

class NetworkExpressRouteCircuitScenarioTest(VCRTestBase):

    def __init__(self, test_method):
         # The resources for this test did not exist so the commands will return 404 errors.
         # So this test is for the command execution itself.
        super(NetworkExpressRouteCircuitScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.express_route_name = 'test_route'
        self.placeholder_value = 'none_existent'

    def test_network_express_route_circuit(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        ern = self.express_route_name
        pv = self.placeholder_value
        allowed_exceptions = "The Resource 'Microsoft.Network/expressRouteCircuits/{}' under resource group '{}' was not found.".format(ern, rg)
        self.cmd('network express-route circuit-auth show --resource-group {0} --circuit-name {1} --name {2}'.format(
            rg, ern, pv), allowed_exceptions=allowed_exceptions)
        self.cmd('network express-route circuit-auth delete --resource-group {0} --circuit-name {1} --name {2}'.format(
            rg, ern, pv), allowed_exceptions=allowed_exceptions)
        self.cmd('network express-route circuit-peering delete --resource-group {0} --circuit-name {1} --name {2}'.format(
            rg, ern, pv), allowed_exceptions=allowed_exceptions)
        self.cmd('network express-route circuit-peering show --resource-group {0} --circuit-name {1} --name {2}'.format(
            rg, ern, pv), allowed_exceptions=allowed_exceptions)
        self.cmd('network express-route circuit list-arp --resource-group {0} --name {1} --peering-name {2} --device-path {2}'.format(
            rg, ern, pv), allowed_exceptions=allowed_exceptions)
        self.cmd('network express-route circuit list-routes --resource-group {0} --name {1} --peering-name {2} --device-path {2}'.format(
            rg, ern, pv), allowed_exceptions=allowed_exceptions)

class NetworkLoadBalancerScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkLoadBalancerScenarioTest, self).__init__(
            __file__, test_method)
        self.resource_group = 'lbrg'
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
        vnet = self.cmd('network vnet create -n {} -g {}'.format(vnet_name, self.resource_group))
        subnet_id = vnet['newVNet']['subnets'][0]['id']
        self.cmd('network lb create -n {}3 -g {} --vnet-name {} --subnet {} --private-ip-address {}'.format(
            self.lb_name, self.resource_group, vnet_name, subnet_id, private_ip), checks=[
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

class NetworkLoadBalancerSubresourceScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkLoadBalancerSubresourceScenarioTest, self).__init__(
            __file__, test_method)
        self.resource_group = 'lbsrg'
        self.lb_name = 'lb1'
        self.vnet_name = 'vnet1'
        self.subnet_name = 'subnet1'

    def test_network_load_balancer_subresources(self):
        self.execute()

    def set_up(self):
        super(NetworkLoadBalancerSubresourceScenarioTest, self).set_up()
        rg = self.resource_group
        lb = self.lb_name
        self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, self.vnet_name, self.subnet_name))
        for i in range(1, 4):
            self.cmd('network public-ip create -g {} -n publicip{}'.format(rg, i))
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

    def body(self):
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
        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool delete {} -n rule{}'.format(lb_rg, count))
        self.cmd('network lb inbound-nat-pool list {}'.format(lb_rg),
            checks=JMESPathCheck('length(@)', 0))

        # Test frontend IP configuration
        self.cmd('network lb frontend-ip create {} -n ipconfig1 --public-ip-address-name publicip1'.format(lb_rg))
        self.cmd('network lb frontend-ip create {} -n ipconfig2 --public-ip-address-name publicip2'.format(lb_rg))
        self.cmd('network lb frontend-ip create {} -n ipconfig3 --vnet-name {} --subnet-name {} --private-ip-address 10.0.0.99'.format(lb_rg, self.vnet_name, self.subnet_name),
            allowed_exceptions='is not registered for feature Microsoft.Network/AllowMultiVipIlb required to carry out the requested operation.')
        # Note that the ipconfig3 won't be added. The 3 that will be found are the default and two created ones
        self.cmd('network lb frontend-ip list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 3))
        self.cmd('network lb frontend-ip update {} -n ipconfig1 --public-ip-address-name publicip3'.format(lb_rg))
        self.cmd('network lb frontend-ip show {} -n ipconfig1'.format(lb_rg),
            checks=JMESPathCheck("publicIpAddress.contains(id, 'publicip3')", True))
        self.cmd('network lb frontend-ip delete {} -n ipconfig2'.format(lb_rg))
        self.cmd('network lb frontend-ip list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 2))

        # Test backend address pool
        for i in range(1, 4):
            self.cmd('network lb address-pool create {} -n bap{}'.format(lb_rg, i))
        self.cmd('network lb address-pool list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 4))
        self.cmd('network lb address-pool show {} -n bap1'.format(lb_rg),
            checks=JMESPathCheck('name', 'bap1'))
        self.cmd('network lb address-pool delete {} -n bap3'.format(lb_rg))
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
        self.cmd('network lb rule update {} -n rule2 --frontend-ip-name ipconfig1 --backend-pool-name bap2 --load-distribution sourceipprotocol'.format(lb_rg))
        self.cmd('network lb rule show {} -n rule1'.format(lb_rg), checks=[
            JMESPathCheck('enableFloatingIp', True),
            JMESPathCheck('idleTimeoutInMinutes', 20),
            JMESPathCheck('loadDistribution', 'SourceIP'),
            JMESPathCheck('protocol', 'Udp')
        ])
        self.cmd('network lb rule show {} -n rule2'.format(lb_rg), checks=[
            JMESPathCheck("backendAddressPool.contains(id, 'bap2')", True),
            JMESPathCheck("frontendIpConfiguration.contains(id, 'ipconfig1')", True),
            JMESPathCheck('loadDistribution', 'SourceIPProtocol')
        ])
        self.cmd('network lb rule delete {} -n rule1'.format(lb_rg))
        self.cmd('network lb rule delete {} -n rule2'.format(lb_rg))
        self.cmd('network lb rule list {}'.format(lb_rg), checks=JMESPathCheck('length(@)', 0))

class NetworkLocalGatewayScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkLocalGatewayScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.name = 'cli-test-loc-gateway'
        self.resource_type = 'Microsoft.Network/localNetworkGateways'

    def test_network_local_gateway(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network local-gateway show --resource-group {} --name {}'.format(
            self.resource_group, self.name)):
            raise RuntimeError('Local gateway must be manually created in order to support this test.')

    def body(self):
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
        self.cmd('network local-gateway delete --resource-group {} --name {}'.format(self.resource_group, self.name))
        # Expecting no results as we just deleted the only local gateway in the resource group
        self.cmd('network local-gateway list --resource-group {}'.format(self.resource_group), checks=NoneCheck())

class NetworkNicScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'

    def test_network_nic(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        nic = 'cli-test-nic'
        rt = 'Microsoft.Network/networkInterfaces'
        subnet = 'mysubnet'
        vnet = 'myvnet'
        nsg = 'mynsg'
        private_ip = '10.0.0.15'
        public_ip_name = 'publicip1'

        self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, vnet, subnet))
        self.cmd('network nsg create -g {} -n {}'.format(rg, nsg))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip_name))

        # create with minimum parameters
        self.cmd('network nic create -g {} -n {} --subnet-name {} --vnet-name {}'.format(rg, nic, subnet, vnet), checks=[
            JMESPathCheck('newNIC.ipConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('newNIC.provisioningState', 'Succeeded')
        ])
        # exercise optional parameters
        self.cmd('network nic create -g {} -n {} --subnet-name {} --vnet-name {} --ip-forwarding --private-ip-address {} --public-ip-address-name "{}"'.format(rg, nic, subnet, vnet, private_ip, public_ip_name), checks=[
            JMESPathCheck('newNIC.ipConfigurations[0].properties.privateIPAllocationMethod', 'Static'),
            JMESPathCheck('newNIC.ipConfigurations[0].properties.privateIPAddress', private_ip),
            JMESPathCheck('newNIC.enableIPForwarding', True),
            JMESPathCheck('newNIC.provisioningState', 'Succeeded')
        ])
        # exercise creating with NSG
        self.cmd('network nic create -g {} -n {} --subnet-name {} --vnet-name {} --nsg-name {}'.format(rg, nic, subnet, vnet, nsg), checks=[
            JMESPathCheck('newNIC.ipConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('newNIC.enableIPForwarding', False),
            JMESPathCheck("newNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheck('newNIC.provisioningState', 'Succeeded')
        ])
        # exercise creating with NSG and Public IP
        self.cmd('network nic create -g {} -n {} --subnet-name {} --vnet-name {} --nsg-name {} --public-ip-address-name "{}"'.format(rg, nic, subnet, vnet, nsg, public_ip_name), checks=[
            JMESPathCheck('newNIC.ipConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheck('newNIC.enableIPForwarding', False),
            JMESPathCheck("newNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheck('newNIC.provisioningState', 'Succeeded')
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
        self.cmd('network nic delete --resource-group {} --name {}'.format(rg, nic))
        self.cmd('network nic list -g {}'.format(rg), checks=NoneCheck())

class NetworkNicScaleSetScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicScaleSetScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.vmss_name = 'clitestvm'
        self.nic_name = 'clitestvmnic'
        self.vm_index = 0
        self.resource_type = 'Microsoft.Network/networkInterfaces'

    def test_network_nic_scaleset(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network nic scale-set show --resource-group {} --vm-scale-set {} --vm-index {} --name {}'.format(
            self.resource_group, self.vmss_name, self.vm_index, self.nic_name)):
            raise RuntimeError('VM scale set NIC must be manually created in order to support this test.')

    def body(self):
        self.cmd('network nic scale-set list --resource-group {} --vm-scale-set {}'.format(
                  self.resource_group, self.vmss_name), checks=[
                JMESPathCheck('type(@)', 'array'),
                JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
                JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network nic scale-set list-vm-nics --resource-group {} --vm-scale-set {} --vm-index {}'.format(self.resource_group, self.vmss_name, self.vm_index), checks=[
                JMESPathCheck('type(@)', 'array'),
                JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
                JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network nic scale-set show --resource-group {} --vm-scale-set {} --vm-index {} --name {}'.format(self.resource_group, self.vmss_name, self.vm_index, self.nic_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.nic_name),
                JMESPathCheck('resourceGroup', self.resource_group),
                JMESPathCheck('type', self.resource_type)
        ])

class NetworkSecurityGroupScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkSecurityGroupScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_nsg_test1'
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
        self.cmd('network nsg rule create --access allow --destination-address-prefix 1234 --direction inbound --nsg-name {} --protocol * -g {} --source-address-prefix 789 -n {} --source-port-range * --destination-port-range 4444'.format(nsg, rg, nrn))

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
        new_protocol = 'tcp'
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

        self.cmd('network nsg rule delete --resource-group {} --nsg-name {} --name {}'.format(rg, nsg, nrn))
        # Delete the network security group
        self.cmd('network nsg delete --resource-group {} --name {}'.format(rg, nsg))
        # Expecting no results as we just deleted the only security group in the resource group
        self.cmd('network nsg list --resource-group {}'.format(rg), checks=NoneCheck())

class NetworkRouteTableOperationScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkRouteTableOperationScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.route_table_name = 'cli-test-route-table'
        self.route_operation_name = 'my-route'
        self.resource_type = 'Microsoft.Network/routeTables'

    def test_network_route_table_operation(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network route-table show --resource-group {} --name {}'.format(
                self.resource_group, self.route_table_name)):
            raise RuntimeError('Network route table must be manually created in order to support this test.')
        if not self.cmd('network route-table route show --resource-group {} --route-table-name {} --name {}'.format(
                self.resource_group, self.route_table_name, self.route_operation_name)):
            raise RuntimeError('Network route operation must be manually created in order to support this test.')

    def body(self):
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
        self.cmd('network route-table route show --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_operation_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.route_operation_name),
                JMESPathCheck('resourceGroup', self.resource_group)
        ])
        self.cmd('network route-table route delete --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_operation_name))
        # Expecting no results as the route operation was just deleted
        self.cmd('network route-table route list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name),
            checks=NoneCheck())
        self.cmd('network route-table delete --resource-group {} --name {}'.format(self.resource_group, self.route_table_name))
        # Expecting no results as the route table was just deleted
        self.cmd('network route-table list --resource-group {}'.format(self.resource_group), checks=NoneCheck())

class NetworkVNetScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(NetworkVNetScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_vnet_test1'
        self.vnet_name = 'test-vnet'
        self.vnet_subnet_name = 'test-subnet1'
        self.resource_type = 'Microsoft.Network/virtualNetworks'

    def test_network_vnet(self):
        self.execute()

    def body(self):
        self.cmd('network vnet create --resource-group {} --name {}'.format(self.resource_group, self.vnet_name), checks=[
                JMESPathCheck('newVNet.provisioningState', 'Succeeded'), # verify the deployment result
                JMESPathCheck('newVNet.addressSpace.addressPrefixes[0]', '10.0.0.0/16')
            ])

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
            self.resource_group, self.vnet_name, vnet_addr_prefixes))

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

class NetworkSubnetSetScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(NetworkSubnetSetScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_subnet_set_test'
        self.vnet_name = 'test-vnet2'

    def test_subnet_set(self):
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

        #Test we can update the address space and nsg
        self.cmd('network vnet subnet update --resource-group {} --vnet-name {} --name {} --address-prefix {} --network-security-group {}'.format(self.resource_group, self.vnet_name, subnet_name, subnet_addr_prefix_new, nsg_name),
                 checks=[
                     JMESPathCheck('addressPrefix', subnet_addr_prefix_new),
                     JMESPathCheck('ends_with(@.networkSecurityGroup.id, `{}`)'.format('/' + nsg_name), True)
                     ])

        #Test we can get rid of the nsg.
        self.cmd('network vnet subnet update --resource-group {} --vnet-name {} --name {} --address-prefix {} --network-security-group {}'.format(self.resource_group, self.vnet_name, subnet_name, subnet_addr_prefix_new, '\"\"'),
                 checks=JMESPathCheck('networkSecurityGroup', None))

        self.cmd('network vnet delete --resource-group {} --name {}'.format(self.resource_group, self.vnet_name))
        self.cmd('network nsg delete --resource-group {} --name {}'.format(self.resource_group, nsg_name))

class NetworkVpnGatewayScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        super(NetworkVpnGatewayScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.placeholder_value = 'none_existent'

    def test_network_vpn_gateway(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        pv = self.placeholder_value
        allowed_exceptions = "The Resource 'Microsoft.Network/virtualNetworkGateways/{}' under resource group '{}' was not found.".format(pv, rg)
        self.cmd('network vpn-gateway delete --resource-group {0} --name {1}'.format(rg, pv))
        self.cmd('network vpn-gateway list --resource-group {0}'.format(rg), checks=NoneCheck())
        self.cmd('network vpn-gateway show --resource-group {0} --name {1}'.format(rg, pv),
            allowed_exceptions=allowed_exceptions)

class NetworkVpnConnectionScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        super(NetworkVpnConnectionScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.placeholder_value = 'none_existent'

    def test_network_vpn_connection(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        pv = self.placeholder_value
        allowed_exceptions = "The Resource 'Microsoft.Network/connections/{}' under resource group '{}' was not found.".format(pv, rg)
        self.cmd('network vpn-connection list --resource-group {0}'.format(rg))
        self.cmd('network vpn-connection show --resource-group {0} --name {1}'.format(rg, pv),
            allowed_exceptions=allowed_exceptions)
        self.cmd('network vpn-connection shared-key show --resource-group {0} --name {1}'.format(rg, pv),
            allowed_exceptions=allowed_exceptions)
        self.cmd('network vpn-connection delete --resource-group {0} --name {1}'.format(rg, pv))
        self.cmd('network vpn-connection shared-key reset --resource-group {0} --connection-name {1}'.format(rg, pv),
            allowed_exceptions=allowed_exceptions)
        self.cmd('network vpn-connection shared-key update --resource-group {0} --connection-name {1} --value {2}'.format(rg, pv, 'S4auzEfwZ6fN'),
            allowed_exceptions=allowed_exceptions)
