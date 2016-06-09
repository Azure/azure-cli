from azure.cli.utils.vcr_test_base import (VCRTestBase, ResourceGroupVCRTestBase, JMESPathCheck,
                                           NoneCheck)

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation

# TODO Make these full scenario tests when we can create the resources through network commands.
# So currently, the tests assume the resources have been created through some other means.

class NetworkUsageListScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkUsageListScenarioTest, self).__init__(__file__, test_method)

    def test_network_usage_list(self):
        self.execute()

    def body(self):
        self.cmd('network list-usages --location westus', checks=JMESPathCheck('type(@)', 'array'))

class NetworkNicListScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicListScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'TravisTestResourceGroup'

    def test_network_nic_list(self):
        self.execute()

    def body(self):
        self.cmd('network nic list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?resourceGroup == '{}' || resourceGroup =='{}']) == length(@)".format(self.resource_group, self.resource_group.lower()), True)
        ])

class NetworkAppGatewayScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkAppGatewayScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_tmp_test1'
        self.name = 'applicationGateway1'

    def test_network_app_gateway(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network application-gateway show --resource-group {} --name {}'.format(
            self.resource_group, self.name)):
            raise RuntimeError('Application gateway must be manually created in order to support this test.')

    def body(self):
        rg = self.resource_group
        name = self.name
        self.cmd('network application-gateway list-all', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1)
        ])
        self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        self.cmd('network application-gateway show --resource-group {} --name {}'.format(rg, name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', self.name),
            JMESPathCheck('resourceGroup', self.resource_group),
        ])
        self.cmd('network application-gateway stop --resource-group {} --name {}'.format(rg, name))
        self.cmd('network application-gateway start --resource-group {} --name {}'.format(rg, name))
        self.cmd('network application-gateway delete --resource-group {} --name {}'.format(rg, name))
        # Expecting the resource to no longer appear in the list
        self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=NoneCheck())

class NetworkPublicIpScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkPublicIpScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.public_ip_name = 'windowsvm'

    def test_network_public_ip(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network public-ip show --resource-group {} --name {}'.format(
            self.resource_group, self.public_ip_name)):
            raise RuntimeError('Public IP must be manually created in order to support this test.')

    def body(self):
        self.cmd('network public-ip list-all', checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network public-ip list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network public-ip show --resource-group {} --name {}'.format(
            self.resource_group, self.public_ip_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', self.public_ip_name),
            JMESPathCheck('resourceGroup', self.resource_group),
        ])
        self.cmd('network public-ip delete --resource-group {} --name {}'.format(
            self.resource_group, self.public_ip_name))
        self.cmd('network public-ip list --resource-group {}'.format(self.resource_group), checks=NoneCheck())

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
        self.cmd('network express-route circuit list-all', checks=[
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

class NetworkLoadBalancerScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkLoadBalancerScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.lb_name = 'cli-test-lb'
        self.resource_type = 'Microsoft.Network/loadBalancers'

    def test_network_load_balancer(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network lb show --resource-group {} --name {}'.format(
            self.resource_group, self.lb_name)):
            raise RuntimeError('Load balancer must be manually created in order to support this test.')

    def body(self):
        self.cmd('network lb list-all', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)
        ])
        self.cmd('network lb list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network lb show --resource-group {} --name {}'.format(self.resource_group, self.lb_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', self.resource_type),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('name', self.lb_name)
        ])
        self.cmd('network lb delete --resource-group {} --name {}'.format(self.resource_group, self.lb_name))
        # Expecting no results as we just deleted the only lb in the resource group
        self.cmd('network lb list --resource-group {}'.format(self.resource_group), checks=NoneCheck())

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

class NetworkNicScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkNicScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.name = 'cli-test-nic'
        self.resource_type = 'Microsoft.Network/networkInterfaces'

    def test_network_nic(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network nic show --resource-group {} --name {}'.format(
            self.resource_group, self.name)):
            raise RuntimeError('NIC must be manually created in order to support this test.')

    def body(self):
        self.cmd('network nic list-all', checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)
        ])
        self.cmd('network nic list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        self.cmd('network nic show --resource-group {} --name {}'.format(self.resource_group, self.name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type', self.resource_type),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('name', self.name)
        ])
        self.cmd('network nic delete --resource-group {} --name {}'.format(self.resource_group, self.name))

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
        self.resource_group = 'cliTestRg_securityGroups'
        self.nsg_name = 'cli-test-nsg'
        self.nsg_rule_name = 'web'
        self.resource_type = 'Microsoft.Network/networkSecurityGroups'
        self.deployment_name = 'nsgDeployment'

    def test_network_nsg(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        nsg = self.nsg_name
        nrn = self.nsg_rule_name
        rt = self.resource_type

        self.cmd('network nsg create --name {} -g {} --deployment-name deployment'.format(nsg, rg))
        self.cmd('network nsg rule create --access allow --destination-address-prefix 1234 --direction inbound --nsg-name {} --protocol * -g {} --source-address-prefix 789 -n {} --source-port-range * --destination-port-range 4444'.format(nsg, rg, nrn))

        self.cmd('network nsg list-all', checks=[
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
        if not self.cmd('network route-operation show --resource-group {} --route-table-name {} --name {}'.format( #pylint: disable=line-too-long
                self.resource_group, self.route_table_name, self.route_operation_name)):
            raise RuntimeError('Network route operation must be manually created in order to support this test.')

    def body(self):
        self.cmd('network route-table list-all',
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
        self.cmd('network route-operation list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name),
            checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network route-operation show --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_operation_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.route_operation_name),
                JMESPathCheck('resourceGroup', self.resource_group)
        ])
        self.cmd('network route-operation delete --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_operation_name))
        # Expecting no results as the route operation was just deleted
        self.cmd('network route-operation list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name),
            checks=NoneCheck())
        self.cmd('network route-table delete --resource-group {} --name {}'.format(self.resource_group, self.route_table_name))
        # Expecting no results as the route table was just deleted
        self.cmd('network route-table list --resource-group {}'.format(self.resource_group), checks=NoneCheck())

class NetworkVNetScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(NetworkVNetScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.vnet_name = 'test-vnet'
        self.vnet_subnet_name = 'test-subnet1'
        self.resource_type = 'Microsoft.Network/virtualNetworks'

    def test_network_vnet(self):
        self.execute()

    def set_up(self):
        if not self.cmd('network vnet show --resource-group {} --name {}'.format(
            self.resource_group, self.vnet_name)):
            raise RuntimeError('Network vnet must be manually created in order to support this test.')
        if not self.cmd('network vnet subnet show --resource-group {} --virtual-network-name {} --name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.vnet_name, self.vnet_subnet_name)):
            raise RuntimeError('Network vnet subnet must be manually created in order to support this test.')

    def body(self):
        self.cmd('network vnet list-all', checks=[
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
        self.cmd('network vnet subnet list --resource-group {} --virtual-network-name {}'.format(self.resource_group, self.vnet_name),
            checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network vnet subnet show --resource-group {} --virtual-network-name {} --name {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', self.vnet_subnet_name),
            JMESPathCheck('resourceGroup', self.resource_group)
        ])
        # Expecting the subnet to be listed
        self.cmd('network vnet subnet list --resource-group {} --virtual-network-name {}'.format(self.resource_group, self.vnet_name),
            checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_subnet_name), 1))
        self.cmd('network vnet subnet delete --resource-group {} --virtual-network-name {} --name {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name))
        # Expecting the subnet to not be listed
        self.cmd('network vnet subnet list --resource-group {} --virtual-network-name {}'.format(self.resource_group, self.vnet_name),
            checks=NoneCheck())
        # Expecting the vnet to appear in the list
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group),
            checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_name), 1))
        self.cmd('network vnet delete --resource-group {} --name {}'.format(self.resource_group, self.vnet_name))
        # Expecting the vnet we deleted to not appear in the list
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group),
            checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_name), 0))

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
        self.cmd('network vpn-connection shared-key set --resource-group {0} --connection-name {1} --value {2}'.format(rg, pv, 'S4auzEfwZ6fN'),
            allowed_exceptions=allowed_exceptions)

class NetworkSubnetCreateScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        super(NetworkSubnetCreateScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli_test1'
        self.placeholder_value = 'none_existent'
        self.address_prefix = '192.168.0/16'

    def test_network_subnet_create(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        pv = self.placeholder_value
        ap = self.address_prefix
        allowed_exceptions = "The Resource 'Microsoft.Network/virtualNetworks/{}' under resource group '{}' was not found.".format(pv, rg)
        self.cmd('network vnet subnet create --resource-group {0} --name {1} --virtual-network-name {1} --address-prefix {2}'.format(rg, pv, ap),
            allowed_exceptions=allowed_exceptions)
