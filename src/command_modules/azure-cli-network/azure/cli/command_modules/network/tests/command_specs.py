# AZURE CLI NETWORK TEST DEFINITIONS

from azure.cli.utils.command_test_script import CommandTestScript, JMESPathComparator

#pylint: disable=method-hidden

# TODO Make these full scenario tests when we can create the resources through network commands.
# So currently, the tests assume the resources have been created through some other means.

class NetworkUsageListScenarioTest(CommandTestScript):

    def __init__(self):
        super(NetworkUsageListScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('network list-usages --location westus', JMESPathComparator('type(@)', 'array'))

class NetworkNicListScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'TravisTestResourceGroup'
        super(NetworkNicListScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('network nic list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator(
                "length([?resourceGroup == '{}' || resourceGroup =='{}']) == length(@)".format(
                    self.resource_group, self.resource_group.lower()),
                True)])

class NetworkAppGatewayScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_tmp_test1'
        self.name = 'applicationGateway1'
        super(NetworkAppGatewayScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network application-gateway show --resource-group {} --name {}'.format(
            self.resource_group, self.name)):
            raise RuntimeError('Application gateway must be manually created in order to support this test.')

    def test_body(self):
        self.test('network application-gateway list-all', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator('length(@)', 1)])
        self.test('network application-gateway list --resource-group {}'.format(
            self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator('length(@)', 1),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network application-gateway show --resource-group {} --name {}'.format(
            self.resource_group, self.name), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('name', self.name),
            JMESPathComparator('resourceGroup', self.resource_group),
            ])
        self.test('network application-gateway stop --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)
        self.test('network application-gateway start --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)
        self.test('network application-gateway delete --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)
        # Expecting the resource to no longer appear in the list
        self.test('network application-gateway list --resource-group {}'.format(
            self.resource_group), None)

class NetworkPublicIpScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.public_ip_name = 'windowsvm'
        super(NetworkPublicIpScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network public-ip show --resource-group {} --name {}'.format(
            self.resource_group, self.public_ip_name)):
            raise RuntimeError('Public IP must be manually created in order to support this test.')

    def test_body(self):
        self.test('network public-ip list-all', JMESPathComparator('type(@)', 'array'))
        self.test('network public-ip list --resource-group {}'.format(self.resource_group),
        [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)
        ])
        self.test('network public-ip show --resource-group {} --name {}'.format(
            self.resource_group, self.public_ip_name),
        [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('name', self.public_ip_name),
            JMESPathComparator('resourceGroup', self.resource_group),
        ])
        self.test('network public-ip delete --resource-group {} --name {}'.format(
            self.resource_group, self.public_ip_name), None)
        self.test('network public-ip list --resource-group {}'.format(self.resource_group), None)

class NetworkExpressRouteScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.express_route_name = 'test_route'
        self.resource_type = 'Microsoft.Network/expressRouteCircuits'
        super(NetworkExpressRouteScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network express-route circuit show --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name)):
            raise RuntimeError('Express route must be manually created in order to support this test.')

    def test_body(self):
        self.test('network express-route circuit list-all', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)
            ])
        self.test('network express-route circuit list --resource-group {}'.format(
            self.resource_group),
        [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)
        ])
        self.test('network express-route circuit show --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type', self.resource_type),
                JMESPathComparator('name', self.express_route_name),
                JMESPathComparator('resourceGroup', self.resource_group),
            ])
        self.test('network express-route circuit get-stats --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name), JMESPathComparator('type(@)', 'object'))
        self.test('network express-route circuit-auth list --resource-group {} --circuit-name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name), None)
        self.test('network express-route circuit-peering list --resource-group {} --circuit-name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name), None)
        self.test('network express-route service-provider list', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          'Microsoft.Network/expressRouteServiceProviders'), True)])
        self.test('network express-route circuit delete --resource-group {} --name {}'.format(
            self.resource_group, self.express_route_name), None)
        # Expecting no results as we just deleted the only express route in the resource group
        self.test('network express-route circuit list --resource-group {}'.format(
            self.resource_group), None)

class NetworkExpressRouteCircuitScenarioTest(CommandTestScript):

    def __init__(self):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        self.resource_group = 'cli_test1'
        self.express_route_name = 'test_route'
        self.placeholder_value = 'none_existent'
        super(NetworkExpressRouteCircuitScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('network express-route circuit-auth show --resource-group {0} --circuit-name {1} --name {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name, self.placeholder_value), None)
        self.test('network express-route circuit-auth delete --resource-group {0} --circuit-name {1} --name {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name, self.placeholder_value), None)
        self.test('network express-route circuit-peering delete --resource-group {0} --circuit-name {1} --name {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name, self.placeholder_value), None)
        self.test('network express-route circuit-peering show --resource-group {0} --circuit-name {1} --name {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name, self.placeholder_value), None)
        self.test('network express-route circuit list-arp --resource-group {0} --name {1} --peering-name {2} --device-path {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name, self.placeholder_value), None)
        self.test('network express-route circuit list-routes --resource-group {0} --name {1} --peering-name {2} --device-path {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.express_route_name, self.placeholder_value), None)

class NetworkLoadBalancerScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.lb_name = 'cli-test-lb'
        self.resource_type = 'Microsoft.Network/loadBalancers'
        super(NetworkLoadBalancerScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network lb show --resource-group {} --name {}'.format(
            self.resource_group, self.lb_name)):
            raise RuntimeError('Load balancer must be manually created in order to support this test.')

    def test_body(self):
        self.test('network lb list-all', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True)])
        self.test('network lb list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network lb show --resource-group {} --name {}'.format(
            self.resource_group, self.lb_name), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('type', self.resource_type),
            JMESPathComparator('resourceGroup', self.resource_group),
            JMESPathComparator('name', self.lb_name)])
        self.test('network lb delete --resource-group {} --name {}'.format(
            self.resource_group, self.lb_name), None)
        # Expecting no results as we just deleted the only lb in the resource group
        self.test('network lb list --resource-group {}'.format(self.resource_group), None)

class NetworkLocalGatewayScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.name = 'cli-test-loc-gateway'
        self.resource_type = 'Microsoft.Network/localNetworkGateways'
        super(NetworkLocalGatewayScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network local-gateway show --resource-group {} --name {}'.format(
            self.resource_group, self.name)):
            raise RuntimeError('Local gateway must be manually created in order to support this test.')

    def test_body(self):
        self.test('network local-gateway list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network local-gateway show --resource-group {} --name {}'.format(
            self.resource_group, self.name), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('type', self.resource_type),
            JMESPathComparator('resourceGroup', self.resource_group),
            JMESPathComparator('name', self.name)])
        self.test('network local-gateway delete --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)
        # Expecting no results as we just deleted the only local gateway in the resource group
        self.test('network local-gateway list --resource-group {}'.format(self.resource_group),
                  None)

class NetworkNicScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.name = 'cli-test-nic'
        self.resource_type = 'Microsoft.Network/networkInterfaces'
        super(NetworkNicScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network nic show --resource-group {} --name {}'.format(
            self.resource_group, self.name)):
            raise RuntimeError('NIC must be manually created in order to support this test.')

    def test_body(self):
        self.test('network nic list-all', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True)])
        self.test('network nic list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network nic show --resource-group {} --name {}'.format(
            self.resource_group, self.name), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('type', self.resource_type),
            JMESPathComparator('resourceGroup', self.resource_group),
            JMESPathComparator('name', self.name)])
        self.test('network nic delete --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)

class NetworkNicScaleSetScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.vmss_name = 'clitestvm'
        self.nic_name = 'clitestvmnic'
        self.vm_index = 0
        self.resource_type = 'Microsoft.Network/networkInterfaces'
        super(NetworkNicScaleSetScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network nic scale-set show --resource-group {} --vm-scale-set {} --vm-index {} --name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.vmss_name, self.vm_index, self.nic_name)):
            raise RuntimeError('VM scale set NIC must be manually created in order to support this test.')

    def test_body(self):
        self.test('network nic scale-set list --resource-group {} --vm-scale-set {}'.format(
                  self.resource_group, self.vmss_name), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator("length([?type == '{}']) == length(@)".format(
                            self.resource_type), True),
                JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                            self.resource_group), True)])
        self.test('network nic scale-set list-vm-nics --resource-group {} --vm-scale-set {} --vm-index {}'.format( #pylint: disable=line-too-long
                  self.resource_group, self.vmss_name, self.vm_index), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator("length([?type == '{}']) == length(@)".format(
                            self.resource_type), True),
                JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                            self.resource_group), True)])
        self.test('network nic scale-set show --resource-group {} --vm-scale-set {} --vm-index {} --name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.vmss_name, self.vm_index, self.nic_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.nic_name),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('type', self.resource_type)])

class NetworkSecurityGroupScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cliTestRg_securityGroups'
        self.nsg_name = 'cli-test-nsg'
        self.nsg_rule_name = 'web'
        self.resource_type = 'Microsoft.Network/networkSecurityGroups'
        super(NetworkSecurityGroupScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network nsg show --resource-group {} --name {}'.format(
            self.resource_group, self.nsg_name)):
            raise RuntimeError('Network security group must be manually created in order to support this test.')
        if not self.run('network nsg-rule show --resource-group {} --nsg-name {} --name {}'.format(
            self.resource_group, self.nsg_name, self.nsg_rule_name)):
            raise RuntimeError('Network security group rule must be manually created in order to support this test.')

    def test_body(self):
        self.test('network nsg list-all', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True)])
        self.test('network nsg list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network nsg show --resource-group {} --name {}'.format(
            self.resource_group, self.nsg_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type', self.resource_type),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('name', self.nsg_name)])
        # Test for the manually added nsg rule
        self.test('network nsg-rule list --resource-group {} --nsg-name {}'.format(
            self.resource_group, self.nsg_name), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', 1),
                JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network nsg-rule show --resource-group {} --nsg-name {} --name {}'.format(
            self.resource_group, self.nsg_name, self.nsg_rule_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('name', self.nsg_rule_name)])
        self.test('network nsg-rule delete --resource-group {} --nsg-name {} --name {}'.format(
            self.resource_group, self.nsg_name, self.nsg_rule_name), None)
        # Delete the network security group
        self.test('network nsg delete --resource-group {} --name {}'.format(
            self.resource_group, self.nsg_name), None)
        # Expecting no results as we just deleted the only security group in the resource group
        self.test('network nsg list --resource-group {}'.format(self.resource_group), None)

class NetworkRouteTableOperationScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.route_table_name = 'cli-test-route-table'
        self.route_operation_name = 'my-route'
        self.resource_type = 'Microsoft.Network/routeTables'
        super(NetworkRouteTableOperationScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network route-table show --resource-group {} --name {}'.format(
                self.resource_group, self.route_table_name)):
            raise RuntimeError('Network route table must be manually created in order to support this test.')
        if not self.run('network route-operation show --resource-group {} --route-table-name {} --name {}'.format( #pylint: disable=line-too-long
                self.resource_group, self.route_table_name, self.route_operation_name)):
            raise RuntimeError('Network route operation must be manually created in order to support this test.')

    def test_body(self):
        self.test('network route-table list-all', [
                JMESPathComparator('type(@)', 'array')])
        self.test('network route-table list --resource-group {}'.format(self.resource_group), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', 1),
                JMESPathComparator('[0].name', self.route_table_name),
                JMESPathComparator('[0].resourceGroup', self.resource_group),
                JMESPathComparator('[0].type', self.resource_type)])
        self.test('network route-table show --resource-group {} --name {}'.format(
                self.resource_group, self.route_table_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.route_table_name),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('type', self.resource_type)])
        self.test('network route-operation list --resource-group {} --route-table-name {}'.format(
                self.resource_group, self.route_table_name), [
                JMESPathComparator('type(@)', 'array')])
        self.test('network route-operation show --resource-group {} --route-table-name {} --name {}'.format( #pylint: disable=line-too-long
                self.resource_group, self.route_table_name, self.route_operation_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.route_operation_name),
                JMESPathComparator('resourceGroup', self.resource_group)])
        self.test('network route-operation delete --resource-group {} --route-table-name {} --name {}'.format( #pylint: disable=line-too-long
                self.resource_group, self.route_table_name, self.route_operation_name), None)
        # Expecting no results as the route operation was just deleted
        self.test('network route-operation list --resource-group {} --route-table-name {}'.format(
                self.resource_group, self.route_table_name), None)
        self.test('network route-table delete --resource-group {} --name {}'.format(
                self.resource_group, self.route_table_name), None)
        # Expecting no results as the route table was just deleted
        self.test('network route-table list --resource-group {}'.format(self.resource_group), None)

class NetworkVNetScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cli_test1'
        self.vnet_name = 'test-vnet'
        self.vnet_subnet_name = 'test-subnet1'
        self.resource_type = 'Microsoft.Network/virtualNetworks'
        super(NetworkVNetScenarioTest, self).__init__(self.set_up, self.test_body, None)

    def set_up(self):
        if not self.run('network vnet show --resource-group {} --name {}'.format(
            self.resource_group, self.vnet_name)):
            raise RuntimeError('Network vnet must be manually created in order to support this test.')
        if not self.run('network vnet subnet show --resource-group {} --virtual-network-name {} --name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.vnet_name, self.vnet_subnet_name)):
            raise RuntimeError('Network vnet subnet must be manually created in order to support this test.')

    def test_body(self):
        self.test('network vnet list-all', [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True)])
        self.test('network vnet list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?type == '{}']) == length(@)".format(
                          self.resource_type), True),
            JMESPathComparator("length([?resourceGroup == '{}']) == length(@)".format(
                          self.resource_group), True)])
        self.test('network vnet show --resource-group {} --name {}'.format(
            self.resource_group, self.vnet_name), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('name', self.vnet_name),
            JMESPathComparator('resourceGroup', self.resource_group),
            JMESPathComparator('type', self.resource_type)])
        self.test('network vnet subnet list --resource-group {} --virtual-network-name {}'.format(
            self.resource_group, self.vnet_name), JMESPathComparator('type(@)', 'array'))
        self.test('network vnet subnet show --resource-group {} --virtual-network-name {} --name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.vnet_name, self.vnet_subnet_name), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('name', self.vnet_subnet_name),
            JMESPathComparator('resourceGroup', self.resource_group)])
        # Expecting the subnet to be listed
        self.test('network vnet subnet list --resource-group {} --virtual-network-name {}'.format(
                      self.resource_group, self.vnet_name),
                  JMESPathComparator("length([?name == '{}'])".format(self.vnet_subnet_name), 1))
        self.test('network vnet subnet delete --resource-group {} --virtual-network-name {} --name {}'.format( #pylint: disable=line-too-long
                  self.resource_group, self.vnet_name, self.vnet_subnet_name), None)
        # Expecting the subnet to not be listed
        self.test('network vnet subnet list --resource-group {} --virtual-network-name {}'.format(
                      self.resource_group, self.vnet_name), None)
        # Expecting the vnet to appear in the list
        self.test('network vnet list --resource-group {}'.format(self.resource_group),
                  JMESPathComparator("length([?name == '{}'])".format(self.vnet_name), 1))
        self.test('network vnet delete --resource-group {} --name {}'.format(
            self.resource_group, self.vnet_name), None)
        # Expecting the vnet we deleted to not appear in the list
        self.test('network vnet list --resource-group {}'.format(self.resource_group),
                  JMESPathComparator("length([?name == '{}'])".format(self.vnet_name), 0))

class NetworkVpnGatewayScenarioTest(CommandTestScript):

    def __init__(self):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        self.resource_group = 'cli_test1'
        self.placeholder_value = 'none_existent'
        super(NetworkVpnGatewayScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('network vpn-gateway delete --resource-group {0} --name {1}'.format(
            self.resource_group, self.placeholder_value), None)
        self.test('network vpn-gateway list --resource-group {0}'.format(self.resource_group), None)
        self.test('network vpn-gateway show --resource-group {0} --name {1}'.format(
            self.resource_group, self.placeholder_value), None)
        self.test('network vpn-gateway reset --resource-group {0} --name {1} --parameters {1}'.format(
            self.resource_group, self.placeholder_value), None)

class NetworkVpnConnectionScenarioTest(CommandTestScript):

    def __init__(self):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        self.resource_group = 'cli_test1'
        self.placeholder_value = 'none_existent'
        super(NetworkVpnConnectionScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('network vpn-connection list --resource-group {0}'.format(
            self.resource_group), None)
        self.test('network vpn-connection show --resource-group {0} --name {1}'.format(
            self.resource_group, self.placeholder_value), None)
        self.test('network vpn-connection shared-key show --resource-group {0} --name {1}'.format( #pylint: disable=line-too-long
            self.resource_group, self.placeholder_value), None)
        self.test('network vpn-connection delete --resource-group {0} --name {1}'.format(
            self.resource_group, self.placeholder_value), None)
        self.test('network vpn-connection shared-key reset --resource-group {0} --connection-name {1}'.format( #pylint: disable=line-too-long
            self.resource_group, self.placeholder_value), None)
        self.test('network vpn-connection shared-key set --resource-group {0} --connection-name {1} --value {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.placeholder_value, 'S4auzEfwZ6fN'), None)

class NetworkSubnetCreateScenarioTest(CommandTestScript):

    def __init__(self):
        # The resources for this test did not exist so the commands will return 404 errors.
        # So this test is for the command execution itself.
        self.resource_group = 'cli_test1'
        self.placeholder_value = 'none_existent'
        self.address_prefix = '192.168.0/16'
        super(NetworkSubnetCreateScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('network vnet subnet create --resource-group {0} --name {1} --virtual-network-name {1} --address-prefix {2}'.format( #pylint: disable=line-too-long
            self.resource_group, self.placeholder_value, self.address_prefix), None)

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'network_usage_list',
        'command': NetworkUsageListScenarioTest()
    },
    {
        'test_name': 'network_nic_list',
        'command': NetworkNicListScenarioTest()
    },
    {
        'test_name': 'network_app_gateway',
        'command': NetworkAppGatewayScenarioTest()
    },
    {
        'test_name': 'network_public_ip',
        'command': NetworkPublicIpScenarioTest()
    },
    {
        'test_name': 'network_express_route',
        'command': NetworkExpressRouteScenarioTest()
    },
    {
        'test_name': 'network_express_route_circuit',
        'command': NetworkExpressRouteCircuitScenarioTest()
    },
    {
        'test_name': 'network_load_balancer',
        'command': NetworkLoadBalancerScenarioTest()
    },
    {
        'test_name': 'network_local_gateway',
        'command': NetworkLocalGatewayScenarioTest()
    },
    {
        'test_name': 'network_nic',
        'command': NetworkNicScenarioTest()
    },
    {
        'test_name': 'network_nic_scaleset',
        'command': NetworkNicScaleSetScenarioTest()
    },
    {
        'test_name': 'network_nsg',
        'command': NetworkSecurityGroupScenarioTest()
    },
    {
        'test_name': 'network_route_table_operation',
        'command': NetworkRouteTableOperationScenarioTest()
    },
    {
        'test_name': 'network_vnet',
        'command': NetworkVNetScenarioTest()
    },
    {
        'test_name': 'network_vpn_gateway',
        'command': NetworkVpnGatewayScenarioTest()
    },
    {
        'test_name': 'network_vpn_connection',
        'command': NetworkVpnConnectionScenarioTest()
    },
    {
        'test_name': 'network_subnet_create',
        'command': NetworkSubnetCreateScenarioTest()
    },
]
