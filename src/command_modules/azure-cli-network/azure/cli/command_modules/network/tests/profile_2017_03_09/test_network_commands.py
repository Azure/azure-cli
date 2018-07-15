# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
import os
import unittest

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, live_only
from knack.util import CLIError
from msrestazure.tools import resource_id

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class NetworkMultiIdsShowScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_multi_id')
    def test_network_multi_id_show(self, resource_group):

        self.cmd('network public-ip create -g {rg} -n pip1')
        self.cmd('network public-ip create -g {rg} -n pip2')

        pip1 = self.cmd('network public-ip show -g {rg} -n pip1').get_output_in_json()
        pip2 = self.cmd('network public-ip show -g {rg} -n pip2').get_output_in_json()
        self.cmd('network public-ip show --ids {} {}'.format(pip1['id'], pip2['id']),
                 checks=self.check('length(@)', 2))


class NetworkUsageListScenarioTest(ScenarioTest):

    def test_network_usage_list(self):
        self.cmd('network list-usages --location westus', checks=self.check('type(@)', 'array'))


class NetworkAppGatewayDefaultScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_basic')
    def test_network_app_gateway_with_defaults(self, resource_group):
        self.cmd('network application-gateway create -g {rg} -n ag1 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n ag1 --exists')
        self.cmd('network application-gateway update -g {rg} -n ag1 --no-wait --capacity 3 --sku standard_small --tags foo=doo')
        self.cmd('network application-gateway wait -g {rg} -n ag1 --updated')

        ag_list = self.cmd('network application-gateway list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?resourceGroup == '{}']) == length(@)".format(resource_group), True)
        ]).get_output_in_json()
        ag_count = len(ag_list)

        self.cmd('network application-gateway show --resource-group {rg} --name ag1', checks=[
            self.check('type(@)', 'object'),
            self.check('name', 'ag1'),
            self.check('resourceGroup', resource_group),
            self.check('frontendIpConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            self.check("frontendIpConfigurations[0].subnet.contains(id, 'default')", True)
        ])
        self.cmd('network application-gateway stop --resource-group {rg} -n ag1')
        self.cmd('network application-gateway start --resource-group {rg} -n ag1')
        self.cmd('network application-gateway delete --resource-group {rg} -n ag1')
        self.cmd('network application-gateway list --resource-group {rg}', checks=self.check('length(@)', ag_count - 1))


class NetworkAppGatewayExistingSubnetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_existing_subnet')
    def test_network_app_gateway_with_existing_subnet(self, resource_group):

        vnet = self.cmd('network vnet create -g {rg} -n vnet2 --subnet-name subnet1').get_output_in_json()
        subnet_id = vnet['newVNet']['subnets'][0]['id']
        self.kwargs['subnet_id'] = subnet_id

        # make sure it fails
        self.cmd('network application-gateway create -g {rg} -n ag2 --subnet {subnet_id} --subnet-address-prefix 10.0.0.0/28', expect_failure=True)
        # now verify it succeeds
        self.cmd('network application-gateway create -g {rg} -n ag2 --subnet {subnet_id} --servers 172.0.0.1 www.mydomain.com', checks=[
            self.check('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            self.check('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
        ])


class NetworkAppGatewayNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_no_wait')
    def test_network_app_gateway_no_wait(self, resource_group):

        self.cmd('network application-gateway create -g {rg} -n ag1 --no-wait', checks=self.is_empty())
        self.cmd('network application-gateway create -g {rg} -n ag2 --no-wait', checks=self.is_empty())
        self.cmd('network application-gateway wait -g {rg} -n ag1 --created --interval 120', checks=self.is_empty())
        self.cmd('network application-gateway wait -g {rg} -n ag2 --created --interval 120', checks=self.is_empty())
        self.cmd('network application-gateway show -g {rg} -n ag1', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])
        self.cmd('network application-gateway show -g {rg} -n ag2',
                 checks=self.check('provisioningState', 'Succeeded'))
        self.cmd('network application-gateway delete -g {rg} -n ag2 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n ag2 --deleted')


class NetworkAppGatewayPrivateIpScenarioTest20170601(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_private_ip')
    def test_network_app_gateway_with_private_ip(self, resource_group):

        self.kwargs.update({
            'private_ip': '10.0.0.15',
            'path': os.path.join(TEST_DIR, 'TestCert.pfx'),
            'pass': 'password'
        })
        self.cmd('network application-gateway create -g {rg} -n ag3 --subnet subnet1 --private-ip-address {private_ip} --cert-file "{path}" --cert-password {pass} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n ag3 --exists')
        self.cmd('network application-gateway show -g {rg} -n ag3', checks=[
            self.check('frontendIpConfigurations[0].privateIpAddress', '{private_ip}'),
            self.check('frontendIpConfigurations[0].privateIpAllocationMethod', 'Static')
        ])
        self.kwargs['path'] = os.path.join(TEST_DIR, 'TestCert2.pfx')
        self.cmd('network application-gateway ssl-cert update -g {rg} --gateway-name ag3 -n ag3SslCert --cert-file "{path}" --cert-password {pass}')
        self.cmd('network application-gateway wait -g {rg} -n ag3 --updated')


class NetworkAppGatewaySubresourceScenarioTest(ScenarioTest):

    def _create_ag(self):
        self.cmd('network application-gateway create -g {rg} -n {ag} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')

    @ResourceGroupPreparer(name_prefix='cli_test_ag_address_pool')
    def test_network_ag_address_pool(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway address-pool',
            'name': 'pool1'
        })
        self._create_ag()

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --servers 123.4.5.6 www.mydns.com')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('length(backendAddresses)', 2),
            self.check('backendAddresses[0].ipAddress', '123.4.5.6'),
            self.check('backendAddresses[1].fqdn', 'www.mydns.com'),
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --servers 5.4.3.2')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('length(backendAddresses)', 1),
            self.check('backendAddresses[0].ipAddress', '5.4.3.2')
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_frontend_port')
    def test_network_ag_frontend_port(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway frontend-port',
            'name': 'myport'
        })
        self._create_ag()

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --port 111')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('name', 'myport'),
            self.check('port', 111)
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --port 112')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('name', 'myport'),
            self.check('port', 112)
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_frontend_ip_public')
    def test_network_ag_frontend_ip_public(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway frontend-ip',
            'name': 'myfrontend',
            'ip1': 'myip1',
            'ip2': 'myip2'
        })
        self.cmd('network application-gateway create -g {rg} -n {ag} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')

        self.cmd('network public-ip create -g {rg} -n {ip1}')
        self.cmd('network public-ip create -g {rg} -n {ip2}')

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --public-ip-address {ip1}')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('subnet', None)
        ])

        # NOTE: Service states that public IP address cannot be changed. https://github.com/Azure/azure-cli/issues/4133
        # self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --public-ip-address {ip2}')
        # self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}')

        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_frontend_ip_private')
    def test_network_ag_frontend_ip_private(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway frontend-ip',
            'name': 'frontendip',
            'ip1': 'myip1',
            'vnet1': 'vnet1',
            'vnet2': 'vnet2',
            'subnet': 'subnet1'
        })
        self.cmd('network public-ip create -g {rg} -n {ip1}')
        self.cmd('network vnet create -g {rg} -n {vnet1} --subnet-name {subnet}')

        self.cmd('network application-gateway create -g {rg} -n {ag} --no-wait --public-ip-address {ip1} --vnet-name {vnet1} --subnet {subnet}')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --private-ip-address 10.0.0.10 --vnet-name {vnet1} --subnet {subnet}')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
        ])

        # NOTE: Service states that frontend subnet cannot differ from gateway subnet https://github.com/Azure/azure-cli/issues/4134
        # self.cmd('network vnet create -g {rg} -n {vnet2} --subnet-name {subnet} --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.10.0/24')
        # self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --private-ip-address 11.0.10.10 --vnet-name {vnet2} --subnet {subnet}')
        # self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}')

        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_http_listener')
    def test_network_ag_http_listener(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway http-listener',
            'name': 'mylistener'
        })
        self._create_ag()

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('hostName', 'www.test.com')
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --host-name www.test2.com')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('hostName', 'www.test2.com')
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_http_settings')
    def test_network_ag_http_settings(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway http-settings',
            'name': 'mysettings'
        })
        self._create_ag()

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --cookie-based-affinity Enabled --protocol https --timeout 50 --port 70')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('cookieBasedAffinity', 'Enabled'),
            self.check('port', 70),
            self.check('protocol', 'Https'),
            self.check('requestTimeout', 50)
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --cookie-based-affinity disabled --protocol http --timeout 40 --port 71')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('cookieBasedAffinity', 'Disabled'),
            self.check('port', 71),
            self.check('protocol', 'Http'),
            self.check('requestTimeout', 40)
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_rule')
    def test_network_ag_rule(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway rule',
            'name': 'myrule'
        })
        self._create_ag()

        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com')
        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener2 --no-wait --frontend-port appGatewayFrontendPort --host-name www.test2.com')

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --http-listener mylistener')
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}').get_output_in_json()
        self.assertTrue(rule['httpListener']['id'].endswith('mylistener'))
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --http-listener mylistener2')
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}').get_output_in_json()
        self.assertTrue(rule['httpListener']['id'].endswith('mylistener2'))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))


class NetworkAppGatewayPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_public_ip')
    def test_network_app_gateway_with_public_ip(self, resource_group):

        self.kwargs['ip'] = 'publicip4'
        self.cmd('network application-gateway create -g {rg} -n test4 --subnet subnet1 --vnet-name vnet4 --vnet-address-prefix 10.0.0.1/16 --subnet-address-prefix 10.0.0.1/28 --public-ip-address {ip}', checks=[
            self.check("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{ip}')", True),
            self.check('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')
        ])


class NetworkPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_public_ip')
    def test_network_public_ip(self, resource_group):

        self.kwargs.update({
            'ip1': 'pubipdns',
            'ip2': 'pubipnodns',
            'dns': 'woot'
        })
        self.cmd('network public-ip create -g {rg} -n {ip1} --dns-name {dns} --allocation-method static', checks=[
            self.check('publicIp.provisioningState', 'Succeeded'),
            self.check('publicIp.publicIpAllocationMethod', 'Static'),
            self.check('publicIp.dnsSettings.domainNameLabel', '{dns}')
        ])
        self.cmd('network public-ip create -g {rg} -n {ip2}', checks=[
            self.check('publicIp.provisioningState', 'Succeeded'),
            self.check('publicIp.publicIpAllocationMethod', 'Dynamic'),
            self.check('publicIp.dnsSettings', None)
        ])
        self.cmd('network public-ip update -g {rg} -n {ip2} --allocation-method static --dns-name wowza --idle-timeout 10', checks=[
            self.check('publicIpAllocationMethod', 'Static'),
            self.check('dnsSettings.domainNameLabel', 'wowza'),
            self.check('idleTimeoutInMinutes', 10)
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


class NetworkZonedPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_zoned_public_ip')
    def test_network_zoned_public_ip(self, resource_group):
        self.kwargs['ip'] = 'pubip'
        self.cmd('network public-ip create -g {rg} -n {ip} -l centralus')
        table_output = self.cmd('network public-ip show -g {rg} -n {ip} -otable').output
        self.assertEqual(table_output.splitlines()[2].split(), ['pubip', resource_group, 'centralus', 'Dynamic', '4', 'Succeeded'])


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
        self.cmd('network lb create -n {lb}2 -g {rg} --public-ip-address-allocation static')
        self.cmd('network public-ip show -g {rg} -n PublicIP{lb}2',
                 checks=self.check('publicIpAllocationMethod', 'Static'))

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


class NetworkLoadBalancerIpConfigScenarioTest(ScenarioTest):

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
                 checks=self.check("publicIpAddress.contains(id, 'publicip3')", True))

        # test generic update
        self.kwargs['ip2_id'] = resource_id(subscription=self.get_subscription_id(), resource_group=self.kwargs['rg'], namespace='Microsoft.Network', type='publicIPAddresses', name='publicip2')
        self.cmd('network lb frontend-ip update -g {rg} --lb-name lb1 -n ipconfig1 --set publicIpAddress.id="{ip2_id}"',
                 checks=self.check("publicIpAddress.contains(id, 'publicip2')", True))
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
            self.check('enableFloatingIp', True),
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
            self.check('enableFloatingIp', True),
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
        self.cmd('network local-gateway create --resource-group {rg} --name {lgw1} --gateway-ip-address 10.1.1.1')
        self.cmd('network local-gateway show --resource-group {rg} --name {lgw1}', checks=[
            self.check('type', '{rt}'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{lgw1}')])

        self.cmd('network local-gateway create --resource-group {rg} --name {lgw2} --gateway-ip-address 10.1.1.2 --local-address-prefixes 10.0.1.0/24',
                 checks=self.check('localNetworkAddressSpace.addressPrefixes[0]', '10.0.1.0/24'))

        self.cmd('network local-gateway list --resource-group {rg}',
                 checks=self.check('length(@)', 2))

        self.cmd('network local-gateway delete --resource-group {rg} --name {lgw1}')
        self.cmd('network local-gateway list --resource-group {rg}',
                 checks=self.check('length(@)', 1))


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
            self.check('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            self.check('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise optional parameters
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet_id} --ip-forwarding --private-ip-address {pri_ip} --public-ip-address {pub_ip} --internal-dns-name test --dns-servers 100.1.2.3 --lb-address-pools {address_pool_ids} --lb-inbound-nat-rules {rule_ids}', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Static'),
            self.check('NewNIC.ipConfigurations[0].privateIpAddress', '{pri_ip}'),
            self.check('NewNIC.enableIpForwarding', True),
            self.check('NewNIC.provisioningState', 'Succeeded'),
            self.check('NewNIC.dnsSettings.internalDnsNameLabel', 'test'),
            self.check('length(NewNIC.dnsSettings.dnsServers)', 1)
        ])
        # exercise creating with NSG
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet} --vnet-name {vnet} --network-security-group {nsg1}', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            self.check('NewNIC.enableIpForwarding', False),
            self.check("NewNIC.networkSecurityGroup.contains(id, '{nsg1}')", True),
            self.check('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise creating with NSG and Public IP
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet} --vnet-name {vnet} --network-security-group {nsg_id} --public-ip-address {pub_ip_id}', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            self.check('NewNIC.enableIpForwarding', False),
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
        self.cmd('network nic update -g {rg} -n {nic} --internal-dns-name noodle --ip-forwarding true --dns-servers "" --network-security-group {nsg2}', checks=[
            self.check('enableIpForwarding', True),
            self.check('dnsSettings.internalDnsNameLabel', 'noodle'),
            self.check('length(dnsSettings.dnsServers)', 0),
            self.check("networkSecurityGroup.contains(id, '{nsg2}')", True)
        ])
        # test generic update
        self.cmd('network nic update -g {rg} -n {nic} --set dnsSettings.internalDnsNameLabel=doodle --set enableIpForwarding=false', checks=[
            self.check('enableIpForwarding', False),
            self.check('dnsSettings.internalDnsNameLabel', 'doodle')
        ])

        self.cmd('network nic delete --resource-group {rg} --name {nic}')
        self.cmd('network nic list -g {rg}', checks=self.is_empty())


class NetworkSecurityGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_nsg')
    def test_network_nsg(self, resource_group):

        self.kwargs.update({
            'nsg': 'test-nsg1',
            'rule': 'web',
            'rt': 'Microsoft.Network/networkSecurityGroups'
        })

        self.cmd('network nsg create --name {nsg} -g {rg}')
        self.cmd('network nsg rule create --access allow --destination-address-prefix 1234 --direction inbound --nsg-name {nsg} --protocol * -g {rg} --source-address-prefix 789 -n {rule} --source-port-range * --destination-port-range 4444 --priority 1000')

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
        self.cmd('network nsg rule update -g {rg} --nsg-name {nsg} -n {rule} --direction {dir} --access {access} --destination-address-prefix {prefix} --protocol {protocol} --source-address-prefix {prefix} --source-port-range {ports} --destination-port-range {ports} --priority {priority} --description {desc}', checks=[
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

        self.cmd('network nsg rule delete --resource-group {rg} --nsg-name {nsg} --name {rule}')
        # Delete the network security group
        self.cmd('network nsg delete --resource-group {rg} --name {nsg}')
        # Expecting no results as we just deleted the only security group in the resource group
        self.cmd('network nsg list --resource-group {rg}', checks=self.is_empty())


class NetworkRouteTableOperationScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_route_table')
    def test_network_route_table_operation(self, resource_group):

        self.kwargs.update({
            'table': 'cli-test-route-table',
            'route': 'my-route',
            'rt': 'Microsoft.Network/routeTables'
        })

        self.cmd('network route-table create -n {table} -g {rg}')
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
        self.cmd('network route-table route delete --resource-group {rg} --route-table-name {table} --name {route}')
        self.cmd('network route-table route list --resource-group {rg} --route-table-name {table}', checks=self.is_empty())
        self.cmd('network route-table delete --resource-group {rg} --name {table}')
        self.cmd('network route-table list --resource-group {rg}', checks=self.is_empty())


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


class NetworkSubnetSetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_subnet_set_test')
    def test_network_subnet_set(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1',
            'vnet_prefix': '123.0.0.0/16',
            'subnet': 'default',
            'subnet_prefix': '123.0.0.0/24',
            'subnet_prefix2': '123.0.5.0/24',
            'nsg': 'test-vnet-nsg'
        })

        self.cmd('network vnet create --resource-group {rg} --name {vnet} --address-prefix {vnet_prefix} --subnet-name {subnet} --subnet-prefix {subnet_prefix}')
        self.cmd('network nsg create --resource-group {rg} --name {nsg}')

        # Test we can update the address space and nsg
        self.cmd('network vnet subnet update --resource-group {rg} --vnet-name {vnet} --name {subnet} --address-prefix {subnet_prefix2} --network-security-group {nsg}', checks=[
            self.check('addressPrefix', '{subnet_prefix2}'),
            self.check('ends_with(@.networkSecurityGroup.id, `/{nsg}`)', True)
        ])

        # test generic update
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --set addressPrefix=123.0.0.0/24',
                 checks=self.check('addressPrefix', '123.0.0.0/24'))

        # Test we can get rid of the nsg.
        self.cmd('network vnet subnet update --resource-group {rg} --vnet-name {vnet} --name {subnet} --address-prefix {subnet_prefix2} --network-security-group \"\"',
                 checks=self.check('networkSecurityGroup', None))

        self.cmd('network vnet delete --resource-group {rg} --name {vnet}')
        self.cmd('network nsg delete --resource-group {rg} --name {nsg}')


class NetworkTrafficManagerScenarioTest(ScenarioTest):

    @ResourceGroupPreparer('cli_test_traffic_manager')
    def test_network_traffic_manager(self, resource_group):

        self.kwargs.update({
            'tm': 'mytmprofile',
            'endpoint': 'myendpoint',
            'dns': 'mytrafficmanager001100a'
        })

        self.cmd('network traffic-manager profile check-dns -n myfoobar1')
        self.cmd('network traffic-manager profile create -n {tm} -g {rg} --routing-method priority --unique-dns-name {dns}',
                 checks=self.check('TrafficManagerProfile.trafficRoutingMethod', 'Priority'))
        self.cmd('network traffic-manager profile show -g {rg} -n {tm}',
                 checks=self.check('dnsConfig.relativeName', '{dns}'))
        self.cmd('network traffic-manager profile update -n {tm} -g {rg} --routing-method weighted',
                 checks=self.check('trafficRoutingMethod', 'Weighted'))
        self.cmd('network traffic-manager profile list -g {rg}')

        # Endpoint tests
        self.cmd('network traffic-manager endpoint create -n {endpoint} --profile-name {tm} -g {rg} --type externalEndpoints --weight 50 --target www.microsoft.com',
                 checks=self.check('type', 'Microsoft.Network/trafficManagerProfiles/externalEndpoints'))
        self.cmd('network traffic-manager endpoint update -n {endpoint} --profile-name {tm} -g {rg} --type externalEndpoints --weight 25 --target www.contoso.com', checks=[
            self.check('weight', 25),
            self.check('target', 'www.contoso.com')
        ])
        self.cmd('network traffic-manager endpoint show -g {rg} --profile-name {tm} -t externalEndpoints -n {endpoint}')
        self.cmd('network traffic-manager endpoint list -g {rg} --profile-name {tm} -t externalEndpoints',
                 checks=self.check('length(@)', 1))

        # ensure a profile with endpoints can be updated
        self.cmd('network traffic-manager profile update -n {tm} -g {rg}')

        self.cmd('network traffic-manager endpoint delete -g {rg} --profile-name {tm} -t externalEndpoints -n {endpoint}')
        self.cmd('network traffic-manager endpoint list -g {rg} --profile-name {tm} -t externalEndpoints',
                 checks=self.check('length(@)', 0))

        self.cmd('network traffic-manager profile delete -g {rg} -n {tm}')


class NetworkDnsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_dns')
    def test_network_dns(self, resource_group):

        self.kwargs['zone'] = 'myzone.com'

        self.cmd('network dns zone list')  # just verify is works (no Exception raised)
        self.cmd('network dns zone create -n {zone} -g {rg}')
        self.cmd('network dns zone list -g {rg}',
                 checks=self.check('length(@)', 1))

        base_record_sets = 2
        self.cmd('network dns zone show -n {zone} -g {rg}',
                 checks=self.check('numberOfRecordSets', base_record_sets))

        args = {
            'a': '--ipv4-address 10.0.0.10',
            'aaaa': '--ipv6-address 2001:db8:0:1:1:1:1:1',
            'caa': '--flags 0 --tag foo --value "my value"',
            'cname': '--cname mycname',
            'mx': '--exchange 12 --preference 13',
            'ns': '--nsdname foobar.com',
            'ptr': '--ptrdname foobar.com',
            'soa': '--email foo.com --expire-time 30 --minimum-ttl 20 --refresh-time 60 --retry-time 90 --serial-number 123',
            'srv': '--port 1234 --priority 1 --target target.com --weight 50',
            'txt': '--value some_text'
        }

        record_types = ['a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']

        for t in record_types:
            # test creating the record set and then adding records
            self.cmd('network dns record-set {0} create -n myrs{0} -g {{rg}} --zone-name {{zone}}'.format(t))
            add_command = 'set-record' if t == 'cname' else 'add-record'
            self.cmd('network dns record-set {0} {2} -g {{rg}} --zone-name {{zone}} --record-set-name myrs{0} {1}'.format(t, args[t], add_command))
            # test creating the record set at the same time you add records
            self.cmd('network dns record-set {0} {2} -g {{rg}} --zone-name {{zone}} --record-set-name myrs{0}alt {1}'.format(t, args[t], add_command))

        self.cmd('network dns record-set a add-record -g {rg} --zone-name {zone} --record-set-name myrsa --ipv4-address 10.0.0.11')
        self.cmd('network dns record-set soa update -g {{rg}} --zone-name {{zone}} {0}'.format(args['soa']))

        long_value = '0123456789' * 50
        self.cmd('network dns record-set txt add-record -g {{rg}} -z {{zone}} -n longtxt -v {0}'.format(long_value))

        typed_record_sets = 2 * len(record_types) + 1
        self.cmd('network dns zone show -n {zone} -g {rg}',
                 checks=self.check('numberOfRecordSets', base_record_sets + typed_record_sets))
        self.cmd('network dns record-set a show -n myrsa -g {rg} --zone-name {zone}',
                 checks=self.check('length(arecords)', 2))

        # test list vs. list type
        self.cmd('network dns record-set list -g {rg} -z {zone}',
                 checks=self.check('length(@)', base_record_sets + typed_record_sets))

        self.cmd('network dns record-set txt list -g {rg} -z {zone}',
                 checks=self.check('length(@)', 3))

        for t in record_types:
            self.cmd('network dns record-set {0} remove-record -g {{rg}} --zone-name {{zone}} --record-set-name myrs{0} {1}'.format(t, args[t]))

        self.cmd('network dns record-set a show -n myrsa -g {rg} --zone-name {zone}',
                 checks=self.check('length(arecords)', 1))

        self.cmd('network dns record-set a remove-record -g {rg} --zone-name {zone} --record-set-name myrsa --ipv4-address 10.0.0.11')

        self.cmd('network dns record-set a show -n myrsa -g {rg} --zone-name {zone}',
                 expect_failure=True)

        self.cmd('network dns record-set a delete -n myrsa -g {rg} --zone-name {zone} -y')
        self.cmd('network dns record-set a show -n myrsa -g {rg} --zone-name {zone}', expect_failure=True)

        self.cmd('network dns zone delete -g {rg} -n {zone} -y',
                 checks=self.is_empty())


class NetworkZoneImportExportTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_dns_zone_import_export')
    def test_network_dns_zone_import_export(self, resource_group):
        self.kwargs.update({
            'zone': 'myzone.com',
            'path': os.path.join(TEST_DIR, 'zone_files', 'zone1.txt')
        })
        self.cmd('network dns zone import -n {zone} -g {rg} --file-name "{path}"')
        self.cmd('network dns zone export -n {zone} -g {rg}')

# TODO: Troubleshoot VNET gateway issue and re-enable...
# class NetworkWatcherScenarioTest(ScenarioTest):
#    import mock

#    def _mock_thread_count():
#        return 1

#    @mock.patch('azure.cli.command_modules.vm._actions._get_thread_count', _mock_thread_count)
#    @ResourceGroupPreparer(name_prefix='cli_test_network_watcher', location='westcentralus')
#    @StorageAccountPreparer(name_prefix='clitestnw', location='westcentralus')
#    def test_network_watcher(self, resource_group, storage_account):

#        self.kwargs.update({
#            'loc': 'westcentralus',
#            'vm': 'vm1',
#            'nsg': 'msg1',
#            'capture': 'capture1'
#        })

#        self.cmd('network watcher configure -g {rg} --locations westus westus2 westcentralus --enabled')
#        self.cmd('network watcher configure --locations westus westus2 --tags foo=doo')
#        self.cmd('network watcher configure -l westus2 --enabled false')
#        self.cmd('network watcher list')

#        # set up resource to troubleshoot
#        self.cmd('storage container create -n troubleshooting --account-name {sa}')
#        sa = self.cmd('storage account show -g {rg} -n {sa}').get_output_in_json()
#        self.kwargs['storage_path'] = sa['primaryEndpoints']['blob'] + 'troubleshooting'
#        self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name GatewaySubnet')
#        self.cmd('network public-ip create -g {rg} -n vgw1-pip')
#        self.cmd('network vnet-gateway create -g {rg} -n vgw1 --vnet vnet1 --public-ip-address vgw1-pip --no-wait')

#        # create VM with NetworkWatcher extension
#        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --authentication-type password --admin-username deploy --admin-password PassPass10!)')
#        self.cmd('vm extension set -g {rg} --vm-name {vm} -n NetworkWatcherAgentLinux --publisher Microsoft.Azure.NetworkWatcher')

#        self.cmd('network watcher show-topology -g {rg}')

#        self.cmd('network watcher test-ip-flow -g {rg} --vm {vm} --direction inbound --local 10.0.0.4:22 --protocol tcp --remote 100.1.2.3:*')
#        self.cmd('network watcher test-ip-flow -g {rg} --vm {vm} --direction outbound --local 10.0.0.4:* --protocol tcp --remote 100.1.2.3:80')

#        self.cmd('network watcher show-security-group-view -g {rg} --vm {vm}')

#        self.cmd('network watcher show-next-hop -g {rg} --vm {vm} --source-ip 123.4.5.6 --dest-ip 10.0.0.6')

#        self.cmd('network watcher test-connectivity -g {rg} --source-resource {vm} --dest-address www.microsoft.com --dest-port 80')

#        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --enabled --retention 5 --storage-account {sa}')
#        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --retention 0')
#        self.cmd('network watcher flow-log show -g {rg} --nsg {nsg}')

#        # test packet capture
#        self.cmd('network watcher packet-capture create -g {rg} --vm {vm} -n {capture} --file-path capture/capture.cap')
#        self.cmd('network watcher packet-capture show -l {loc} -n {capture}')
#        self.cmd('network watcher packet-capture stop -l {loc} -n {capture}')
#        self.cmd('network watcher packet-capture show-status -l {loc} -n {capture}')
#        self.cmd('network watcher packet-capture list -l {loc}')
#        self.cmd('network watcher packet-capture delete -l {loc} -n {capture}')
#        self.cmd('network watcher packet-capture list -l {loc}')

#        # test troubleshooting
#        self.cmd('network vnet-gateway wait -g {rg} -n vgw1 --created')
#        self.cmd('network watcher troubleshooting start --resource vgw1 -t vnetGateway -g {rg} --storage-account {sa} --storage-path {storage_path}')
#        self.cmd('network watcher troubleshooting show --resource vgw1 -t vnetGateway -g {rg}')


if __name__ == '__main__':
    unittest.main()
