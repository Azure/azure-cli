# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
import os
import unittest

from azure.cli.core.util import CLIError
from msrestazure.tools import resource_id
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import supported_api_version, ResourceType

from azure.cli.testsdk import JMESPathCheck as JMESPathCheckV2
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, api_version_constraint, live_only
from azure.cli.testsdk.vcr_test_base import (VCRTestBase, ResourceGroupVCRTestBase, JMESPathCheck, NoneCheck, MOCKED_SUBSCRIPTION_ID)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-08-01')
class NetworkLoadBalancerWithSku(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_sku')
    def test_network_lb_sku(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'lb': 'lb1',
            'sku': 'standard',
            'location': 'eastus2',
            'ip': 'pubip1'
        }

        self.cmd('network lb create -g {rg} -l {location} -n {lb} --sku {sku} --public-ip-address {ip}'.format(**kwargs))
        self.cmd('network lb show -g {rg} -n {lb}'.format(**kwargs), checks=[
            JMESPathCheckV2('sku.name', 'Standard')
        ])
        self.cmd('network public-ip show -g {rg} -n {ip}'.format(**kwargs), checks=[
            JMESPathCheckV2('sku.name', 'Standard'),
            JMESPathCheckV2('publicIpAllocationMethod', 'Static')
        ])


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkLoadBalancerWithZone(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_zone')
    def test_network_lb_zone(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'lb': 'lb1',
            'zone': '2',
            'location': 'eastus2',
            'ip': 'pubip1'
        }

        # LB with public ip
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --public-ip-zone {zone} --public-ip-address {ip}'.format(**kwargs))
        # No zone on LB and its front-ip-config
        self.cmd('network lb show -g {rg} -n {lb}'.format(**kwargs), checks=[
            JMESPathCheckV2("frontendIpConfigurations[0].zones", None),
            JMESPathCheckV2("zones", None)
        ])
        # Zone on public-ip which LB uses to infer the zone
        self.cmd('network public-ip show -g {rg} -n {ip}'.format(**kwargs), checks=[
            JMESPathCheckV2('zones[0]', kwargs['zone'])
        ])

        # LB w/o public ip, so called ILB
        kwargs['lb'] = 'lb2'
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --frontend-ip-zone {zone} --public-ip-address "" --vnet-name vnet1 --subnet subnet1'.format(**kwargs))
        # Zone on front-ip-config, and still no zone on LB resource
        self.cmd('network lb show -g {rg} -n {lb}'.format(**kwargs), checks=[
            JMESPathCheckV2("frontendIpConfigurations[0].zones[0]", kwargs['zone']),
            JMESPathCheckV2("zones", None)
        ])
        # add a second frontend ip configuration
        self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb} -n LoadBalancerFrontEnd2 -z {zone}  --vnet-name vnet1 --subnet subnet1'.format(**kwargs), checks=[
            JMESPathCheckV2("zones", [kwargs['zone']])
        ])


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-08-01')
class NetworkPublicIpWithSku(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_sku')
    def test_network_public_ip_sku(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'sku': 'standard',
            'location': 'eastus2',
            'ip': 'pubip1'
        }

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip} --sku {sku}'.format(**kwargs))
        self.cmd('network public-ip show -g {rg} -n {ip}'.format(**kwargs), checks=[
            JMESPathCheckV2('sku.name', 'Standard'),
            JMESPathCheckV2('publicIpAllocationMethod', 'Static')
        ])


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
        self.cmd('network public-ip show --ids {} {}'.format(pip1['id'], pip2['id']), checks=JMESPathCheck('length(@)', 2))


class NetworkUsageListScenarioTest(VCRTestBase):
    def __init__(self, test_method):
        super(NetworkUsageListScenarioTest, self).__init__(__file__, test_method)

    def test_network_usage_list(self):
        self.execute()

    def body(self):
        self.cmd('network list-usages --location westus', checks=JMESPathCheck('type(@)', 'array'))


class NetworkAppGatewayDefaultScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_basic')
    def test_network_app_gateway_with_defaults(self, resource_group):
        rg = resource_group
        self.cmd('network application-gateway create -g {} -n ag1 --no-wait'.format(rg))
        self.cmd('network application-gateway wait -g {} -n ag1 --exists'.format(rg))
        self.cmd('network application-gateway update -g {} -n ag1 --no-wait --capacity 3 --sku standard_small --tags foo=doo'.format(rg))
        self.cmd('network application-gateway wait -g {} -n ag1 --updated'.format(rg))

        ag_list = self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=[
            JMESPathCheckV2('type(@)', 'array'),
            JMESPathCheckV2("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ]).get_output_in_json()
        ag_count = len(ag_list)

        self.cmd('network application-gateway show --resource-group {} --name ag1'.format(rg), checks=[
            JMESPathCheckV2('type(@)', 'object'),
            JMESPathCheckV2('name', 'ag1'),
            JMESPathCheckV2('resourceGroup', rg),
            JMESPathCheckV2('frontendIpConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheckV2("frontendIpConfigurations[0].subnet.contains(id, 'default')", True)
        ])
        self.cmd('network application-gateway show-backend-health -g {} -n ag1'.format(rg))
        self.cmd('network application-gateway stop --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway start --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway delete --resource-group {} -n ag1'.format(rg))
        self.cmd('network application-gateway list --resource-group {}'.format(rg), checks=JMESPathCheckV2('length(@)', ag_count - 1))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkAppGatewayRedirectConfigScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_basic')
    def test_network_app_gateway_redirect_config(self, resource_group):
        kwargs = {
            'rg': resource_group,
            'gateway': 'ag1',
            'name': 'redirect1'
        }
        self.cmd('network application-gateway create -g {rg} -n {gateway} --no-wait'.format(**kwargs))
        self.cmd('network application-gateway wait -g {rg} -n {gateway} --exists'.format(**kwargs))
        self.cmd('network application-gateway redirect-config create --gateway-name {gateway} -g {rg} -n {name} -t permanent --include-query-string --include-path false --target-listener appGatewayHttpListener --no-wait'.format(**kwargs))
        self.cmd('network application-gateway redirect-config show --gateway-name {gateway} -g {rg} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('includePath', False),
            JMESPathCheckV2('includeQueryString', True),
            JMESPathCheckV2('redirectType', 'Permanent')
        ])
        self.cmd('network application-gateway redirect-config update --gateway-name {gateway} -g {rg} -n {name} --include-path --include-query-string false --no-wait'.format(**kwargs))
        self.cmd('network application-gateway redirect-config show --gateway-name {gateway} -g {rg} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('includePath', True),
            JMESPathCheckV2('includeQueryString', False),
            JMESPathCheckV2('redirectType', 'Permanent')
        ])


class NetworkAppGatewayExistingSubnetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_existing_subnet')
    def test_network_app_gateway_with_existing_subnet(self, resource_group):
        rg = resource_group
        vnet = self.cmd('network vnet create -g {} -n vnet2 --subnet-name subnet1'.format(rg)).get_output_in_json()
        subnet_id = vnet['newVNet']['subnets'][0]['id']

        with self.assertRaises(CLIError):
            # make sure it fails
            self.cmd('network application-gateway create -g {} -n ag2 --subnet {} --subnet-address-prefix 10.0.0.0/28'.format(rg, subnet_id), checks=[
                JMESPathCheckV2('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
                JMESPathCheckV2('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
            ])
        # now verify it succeeds
        self.cmd('network application-gateway create -g {} -n ag2 --subnet {} --servers 172.0.0.1 www.mydomain.com'.format(rg, subnet_id), checks=[
            JMESPathCheckV2('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            JMESPathCheckV2('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
        ])


class NetworkAppGatewayNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_no_wait')
    def test_network_app_gateway_no_wait(self, resource_group):
        rg = resource_group
        self.cmd('network application-gateway create -g {} -n ag1 --no-wait --connection-draining-timeout 180'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway create -g {} -n ag2 --no-wait'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway wait -g {} -n ag1 --created --interval 120'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway wait -g {} -n ag2 --created --interval 120'.format(rg), checks=NoneCheck())
        self.cmd('network application-gateway show -g {} -n ag1'.format(rg), checks=[
            JMESPathCheckV2('provisioningState', 'Succeeded'),
            JMESPathCheckV2('backendHttpSettingsCollection[0].connectionDraining.enabled', True),
            JMESPathCheckV2('backendHttpSettingsCollection[0].connectionDraining.drainTimeoutInSec', 180)
        ])
        self.cmd('network application-gateway show -g {} -n ag2'.format(rg),
                 checks=JMESPathCheckV2('provisioningState', 'Succeeded'))
        self.cmd('network application-gateway delete -g {} -n ag2 --no-wait'.format(rg))
        self.cmd('network application-gateway wait -g {} -n ag2 --deleted'.format(rg))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkAppGatewayPrivateIpScenarioTest20170601(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_private_ip')
    def test_network_app_gateway_with_private_ip(self, resource_group):
        rg = resource_group
        private_ip = '10.0.0.15'
        cert_path = os.path.join(TEST_DIR, 'TestCert.pfx')
        cert_pass = 'password'
        self.cmd('network application-gateway create -g {} -n ag3 --subnet subnet1 --private-ip-address {} --cert-file "{}" --cert-password {} --no-wait'.format(rg, private_ip, cert_path, cert_pass))
        self.cmd('network application-gateway wait -g {} -n ag3 --exists'.format(rg))
        self.cmd('network application-gateway show -g {} -n ag3'.format(rg), checks=[
            JMESPathCheckV2('frontendIpConfigurations[0].privateIpAddress', private_ip),
            JMESPathCheckV2('frontendIpConfigurations[0].privateIpAllocationMethod', 'Static')
        ])
        cert_path = os.path.join(TEST_DIR, 'TestCert2.pfx')
        self.cmd('network application-gateway ssl-cert update -g {} --gateway-name ag3 -n ag3SslCert --cert-file "{}" --cert-password {}'.format(rg, cert_path, cert_pass))
        self.cmd('network application-gateway wait -g {} -n ag3 --updated'.format(rg))

        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 --disabled-ssl-protocols TLSv1_0 TLSv1_1 --no-wait'.format(rg))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg), checks=JMESPathCheck('disabledSslProtocols.length(@)', 2))

        cipher_suite = 'TLS_RSA_WITH_AES_128_CBC_SHA256'
        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 --min-protocol-version TLSv1_0 --cipher-suites {} --no-wait'.format(rg, cipher_suite))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg), checks=[
            JMESPathCheckV2('cipherSuites.length(@)', 1),
            JMESPathCheckV2('minProtocolVersion', 'TLSv1_0'),
            JMESPathCheckV2('policyType', 'Custom')
        ])

        policy_name = 'AppGwSslPolicy20150501'
        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 -n {} --no-wait'.format(rg, policy_name))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg), checks=[
            JMESPathCheckV2('policyName', policy_name),
            JMESPathCheckV2('policyType', 'Predefined')
        ])


@api_version_constraint(ResourceType.MGMT_NETWORK, max_api='2017-03-01')
class NetworkAppGatewayPrivateIpScenarioTest20170301(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(NetworkAppGatewayPrivateIpScenarioTest20170301, self).__init__(__file__, test_method, resource_group='cli_test_ag_private_ip')

    def test_network_app_gateway_with_private_ip(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        private_ip = '10.0.0.15'
        cert_path = os.path.join(TEST_DIR, 'TestCert.pfx')
        cert_pass = 'password'
        self.cmd('network application-gateway create -g {} -n ag3 --subnet subnet1 --private-ip-address {} --cert-file "{}" --cert-password {} --no-wait'.format(rg, private_ip, cert_path, cert_pass))
        self.cmd('network application-gateway wait -g {} -n ag3 --exists'.format(rg))
        self.cmd('network application-gateway show -g {} -n ag3'.format(rg), checks=[JMESPathCheck('frontendIpConfigurations[0].privateIpAddress', private_ip), JMESPathCheck('frontendIpConfigurations[0].privateIpAllocationMethod', 'Static')])
        cert_path = os.path.join(TEST_DIR, 'TestCert2.pfx')
        self.cmd('network application-gateway ssl-cert update -g {} --gateway-name ag3 -n ag3SslCert --cert-file "{}" --cert-password {}'.format(rg, cert_path, cert_pass))
        self.cmd('network application-gateway wait -g {} -n ag3 --updated'.format(rg))
        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 --disabled-ssl-protocols tlsv1_0 tlsv1_1 --no-wait'.format(rg))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg), checks=JMESPathCheck('disabledSslProtocols.length(@)', 2))
        self.cmd('network application-gateway ssl-policy set -g {} --gateway-name ag3 --clear --no-wait'.format(rg))
        self.cmd('network application-gateway ssl-policy show -g {} --gateway-name ag3'.format(rg), checks=NoneCheck())


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkAppGatewaySubresourceScenarioTest(ScenarioTest):

    def _create_ag(self, kwargs):
        self.cmd('network application-gateway create -g {rg} -n {ag} --no-wait'.format(**kwargs))
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists'.format(**kwargs))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_address_pool')
    def test_network_ag_address_pool(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway address-pool',
            'name': 'pool1'
        }
        self._create_ag(kwargs)

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --servers 123.4.5.6 www.mydns.com'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('length(backendAddresses)', 2),
            JMESPathCheckV2('backendAddresses[0].ipAddress', '123.4.5.6'),
            JMESPathCheckV2('backendAddresses[1].fqdn', 'www.mydns.com'),
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --servers 5.4.3.2'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('length(backendAddresses)', 1),
            JMESPathCheckV2('backendAddresses[0].ipAddress', '5.4.3.2')
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_frontend_port')
    def test_network_ag_frontend_port(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway frontend-port',
            'name': 'myport'
        }
        self._create_ag(kwargs)

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --port 111'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('name', 'myport'),
            JMESPathCheckV2('port', 111)
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --port 112'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('name', 'myport'),
            JMESPathCheckV2('port', 112)
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_frontend_ip_public')
    def test_network_ag_frontend_ip_public(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway frontend-ip',
            'name': 'myfrontend',
            'ip1': 'myip1',
            'ip2': 'myip2'
        }
        self.cmd('network application-gateway create -g {rg} -n {ag} --no-wait'.format(**kwargs))
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists'.format(**kwargs))

        self.cmd('network public-ip create -g {rg} -n {ip1}'.format(**kwargs))
        self.cmd('network public-ip create -g {rg} -n {ip2}'.format(**kwargs))

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --public-ip-address {ip1}'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('subnet', None)
        ])

        # NOTE: Service states that public IP address cannot be changed. https://github.com/Azure/azure-cli/issues/4133
        # self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --public-ip-address {ip2}'.format(**kwargs))
        # self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs))

        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_frontend_ip_private')
    def test_network_ag_frontend_ip_private(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway frontend-ip',
            'name': 'frontendip',
            'ip1': 'myip1',
            'vnet1': 'vnet1',
            'vnet2': 'vnet2',
            'subnet': 'subnet1'
        }
        self.cmd('network public-ip create -g {rg} -n {ip1}'.format(**kwargs))
        self.cmd('network vnet create -g {rg} -n {vnet1} --subnet-name {subnet}'.format(**kwargs))

        self.cmd('network application-gateway create -g {rg} -n {ag} --no-wait --public-ip-address {ip1} --vnet-name {vnet1} --subnet {subnet}'.format(**kwargs))
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists'.format(**kwargs))

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --private-ip-address 10.0.0.10 --vnet-name {vnet1} --subnet {subnet}'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
        ])

        # NOTE: Service states that frontend subnet cannot differ from gateway subnet https://github.com/Azure/azure-cli/issues/4134
        # self.cmd('network vnet create -g {rg} -n {vnet2} --subnet-name {subnet} --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.10.0/24'.format(**kwargs))
        # self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --private-ip-address 11.0.10.10 --vnet-name {vnet2} --subnet {subnet}'.format(**kwargs))
        # self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs))

        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_http_listener')
    def test_network_ag_http_listener(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway http-listener',
            'name': 'mylistener'
        }
        self._create_ag(kwargs)

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('hostName', 'www.test.com')
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --host-name www.test2.com'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('hostName', 'www.test2.com')
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_http_settings')
    def test_network_ag_http_settings(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway http-settings',
            'name': 'mysettings'
        }
        self._create_ag(kwargs)

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --affinity-cookie-name mycookie --connection-draining-timeout 60 --cookie-based-affinity --host-name-from-backend-pool --protocol https --timeout 50 --port 70'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('affinityCookieName', 'mycookie'),
            JMESPathCheckV2('connectionDraining.drainTimeoutInSec', 60),
            JMESPathCheckV2('connectionDraining.enabled', True),
            JMESPathCheckV2('cookieBasedAffinity', 'Enabled'),
            JMESPathCheckV2('pickHostNameFromBackendAddress', True),
            JMESPathCheckV2('port', 70),
            JMESPathCheckV2('protocol', 'Https'),
            JMESPathCheckV2('requestTimeout', 50)
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --affinity-cookie-name mycookie2 --connection-draining-timeout 0 --cookie-based-affinity disabled --host-name-from-backend-pool false --protocol http --timeout 40 --port 71'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('affinityCookieName', 'mycookie2'),
            JMESPathCheckV2('connectionDraining.drainTimeoutInSec', 1),
            JMESPathCheckV2('connectionDraining.enabled', False),
            JMESPathCheckV2('cookieBasedAffinity', 'Disabled'),
            JMESPathCheckV2('pickHostNameFromBackendAddress', False),
            JMESPathCheckV2('port', 71),
            JMESPathCheckV2('protocol', 'Http'),
            JMESPathCheckV2('requestTimeout', 40)
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_probe')
    def test_network_ag_probe(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway probe',
            'name': 'myprobe'
        }
        self._create_ag(kwargs)

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --path /test --protocol http --interval 25 --timeout 100 --threshold 10 --min-servers 2 --host www.test.com --match-status-codes 200 204 --host-name-from-http-settings false'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('path', '/test'),
            JMESPathCheckV2('protocol', 'Http'),
            JMESPathCheckV2('interval', 25),
            JMESPathCheckV2('timeout', 100),
            JMESPathCheckV2('unhealthyThreshold', 10),
            JMESPathCheckV2('minServers', 2),
            JMESPathCheckV2('host', 'www.test.com'),
            JMESPathCheckV2('length(match.statusCodes)', 2),
            JMESPathCheckV2('pickHostNameFromBackendHttpSettings', False)
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --path /test2 --protocol https --interval 26 --timeout 101 --threshold 11 --min-servers 3 --host "" --match-status-codes 201 --host-name-from-http-settings'.format(**kwargs))
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs), checks=[
            JMESPathCheckV2('path', '/test2'),
            JMESPathCheckV2('protocol', 'Https'),
            JMESPathCheckV2('interval', 26),
            JMESPathCheckV2('timeout', 101),
            JMESPathCheckV2('unhealthyThreshold', 11),
            JMESPathCheckV2('minServers', 3),
            JMESPathCheckV2('host', ''),
            JMESPathCheckV2('length(match.statusCodes)', 1),
            JMESPathCheckV2('pickHostNameFromBackendHttpSettings', True)
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_rule')
    def test_network_ag_rule(self, resource_group):

        kwargs = {
            'ag': 'ag1',
            'rg': resource_group,
            'res': 'application-gateway rule',
            'name': 'myrule'
        }
        self._create_ag(kwargs)

        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com'.format(**kwargs))
        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener2 --no-wait --frontend-port appGatewayFrontendPort --host-name www.test2.com'.format(**kwargs))

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --http-listener mylistener'.format(**kwargs))
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs)).get_output_in_json()
        self.assertTrue(rule['httpListener']['id'].endswith('mylistener'))
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --http-listener mylistener2'.format(**kwargs))
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}'.format(**kwargs)).get_output_in_json()
        self.assertTrue(rule['httpListener']['id'].endswith('mylistener2'))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}'.format(**kwargs))
        self.cmd('network {res} list -g {rg} --gateway-name {ag}'.format(**kwargs), checks=JMESPathCheckV2('length(@)', 1))


class NetworkAppGatewayPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_public_ip')
    def test_network_app_gateway_with_public_ip(self, resource_group):
        rg = resource_group
        public_ip_name = 'publicip4'
        self.cmd('network application-gateway create -g {} -n test4 --subnet subnet1 --vnet-name vnet4 --vnet-address-prefix 10.0.0.1/16 --subnet-address-prefix 10.0.0.1/28 --public-ip-address {}'.format(rg, public_ip_name), checks=[
            JMESPathCheckV2("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(public_ip_name), True),
            JMESPathCheckV2('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')
        ])


if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-03-01'):
    class NetworkAppGatewayWafConfigScenarioTest(ScenarioTest):

        @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_config')
        def test_network_app_gateway_waf_config(self, resource_group):
            rg = resource_group
            public_ip_name = 'pip1'
            self.cmd('network application-gateway create -g {} -n ag1 --subnet subnet1 --vnet-name vnet1 --public-ip-address {} --sku WAF_Medium'.format(rg, public_ip_name), checks=[JMESPathCheckV2("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(public_ip_name), True), JMESPathCheckV2('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')])
            self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled true --firewall-mode prevention --rule-set-version 2.2.9 --disabled-rule-groups crs_30_http_policy --disabled-rules 981175 981176 --no-wait'.format(rg))
            self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[
                JMESPathCheckV2('enabled', True),
                JMESPathCheckV2('firewallMode', 'Prevention'),
                JMESPathCheckV2('length(disabledRuleGroups)', 2),
                JMESPathCheckV2('length(disabledRuleGroups[1].rules)', 2)
            ])
else:
    class NetworkAppGatewayWafScenarioTest(ResourceGroupVCRTestBase):

        def __init__(self, test_method):
            super(NetworkAppGatewayWafScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_ag_waf')

        def test_network_app_gateway_waf(self):
            self.execute()

        def body(self):
            rg = self.resource_group
            public_ip_name = 'pip1'
            self.cmd('network application-gateway create -g {} -n ag1 --subnet subnet1 --vnet-name vnet4 --public-ip-address {} --sku WAF_Medium'.format(rg, public_ip_name), checks=[JMESPathCheck("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(public_ip_name), True), JMESPathCheck('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')])
            self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled true --firewall-mode detection --no-wait'.format(rg))
            self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[JMESPathCheck('enabled', True), JMESPathCheck('firewallMode', 'Detection')])
            self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled true --firewall-mode prevention --no-wait'.format(rg))
            self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[JMESPathCheck('enabled', True), JMESPathCheck('firewallMode', 'Prevention')])
            self.cmd('network application-gateway waf-config set -g {} --gateway-name ag1 --enabled false --no-wait'.format(rg))
            self.cmd('network application-gateway waf-config show -g {} --gateway-name ag1'.format(rg), checks=[JMESPathCheck('enabled', False), JMESPathCheck('firewallMode', 'Detection')])


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
        s.cmd('network public-ip create -g {} -n {} --dns-name {} --allocation-method static'.format(rg, public_ip_dns, dns), checks=[JMESPathCheck('publicIp.provisioningState', 'Succeeded'), JMESPathCheck('publicIp.publicIpAllocationMethod', 'Static'), JMESPathCheck('publicIp.dnsSettings.domainNameLabel', dns)])
        s.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip_no_dns), checks=[JMESPathCheck('publicIp.provisioningState', 'Succeeded'), JMESPathCheck('publicIp.publicIpAllocationMethod', 'Dynamic'), JMESPathCheck('publicIp.dnsSettings', None)])
        s.cmd('network public-ip update -g {} -n {} --allocation-method static --dns-name wowza --idle-timeout 10'.format(rg, public_ip_no_dns), checks=[JMESPathCheck('publicIpAllocationMethod', 'Static'), JMESPathCheck('dnsSettings.domainNameLabel', 'wowza'), JMESPathCheck('idleTimeoutInMinutes', 10)])

        s.cmd('network public-ip list -g {}'.format(rg), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)])

        s.cmd('network public-ip show -g {} -n {}'.format(rg, public_ip_dns), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('name', public_ip_dns), JMESPathCheck('resourceGroup', rg), ])

        s.cmd('network public-ip delete -g {} -n {}'.format(rg, public_ip_dns))
        s.cmd('network public-ip list -g {}'.format(rg), checks=JMESPathCheck("length[?name == '{}']".format(public_ip_dns), None))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkZonedPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_zoned_public_ip')
    def test_network_zoned_public_ip(self, resource_group):
        kwargs = {
            'rg': resource_group,
            'ip': 'pubip'
        }
        self.cmd('network public-ip create -g {rg} -n {ip} -l centralus -z 2'.format(**kwargs),
                 checks=JMESPathCheck('publicIp.zones[0]', '2'))

        table_output = self.cmd('network public-ip show -g {rg} -n {ip} -otable'.format(**kwargs)).output
        self.assertEqual(table_output.splitlines()[2].split(), ['pubip', resource_group, 'centralus', '2', 'IPv4', 'Dynamic', '4', 'Succeeded'])


class NetworkRouteFilterScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_route_filter')
    def test_network_route_filter(self, resource_group):
        kwargs = {
            'rg': resource_group,
            'filter': 'filter1'
        }
        self.cmd('network route-filter create -g {rg} -n {filter}'.format(**kwargs))
        self.cmd('network route-filter update -g {rg} -n {filter}'.format(**kwargs))
        self.cmd('network route-filter show -g {rg} -n {filter}'.format(**kwargs))
        self.cmd('network route-filter list -g {rg}'.format(**kwargs))

        self.cmd('network route-filter rule list-service-communities')
        with self.assertRaises(CLIError):
            self.cmd('network route-filter rule create -g {rg} --filter-name {filter} -n rule1 --communities 12076:5040 12076:5030 --access allow'.format(**kwargs))
        with self.assertRaises(Exception):
            self.cmd('network route-filter rule update -g {rg} --filter-name {filter} -n rule1 --set access=Deny'.format(**kwargs))
        self.cmd('network route-filter rule show -g {rg} --filter-name {filter} -n rule1'.format(**kwargs))
        self.cmd('network route-filter rule list -g {rg} --filter-name {filter}'.format(**kwargs))
        self.cmd('network route-filter rule delete -g {rg} --filter-name {filter} -n rule1'.format(**kwargs))

        self.cmd('network route-filter delete -g {rg} -n {filter}'.format(**kwargs))


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

        self.cmd('network express-route peering create -g {} --circuit-name {} --peering-type MicrosoftPeering --peer-asn 10002 --vlan-id 103 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30 --advertised-public-prefixes 104.0.0.0/30 --customer-asn 10000 --routing-registry-name level3'.format(rg, circuit), allowed_exceptions='not authorized for creating Microsoft Peering')
        self.cmd('network express-route peering show -g {} --circuit-name {} -n MicrosoftPeering'.format(rg, circuit), checks=[JMESPathCheck('microsoftPeeringConfig.advertisedPublicPrefixes[0]', '104.0.0.0/30'), JMESPathCheck('microsoftPeeringConfig.customerAsn', 10000), JMESPathCheck('microsoftPeeringConfig.routingRegistryName', 'LEVEL3')])

        self.cmd('network express-route peering delete -g {} --circuit-name {} -n MicrosoftPeering'.format(rg, circuit))

        self.cmd('network express-route peering list --resource-group {} --circuit-name {}'.format(rg, circuit), checks=JMESPathCheck('length(@)', 2))

        self.cmd('network express-route peering update -g {} --circuit-name {} -n AzurePublicPeering --set vlanId=200'.format(rg, circuit), checks=JMESPathCheck('vlanId', 200))

    def _test_express_route_auth(self):
        rg = self.resource_group
        circuit = self.circuit_name

        self.cmd('network express-route auth create -g {} --circuit-name {} -n auth1'.format(rg, circuit), checks=JMESPathCheck('authorizationUseStatus', 'Available'))

        self.cmd('network express-route auth list --resource-group {} --circuit-name {}'.format(rg, circuit), checks=JMESPathCheck('length(@)', 1))

        self.cmd('network express-route auth show -g {} --circuit-name {} -n auth1'.format(rg, circuit), checks=JMESPathCheck('authorizationUseStatus', 'Available'))

        self.cmd('network express-route auth delete -g {} --circuit-name {} -n auth1'.format(rg, circuit))

        self.cmd('network express-route auth list --resource-group {} --circuit-name {}'.format(rg, circuit), checks=NoneCheck())

    def body(self):
        rg = self.resource_group
        circuit = self.circuit_name

        self.cmd('network express-route list-service-providers', checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format('Microsoft.Network/expressRouteServiceProviders'), True)])

        # Premium SKU required to create MicrosoftPeering settings
        self.cmd('network express-route create -g {} -n {} --bandwidth 50 --provider "Microsoft ER Test" --peering-location Area51 --sku-tier Premium'.format(rg, circuit))
        self.cmd('network express-route list', checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)])
        self.cmd('network express-route list --resource-group {}'.format(rg), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True), JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)])
        self.cmd('network express-route show --resource-group {} --name {}'.format(rg, circuit), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('type', self.resource_type), JMESPathCheck('name', circuit), JMESPathCheck('resourceGroup', rg), ])
        self.cmd('network express-route get-stats --resource-group {} --name {}'.format(rg, circuit), checks=JMESPathCheck('type(@)', 'object'))

        self.cmd('network express-route update -g {} -n {} --set tags.test=Test'.format(rg, circuit), checks=JMESPathCheck('tags', {'test': 'Test'}))

        self._test_express_route_auth()

        self._test_express_route_peering()

        # because the circuit isn't actually provisioned, these commands will not return anything useful
        # so we will just verify that the command makes it through the SDK without error.
        self.cmd('network express-route list-arp-tables --resource-group {} --name {} --peering-name azureprivatepeering --path primary'.format(rg, circuit))
        self.cmd('network express-route list-route-tables --resource-group {} --name {} --peering-name azureprivatepeering --path primary'.format(rg, circuit))

        self.cmd('network express-route delete --resource-group {} --name {}'.format(rg, circuit))
        # Expecting no results as we just deleted the only express route in the resource group
        self.cmd('network express-route list --resource-group {}'.format(rg), checks=NoneCheck())


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkExpressRouteIPv6PeeringScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_express_route_ipv6_peering')
    def test_network_express_route_ipv6_peering(self, resource_group):

        rg = resource_group
        circuit = 'circuit1'

        # Premium SKU required to create MicrosoftPeering settings
        self.cmd('network express-route create -g {} -n {} --bandwidth 50 --provider "Microsoft ER Test" --peering-location Area51 --sku-tier Premium'.format(rg, circuit))
        self.cmd('network express-route peering create -g {} --circuit-name {} --peering-type MicrosoftPeering --peer-asn 10002 --vlan-id 103 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30 --advertised-public-prefixes 104.0.0.0/30 --customer-asn 10000 --routing-registry-name level3'.format(rg, circuit))
        self.cmd('network express-route peering update -g {} --circuit-name {} -n MicrosoftPeering --ip-version ipv6 --primary-peer-subnet 2001:db00::/126 --secondary-peer-subnet 2002:db00::/126 --advertised-public-prefixes 2001:db00::/126 --customer-asn 100001 --routing-registry-name level3'.format(rg, circuit))
        self.cmd('network express-route peering show -g {} --circuit-name {} -n MicrosoftPeering'.format(rg, circuit), checks=[
            JMESPathCheckV2('microsoftPeeringConfig.advertisedPublicPrefixes[0]', '104.0.0.0/30'),
            JMESPathCheckV2('microsoftPeeringConfig.customerAsn', 10000),
            JMESPathCheckV2('microsoftPeeringConfig.routingRegistryName', 'LEVEL3'),
            JMESPathCheckV2('ipv6PeeringConfig.microsoftPeeringConfig.advertisedPublicPrefixes[0]', '2001:db00::/126'),
            JMESPathCheckV2('ipv6PeeringConfig.microsoftPeeringConfig.customerAsn', 100001),
            JMESPathCheckV2('ipv6PeeringConfig.state', 'Enabled')
        ])


class NetworkLoadBalancerScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(NetworkLoadBalancerScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_load_balancer')
        self.lb_name = 'lb'
        self.resource_type = 'Microsoft.Network/loadBalancers'

    def test_network_load_balancer(self):
        self.execute()

    def body(self):
        # test lb create with min params (new ip)
        self.cmd('network lb create -n {}1 -g {}'.format(self.lb_name, self.resource_group), checks=[JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'), JMESPathCheck('loadBalancer.frontendIPConfigurations[0].resourceGroup', self.resource_group)])

        # test internet facing load balancer with new static public IP
        self.cmd('network lb create -n {}2 -g {} --public-ip-address-allocation static'.format(self.lb_name, self.resource_group))
        self.cmd('network public-ip show -g {} -n PublicIP{}2'.format(self.resource_group, self.lb_name), checks=JMESPathCheck('publicIpAllocationMethod', 'Static'))

        # test internal load balancer create (existing subnet ID)
        vnet_name = 'mytestvnet'
        private_ip = '10.0.0.15'
        vnet = self.cmd('network vnet create -n {} -g {} --subnet-name default'.format(vnet_name, self.resource_group))
        subnet_id = vnet['newVNet']['subnets'][0]['id']
        self.cmd('network lb create -n {}3 -g {} --subnet {} --private-ip-address {}'.format(self.lb_name, self.resource_group, subnet_id, private_ip), checks=[JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Static'), JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAddress', private_ip), JMESPathCheck('loadBalancer.frontendIPConfigurations[0].resourceGroup', self.resource_group), JMESPathCheck("loadBalancer.frontendIPConfigurations[0].properties.subnet.id", subnet_id)])

        # test internet facing load balancer with existing public IP (by name)
        pub_ip_name = 'publicip4'
        self.cmd('network public-ip create -n {} -g {}'.format(pub_ip_name, self.resource_group))
        self.cmd('network lb create -n {}4 -g {} --public-ip-address {}'.format(self.lb_name, self.resource_group, pub_ip_name), checks=[JMESPathCheck('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'), JMESPathCheck('loadBalancer.frontendIPConfigurations[0].resourceGroup', self.resource_group), JMESPathCheck("loadBalancer.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{}')".format(pub_ip_name), True)])

        self.cmd('network lb list', checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)])
        self.cmd('network lb list --resource-group {}'.format(self.resource_group), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True), JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)])
        self.cmd('network lb show --resource-group {} --name {}1'.format(self.resource_group, self.lb_name), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('type', self.resource_type), JMESPathCheck('resourceGroup', self.resource_group), JMESPathCheck('name', '{}1'.format(self.lb_name))])
        self.cmd('network lb delete --resource-group {} --name {}1'.format(self.resource_group, self.lb_name))
        # Expecting no results as we just deleted the only lb in the resource group
        self.cmd('network lb list --resource-group {}'.format(self.resource_group), checks=JMESPathCheck('length(@)', 3))


class NetworkLoadBalancerIpConfigScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_load_balancer_ip_config')
    def test_network_load_balancer_ip_config(self, resource_group):
        rg = resource_group

        for i in range(1, 4):  # create 3 public IPs to use for the test
            self.cmd('network public-ip create -g {} -n publicip{}'.format(rg, i))

        # create internet-facing LB with public IP (lb1)
        self.cmd('network lb create -g {} -n lb1 --public-ip-address publicip1'.format(rg))

        # create internal LB (lb2)
        self.cmd('network vnet create -g {} -n vnet1 --subnet-name subnet1'.format(rg))
        self.cmd('network vnet subnet create -g {} --vnet-name vnet1 -n subnet2 --address-prefix 10.0.1.0/24'.format(rg))
        self.cmd('network lb create -g {} -n lb2 --subnet subnet1 --vnet-name vnet1'.format(rg))

        # Test frontend IP configuration for internet-facing LB
        self.cmd('network lb frontend-ip create -g {} --lb-name lb1 -n ipconfig1 --public-ip-address publicip2'.format(rg))
        self.cmd('network lb frontend-ip list -g {} --lb-name lb1'.format(rg),
                 checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network lb frontend-ip update -g {} --lb-name lb1 -n ipconfig1 --public-ip-address publicip3'.format(rg))
        self.cmd('network lb frontend-ip show -g {} --lb-name lb1 -n ipconfig1'.format(rg),
                 checks=JMESPathCheckV2("publicIpAddress.contains(id, 'publicip3')", True))

        # test generic update
        subscription_id = MOCKED_SUBSCRIPTION_ID if not self.in_recording else get_subscription_id()
        ip2_id = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='publicIPAddresses', name='publicip2')
        self.cmd('network lb frontend-ip update -g {} --lb-name lb1 -n ipconfig1 --set publicIpAddress.id="{}"'.format(rg, ip2_id),
                 checks=JMESPathCheckV2("publicIpAddress.contains(id, 'publicip2')", True))
        self.cmd('network lb frontend-ip delete -g {} --lb-name lb1 -n ipconfig1'.format(rg))
        self.cmd('network lb frontend-ip list -g {} --lb-name lb1'.format(rg),
                 checks=JMESPathCheckV2('length(@)', 1))

        # Test frontend IP configuration for internal LB
        self.cmd('network lb frontend-ip create -g {} --lb-name lb2 -n ipconfig2 --vnet-name vnet1 --subnet subnet1 --private-ip-address 10.0.0.99'.format(rg))
        self.cmd('network lb frontend-ip list -g {} --lb-name lb2'.format(rg),
                 checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network lb frontend-ip update -g {} --lb-name lb2 -n ipconfig2 --subnet subnet2 --vnet-name vnet1 --private-ip-address 10.0.1.100'.format(rg))
        self.cmd('network lb frontend-ip show -g {} --lb-name lb2 -n ipconfig2'.format(rg),
                 checks=JMESPathCheckV2("subnet.contains(id, 'subnet2')", True))


class NetworkLoadBalancerSubresourceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_rules')
    def test_network_lb_nat_rules(self, resource_group):
        rg = resource_group
        lb = 'lb1'
        lb_rg = '-g {} --lb-name {}'.format(rg, lb)
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

        for count in range(1, 3):
            self.cmd('network lb inbound-nat-rule create {} -n rule{} --protocol tcp --frontend-port {} --backend-port {} --frontend-ip-name LoadBalancerFrontEnd'.format(lb_rg, count, count, count))
        self.cmd('network lb inbound-nat-rule create {} -n rule3 --protocol tcp --frontend-port 3 --backend-port 3'.format(lb_rg))
        self.cmd('network lb inbound-nat-rule list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 3))
        self.cmd('network lb inbound-nat-rule update {} -n rule1 --floating-ip true --idle-timeout 10'.format(lb_rg))
        self.cmd('network lb inbound-nat-rule show {} -n rule1'.format(lb_rg), checks=[
            JMESPathCheckV2('enableFloatingIp', True),
            JMESPathCheckV2('idleTimeoutInMinutes', 10)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-rule update {} -n rule1 --set idleTimeoutInMinutes=5'.format(lb_rg),
                 checks=JMESPathCheckV2('idleTimeoutInMinutes', 5))

        for count in range(1, 4):
            self.cmd('network lb inbound-nat-rule delete {} -n rule{}'.format(lb_rg, count))
        self.cmd('network lb inbound-nat-rule list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_pools')
    def test_network_lb_nat_pools(self, resource_group):
        rg = resource_group
        lb = 'lb1'
        lb_rg = '-g {} --lb-name {}'.format(rg, lb)
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool create {} -n rule{} --protocol tcp --frontend-port-range-start {}  --frontend-port-range-end {} --backend-port {}'.format(lb_rg, count, count, count + 999, count))
        self.cmd('network lb inbound-nat-pool list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 3))
        self.cmd('network lb inbound-nat-pool update {} -n rule1000 --protocol udp --backend-port 50'.format(lb_rg))
        self.cmd('network lb inbound-nat-pool show {} -n rule1000'.format(lb_rg), checks=[
            JMESPathCheckV2('protocol', 'Udp'),
            JMESPathCheckV2('backendPort', 50)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-pool update {} -n rule1000 --set protocol=Tcp'.format(lb_rg),
                 checks=JMESPathCheckV2('protocol', 'Tcp'))

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool delete {} -n rule{}'.format(lb_rg, count))
        self.cmd('network lb inbound-nat-pool list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_address_pool')
    def test_network_lb_address_pool(self, resource_group):
        rg = resource_group
        lb = 'lb1'
        lb_rg = '-g {} --lb-name {}'.format(rg, lb)
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

        for i in range(1, 4):
            self.cmd('network lb address-pool create {} -n bap{}'.format(lb_rg, i),
                     checks=JMESPathCheckV2('name', 'bap{}'.format(i)))
        self.cmd('network lb address-pool list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 4))
        self.cmd('network lb address-pool show {} -n bap1'.format(lb_rg),
                 checks=JMESPathCheckV2('name', 'bap1'))
        self.cmd('network lb address-pool delete {} -n bap1'.format(lb_rg),
                 checks=NoneCheck())
        self.cmd('network lb address-pool list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 3))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_probes')
    def test_network_lb_probes(self, resource_group):
        rg = resource_group
        lb = 'lb1'
        lb_rg = '-g {} --lb-name {}'.format(rg, lb)
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

        for i in range(1, 4):
            self.cmd('network lb probe create {} -n probe{} --port {} --protocol http --path "/test{}"'.format(lb_rg, i, i, i))
        self.cmd('network lb probe list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 3))
        self.cmd('network lb probe update {} -n probe1 --interval 20 --threshold 5'.format(lb_rg))
        self.cmd('network lb probe update {} -n probe2 --protocol tcp --path ""'.format(lb_rg))
        self.cmd('network lb probe show {} -n probe1'.format(lb_rg), checks=[
            JMESPathCheckV2('intervalInSeconds', 20),
            JMESPathCheckV2('numberOfProbes', 5)
        ])
        # test generic update
        self.cmd('network lb probe update {} -n probe1 --set intervalInSeconds=15 --set numberOfProbes=3'.format(lb_rg), checks=[
            JMESPathCheckV2('intervalInSeconds', 15),
            JMESPathCheckV2('numberOfProbes', 3)
        ])

        self.cmd('network lb probe show {} -n probe2'.format(lb_rg), checks=[
            JMESPathCheckV2('protocol', 'Tcp'),
            JMESPathCheckV2('path', None)
        ])
        self.cmd('network lb probe delete {} -n probe3'.format(lb_rg))
        self.cmd('network lb probe list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 2))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_rules')
    def test_network_lb_rules(self, resource_group):

        rg = resource_group
        lb = 'lb1'
        lb_rg = '-g {} --lb-name {}'.format(rg, lb)
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))

        self.cmd('network lb rule create {} -n rule2 --frontend-port 60 --backend-port 60 --protocol tcp'.format(lb_rg))
        self.cmd('network lb address-pool create {} -n bap1'.format(lb_rg))
        self.cmd('network lb address-pool create {} -n bap2'.format(lb_rg))
        self.cmd('network lb rule create {} -n rule1 --frontend-ip-name LoadBalancerFrontEnd --frontend-port 40 --backend-pool-name bap1 --backend-port 40 --protocol tcp'.format(lb_rg))

        self.cmd('network lb rule list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 2))
        self.cmd('network lb rule update {} -n rule1 --floating-ip true --idle-timeout 20 --load-distribution sourceip --protocol udp'.format(lb_rg))
        self.cmd('network lb rule update {} -n rule2 --backend-pool-name bap2 --load-distribution sourceipprotocol'.format(lb_rg))
        self.cmd('network lb rule show {} -n rule1'.format(lb_rg), checks=[
            JMESPathCheckV2('enableFloatingIp', True),
            JMESPathCheckV2('idleTimeoutInMinutes', 20),
            JMESPathCheckV2('loadDistribution', 'SourceIP'),
            JMESPathCheckV2('protocol', 'Udp')
        ])
        # test generic update
        self.cmd('network lb rule update {} -n rule1 --set idleTimeoutInMinutes=5'.format(lb_rg),
                 checks=JMESPathCheckV2('idleTimeoutInMinutes', 5))

        self.cmd('network lb rule show {} -n rule2'.format(lb_rg), checks=[
            JMESPathCheckV2("backendAddressPool.contains(id, 'bap2')", True),
            JMESPathCheckV2('loadDistribution', 'SourceIPProtocol')
        ])
        self.cmd('network lb rule delete {} -n rule1'.format(lb_rg))
        self.cmd('network lb rule delete {} -n rule2'.format(lb_rg))
        self.cmd('network lb rule list {}'.format(lb_rg),
                 checks=JMESPathCheckV2('length(@)', 0))


class NetworkLocalGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='local_gateway_scenario')
    def test_network_local_gateway(self, resource_group):
        lgw1 = 'lgw1'
        lgw2 = 'lgw2'
        resource_type = 'Microsoft.Network/localNetworkGateways'
        self.cmd('network local-gateway create --resource-group {} --name {} --gateway-ip-address 10.1.1.1'.format(resource_group, lgw1))
        self.cmd('network local-gateway show --resource-group {} --name {}'.format(resource_group, lgw1), checks=[
            JMESPathCheckV2('type', resource_type),
            JMESPathCheckV2('resourceGroup', resource_group),
            JMESPathCheckV2('name', lgw1)])

        self.cmd('network local-gateway create --resource-group {} --name {} --gateway-ip-address 10.1.1.2 --local-address-prefixes 10.0.1.0/24'.format(resource_group, lgw2),
                 checks=JMESPathCheckV2('localNetworkAddressSpace.addressPrefixes[0]', '10.0.1.0/24'))

        self.cmd('network local-gateway list --resource-group {}'.format(resource_group),
                 checks=JMESPathCheckV2('length(@)', 2))

        self.cmd('network local-gateway delete --resource-group {} --name {}'.format(resource_group, lgw1))
        self.cmd('network local-gateway list --resource-group {}'.format(resource_group),
                 checks=JMESPathCheckV2('length(@)', 1))


class NetworkNicScenarioTest(ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_nic_scenario')
    def test_network_nic(self, resource_group):
        rg = resource_group
        nic = 'cli-test-nic'
        rt = 'Microsoft.Network/networkInterfaces'
        subnet = 'mysubnet'
        vnet = 'myvnet'
        nsg = 'mynsg'
        alt_nsg = 'myothernsg'
        lb = 'mylb'
        private_ip = '10.0.0.15'
        public_ip_name = 'publicip1'

        subnet_id = self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, vnet, subnet)).get_output_in_json()['newVNet']['subnets'][0]['id']
        self.cmd('network nsg create -g {} -n {}'.format(rg, nsg))
        nsg_id = self.cmd('network nsg show -g {} -n {}'.format(rg, nsg)).get_output_in_json()['id']
        self.cmd('network nsg create -g {} -n {}'.format(rg, alt_nsg))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip_name))
        public_ip_id = self.cmd('network public-ip show -g {} -n {}'.format(rg, public_ip_name)).get_output_in_json()['id']
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule1 --protocol tcp --frontend-port 100 --backend-port 100 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule2 --protocol tcp --frontend-port 200 --backend-port 200 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        rule_ids = ' '.join(self.cmd('network lb inbound-nat-rule list -g {} --lb-name {} --query "[].id"'.format(rg, lb)).get_output_in_json())
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap1'.format(rg, lb))
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap2'.format(rg, lb))
        address_pool_ids = ' '.join(self.cmd('network lb address-pool list -g {} --lb-name {} --query "[].id"'.format(rg, lb)).get_output_in_json())

        # create with minimum parameters
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {}'.format(rg, nic, subnet, vnet), checks=[
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise optional parameters
        self.cmd('network nic create -g {} -n {} --subnet {} --ip-forwarding --private-ip-address {} --public-ip-address {} --internal-dns-name test --dns-servers 100.1.2.3 --lb-address-pools {} --lb-inbound-nat-rules {} --accelerated-networking'.format(rg, nic, subnet_id, private_ip, public_ip_name, address_pool_ids, rule_ids), checks=[
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Static'),
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAddress', private_ip),
            JMESPathCheckV2('NewNIC.enableIpForwarding', True),
            JMESPathCheckV2('NewNIC.enableAcceleratedNetworking', True),
            JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded'),
            JMESPathCheckV2('NewNIC.dnsSettings.internalDnsNameLabel', 'test'),
            JMESPathCheckV2('length(NewNIC.dnsSettings.dnsServers)', 1)])
        # exercise creating with NSG
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {} --network-security-group {}'.format(rg, nic, subnet, vnet, nsg), checks=[
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheckV2('NewNIC.enableIpForwarding', False),
            JMESPathCheckV2("NewNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded')
        ])
        # exercise creating with NSG and Public IP
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {} --network-security-group {} --public-ip-address {}'.format(rg, nic, subnet, vnet, nsg_id, public_ip_id), checks=[
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheckV2('NewNIC.enableIpForwarding', False),
            JMESPathCheckV2("NewNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded')
        ])
        self.cmd('network nic list', checks=[
            JMESPathCheckV2('type(@)', 'array'),
            JMESPathCheckV2("length([?contains(id, 'networkInterfaces')]) == length(@)", True)
        ])
        self.cmd('network nic list --resource-group {}'.format(rg), checks=[
            JMESPathCheckV2('type(@)', 'array'),
            JMESPathCheckV2("length([?type == '{}']) == length(@)".format(rt), True),
            JMESPathCheckV2("length([?resourceGroup == '{}']) == length(@)".format(rg), True)
        ])
        self.cmd('network nic show --resource-group {} --name {}'.format(rg, nic), checks=[
            JMESPathCheckV2('type(@)', 'object'),
            JMESPathCheckV2('type', rt),
            JMESPathCheckV2('resourceGroup', rg),
            JMESPathCheckV2('name', nic)
        ])
        self.cmd('network nic update -g {} -n {} --internal-dns-name noodle --ip-forwarding true --accelerated-networking false --dns-servers "" --network-security-group {}'.format(rg, nic, alt_nsg), checks=[
            JMESPathCheckV2('enableIpForwarding', True),
            JMESPathCheckV2('enableAcceleratedNetworking', False),
            JMESPathCheckV2('dnsSettings.internalDnsNameLabel', 'noodle'),
            JMESPathCheckV2('length(dnsSettings.dnsServers)', 0),
            JMESPathCheckV2("networkSecurityGroup.contains(id, '{}')".format(alt_nsg), True)
        ])
        # test generic update
        self.cmd('network nic update -g {} -n {} --set dnsSettings.internalDnsNameLabel=doodle --set enableIpForwarding=false'.format(rg, nic), checks=[
            JMESPathCheckV2('enableIpForwarding', False),
            JMESPathCheckV2('dnsSettings.internalDnsNameLabel', 'doodle')
        ])

        self.cmd('network nic delete --resource-group {} --name {}'.format(rg, nic))
        self.cmd('network nic list -g {}'.format(rg), checks=NoneCheck())

    @api_version_constraint(ResourceType.MGMT_NETWORK, max_api='2015-06-15')
    @ResourceGroupPreparer(name_prefix='cli_test_nic_stack_scenario', location='local', dev_setting_location='local')
    def test_network_nic_stack(self, resource_group):
        rg = resource_group
        nic = 'cli-test-nic'
        rt = 'Microsoft.Network/networkInterfaces'
        subnet = 'mysubnet'
        vnet = 'myvnet'
        nsg = 'mynsg'
        alt_nsg = 'myothernsg'
        lb = 'mylb'
        private_ip = '10.0.0.15'
        public_ip_name = 'publicip1'

        subnet_id = self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, vnet, subnet)).get_output_in_json()['newVNet']['subnets'][0]['id']
        self.cmd('network nsg create -g {} -n {}'.format(rg, nsg))
        nsg_id = self.cmd('network nsg show -g {} -n {}'.format(rg, nsg)).get_output_in_json()['id']
        self.cmd('network nsg create -g {} -n {}'.format(rg, alt_nsg))
        self.cmd('network public-ip create -g {} -n {}'.format(rg, public_ip_name))
        public_ip_id = self.cmd('network public-ip show -g {} -n {}'.format(rg, public_ip_name)).get_output_in_json()['id']
        self.cmd('network lb create -g {} -n {}'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule1 --protocol tcp --frontend-port 100 --backend-port 100 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n rule2 --protocol tcp --frontend-port 200 --backend-port 200 --frontend-ip-name LoadBalancerFrontEnd'.format(rg, lb))
        rule_ids = ' '.join(self.cmd('network lb inbound-nat-rule list -g {} --lb-name {} --query "[].id"'.format(rg, lb)).get_output_in_json())
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap1'.format(rg, lb))
        self.cmd('network lb address-pool create -g {} --lb-name {} -n bap2'.format(rg, lb))
        address_pool_ids = ' '.join(self.cmd('network lb address-pool list -g {} --lb-name {} --query "[].id"'.format(rg, lb)).get_output_in_json())

        # create with minimum parameters
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {}'.format(rg, nic, subnet, vnet), checks=[
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded')])

        # exercise optional parameters
        self.cmd('network nic create -g {} -n {} --subnet {} --ip-forwarding --private-ip-address {} --public-ip-address {} --internal-dns-name test --dns-servers 100.1.2.3 --lb-address-pools {} --lb-inbound-nat-rules {}'.format(rg, nic, subnet_id, private_ip, public_ip_name, address_pool_ids, rule_ids),
                 checks=[JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Static'),
                         JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAddress', private_ip),
                         JMESPathCheckV2('NewNIC.enableIpForwarding', True),
                         JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded'),
                         JMESPathCheckV2('NewNIC.dnsSettings.internalDnsNameLabel', 'test'),
                         JMESPathCheckV2('length(NewNIC.dnsSettings.dnsServers)', 1)])

        # exercise creating with NSG
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {} --network-security-group {}'.format(rg, nic, subnet, vnet, nsg),
                 checks=[JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
                         JMESPathCheckV2('NewNIC.enableIpForwarding', False),
                         JMESPathCheckV2("NewNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
                         JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded')])

        # exercise creating with NSG and Public IP
        self.cmd('network nic create -g {} -n {} --subnet {} --vnet-name {} --network-security-group {} --public-ip-address {}'.format(rg, nic, subnet, vnet, nsg_id, public_ip_id), checks=[
            JMESPathCheckV2('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Dynamic'),
            JMESPathCheckV2('NewNIC.enableIpForwarding', False),
            JMESPathCheckV2("NewNIC.networkSecurityGroup.contains(id, '{}')".format(nsg), True),
            JMESPathCheckV2('NewNIC.provisioningState', 'Succeeded')])

        self.cmd('network nic list',
                 checks=[JMESPathCheckV2('type(@)', 'array'),
                         JMESPathCheckV2("length([?contains(id, 'networkInterfaces')]) == length(@)", True)])

        self.cmd('network nic list --resource-group {}'.format(rg),
                 checks=[JMESPathCheckV2('type(@)', 'array'),
                         JMESPathCheckV2("length([?type == '{}']) == length(@)".format(rt), True),
                         JMESPathCheckV2("length([?resourceGroup == '{}']) == length(@)".format(rg), True)])

        self.cmd('network nic show --resource-group {} --name {}'.format(rg, nic),
                 checks=[JMESPathCheckV2('type(@)', 'object'),
                         JMESPathCheckV2('type', rt),
                         JMESPathCheckV2('resourceGroup', rg),
                         JMESPathCheckV2('name', nic)])

        self.cmd('network nic update -g {} -n {} --internal-dns-name noodle --ip-forwarding true --dns-servers "" --network-security-group {}'.format(rg, nic, alt_nsg),
                 checks=[JMESPathCheckV2('enableIpForwarding', True),
                         JMESPathCheckV2('dnsSettings.internalDnsNameLabel', 'noodle'),
                         JMESPathCheckV2('length(dnsSettings.dnsServers)', 0),
                         JMESPathCheckV2("networkSecurityGroup.contains(id, '{}')".format(alt_nsg), True)])

        # test generic update
        self.cmd('network nic update -g {} -n {} --set dnsSettings.internalDnsNameLabel=doodle --set enableIpForwarding=false'.format(rg, nic),
                 checks=[JMESPathCheckV2('enableIpForwarding', False),
                         JMESPathCheckV2('dnsSettings.internalDnsNameLabel', 'doodle')])

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
        self.cmd('network nic ip-config list -g {} --nic-name {}'.format(rg, nic), checks=JMESPathCheck('length(@)', 1))
        self.cmd('network nic ip-config show -g {} --nic-name {} -n ipconfig1'.format(rg, nic), checks=[JMESPathCheck('name', 'ipconfig1'), JMESPathCheck('privateIpAllocationMethod', 'Dynamic')])
        self.cmd('network nic ip-config create -g {} --nic-name {} -n ipconfig2 --make-primary'.format(rg, nic), checks=[JMESPathCheck('primary', True)])
        self.cmd('network nic ip-config update -g {} --nic-name {} -n ipconfig1 --make-primary'.format(rg, nic), checks=[JMESPathCheck('primary', True)])
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
        # includes the default backend pool
        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --lb-name {} --lb-address-pools {} bap2 --lb-inbound-nat-rules {} rule2 --private-ip-address {}'.format(rg, nic, config, lb, bap1_id, rule1_id, private_ip),
                 checks=[JMESPathCheck('length(loadBalancerBackendAddressPools)', 2),
                         JMESPathCheck('length(loadBalancerInboundNatRules)', 2),
                         JMESPathCheck('privateIpAddress', private_ip),
                         JMESPathCheck('privateIpAllocationMethod', 'Static')])
        # test generic update
        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --set privateIpAddress=10.0.0.50'.format(rg, nic, config), checks=JMESPathCheck('privateIpAddress', '10.0.0.50'))

        # test ability to add and remove IDs one at a time with subcommands
        self.cmd('network nic ip-config inbound-nat-rule remove -g {} --lb-name {} --nic-name {} --ip-config-name {} --inbound-nat-rule rule1'.format(rg, lb, nic, config), checks=JMESPathCheck('length(loadBalancerInboundNatRules)', 1))
        self.cmd('network nic ip-config inbound-nat-rule add -g {} --lb-name {} --nic-name {} --ip-config-name {} --inbound-nat-rule rule1'.format(rg, lb, nic, config), checks=JMESPathCheck('length(loadBalancerInboundNatRules)', 2))

        self.cmd('network nic ip-config address-pool remove -g {} --lb-name {} --nic-name {} --ip-config-name {} --address-pool bap1'.format(rg, lb, nic, config), checks=JMESPathCheck('length(loadBalancerBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool add -g {} --lb-name {} --nic-name {} --ip-config-name {} --address-pool bap1'.format(rg, lb, nic, config), checks=JMESPathCheck('length(loadBalancerBackendAddressPools)', 2))

        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --private-ip-address "" --public-ip-address {}'.format(rg, nic, config, public_ip_id), checks=[JMESPathCheck('privateIpAllocationMethod', 'Dynamic'), JMESPathCheck("publicIpAddress.contains(id, '{}')".format(public_ip), True)])

        self.cmd('network nic ip-config update -g {} --nic-name {} -n {} --subnet {} --vnet-name {}'.format(rg, nic, config, subnet, vnet), checks=JMESPathCheck("subnet.contains(id, '{}')".format(subnet), True))


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


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkExtendedNSGScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_extended_nsg')
    def test_network_extended_nsg(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'nsg': 'nsg1',
            'rule': 'rule1'
        }
        self.cmd('network nsg create --name {nsg} -g {rg}'.format(**kwargs))
        self.cmd('network nsg rule create --access allow --destination-address-prefixes 10.0.0.0/24 11.0.0.0/24 --direction inbound --nsg-name {nsg} --protocol * -g {rg} --source-address-prefix * -n {rule} --source-port-range 700-900 1000-1100 --destination-port-range 4444 --priority 1000'.format(**kwargs), checks=[
            JMESPathCheckV2('length(destinationAddressPrefixes)', 2),
            JMESPathCheckV2('destinationAddressPrefix', ''),
            JMESPathCheckV2('length(sourceAddressPrefixes)', 0),
            JMESPathCheckV2('sourceAddressPrefix', '*'),
            JMESPathCheckV2('length(sourcePortRanges)', 2),
            JMESPathCheckV2('sourcePortRange', None),
            JMESPathCheckV2('length(destinationPortRanges)', 0),
            JMESPathCheckV2('destinationPortRange', '4444')
        ])
        self.cmd('network nsg rule update --destination-address-prefixes Internet --nsg-name {nsg} -g {rg} --source-address-prefix 10.0.0.0/24 11.0.0.0/24 -n {rule} --source-port-range * --destination-port-range 500-1000 2000 3000'.format(**kwargs), checks=[
            JMESPathCheckV2('length(destinationAddressPrefixes)', 0),
            JMESPathCheckV2('destinationAddressPrefix', 'Internet'),
            JMESPathCheckV2('length(sourceAddressPrefixes)', 2),
            JMESPathCheckV2('sourceAddressPrefix', ''),
            JMESPathCheckV2('length(sourcePortRanges)', 0),
            JMESPathCheckV2('sourcePortRange', '*'),
            JMESPathCheckV2('length(destinationPortRanges)', 3),
            JMESPathCheckV2('destinationPortRange', None)
        ])


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

        self.cmd('network nsg list', checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(rt), True)])
        self.cmd('network nsg list --resource-group {}'.format(rg), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(rt), True), JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)])
        self.cmd('network nsg show --resource-group {} --name {}'.format(rg, nsg), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('type', rt), JMESPathCheck('resourceGroup', rg), JMESPathCheck('name', nsg)])
        # Test for the manually added nsg rule
        self.cmd('network nsg rule list --resource-group {} --nsg-name {}'.format(rg, nsg), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck('length(@)', 1), JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(rg), True)])
        self.cmd('network nsg rule show --resource-group {} --nsg-name {} --name {}'.format(rg, nsg, nrn), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('resourceGroup', rg), JMESPathCheck('name', nrn)])

        # Test for updating the rule
        new_access = 'DENY'
        new_addr_prefix = '111'
        new_direction = 'Outbound'
        new_protocol = 'Tcp'
        new_port_range = '1234-1235'
        description = 'greatrule'
        priority = 888
        self.cmd('network nsg rule update -g {} --nsg-name {} -n {} --direction {} --access {} --destination-address-prefix {} --protocol {} --source-address-prefix {} --source-port-range {} --destination-port-range {} --priority {} --description {}'.format(rg, nsg, nrn, new_direction, new_access, new_addr_prefix, new_protocol, new_addr_prefix, new_port_range, new_port_range, priority, description), checks=[JMESPathCheck('access', 'Deny'), JMESPathCheck('direction', new_direction), JMESPathCheck('destinationAddressPrefix', new_addr_prefix), JMESPathCheck('protocol', new_protocol), JMESPathCheck('sourceAddressPrefix', new_addr_prefix), JMESPathCheck('sourcePortRange', new_port_range), JMESPathCheck('priority', priority), JMESPathCheck('description', description), ])

        # test generic update
        self.cmd('network nsg rule update -g {} --nsg-name {} -n {} --set description="cool"'.format(rg, nsg, nrn), checks=JMESPathCheck('description', 'cool'))

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

        self.cmd('network route-table list', checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network route-table list --resource-group {}'.format(self.resource_group), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck('length(@)', 1), JMESPathCheck('[0].name', self.route_table_name), JMESPathCheck('[0].resourceGroup', self.resource_group), JMESPathCheck('[0].type', self.resource_type)])
        self.cmd('network route-table show --resource-group {} --name {}'.format(self.resource_group, self.route_table_name), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('name', self.route_table_name), JMESPathCheck('resourceGroup', self.resource_group), JMESPathCheck('type', self.resource_type)])
        self.cmd('network route-table route list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name), checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network route-table route show --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_name), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('name', self.route_name), JMESPathCheck('resourceGroup', self.resource_group)])
        self.cmd('network route-table route delete --resource-group {} --route-table-name {} --name {}'.format(self.resource_group, self.route_table_name, self.route_name))
        # Expecting no results as the route operation was just deleted
        self.cmd('network route-table route list --resource-group {} --route-table-name {}'.format(self.resource_group, self.route_table_name), checks=NoneCheck())
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
        # verify the deployment result
        self.cmd('network vnet create --resource-group {} --name {} --subnet-name default'.format(self.resource_group, self.vnet_name), checks=[JMESPathCheck('newVNet.provisioningState', 'Succeeded'), JMESPathCheck('newVNet.addressSpace.addressPrefixes[0]', '10.0.0.0/16')])

        self.cmd('network vnet check-ip-address -g {} -n {} --ip-address 10.0.0.50'.format(self.resource_group, self.vnet_name), checks=JMESPathCheck('available', True))

        self.cmd('network vnet check-ip-address -g {} -n {} --ip-address 10.0.0.0'.format(self.resource_group, self.vnet_name), checks=JMESPathCheck('available', False))

        self.cmd('network vnet list', checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True)])
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group), checks=[JMESPathCheck('type(@)', 'array'), JMESPathCheck("length([?type == '{}']) == length(@)".format(self.resource_type), True), JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)])
        self.cmd('network vnet show --resource-group {} --name {}'.format(self.resource_group, self.vnet_name), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('name', self.vnet_name), JMESPathCheck('resourceGroup', self.resource_group), JMESPathCheck('type', self.resource_type)])

        vnet_addr_prefixes = '20.0.0.0/16 10.0.0.0/16'
        self.cmd('network vnet update --resource-group {} --name {} --address-prefixes {} --dns-servers 1.2.3.4'.format(self.resource_group, self.vnet_name, vnet_addr_prefixes), checks=[
            JMESPathCheck('length(addressSpace.addressPrefixes)', 2),
            JMESPathCheck('dhcpOptions.dnsServers[0]', '1.2.3.4')
        ])
        self.cmd('network vnet update -g {} -n {} --dns-servers ""'.format(self.resource_group, self.vnet_name), checks=[
            JMESPathCheck('length(addressSpace.addressPrefixes)', 2),
            JMESPathCheck('dhcpOptions.dnsServers', [])
        ])

        # test generic update
        self.cmd('network vnet update --resource-group {} --name {} --set addressSpace.addressPrefixes[0]="20.0.0.0/24"'.format(self.resource_group, self.vnet_name), checks=JMESPathCheck('addressSpace.addressPrefixes[0]', '20.0.0.0/24'))

        self.cmd('network vnet subnet create --resource-group {} --vnet-name {} --name {} --address-prefix {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name, '20.0.0.0/24'))

        self.cmd('network vnet subnet list --resource-group {} --vnet-name {}'.format(self.resource_group, self.vnet_name), checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('network vnet subnet show --resource-group {} --vnet-name {} --name {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name), checks=[JMESPathCheck('type(@)', 'object'), JMESPathCheck('name', self.vnet_subnet_name), JMESPathCheck('resourceGroup', self.resource_group)])

        # Test delete subnet
        self.cmd('network vnet subnet delete --resource-group {} --vnet-name {} --name {}'.format(self.resource_group, self.vnet_name, self.vnet_subnet_name))
        # Expecting the subnet to not be listed after delete
        self.cmd('network vnet subnet list --resource-group {} --vnet-name {}'.format(self.resource_group, self.vnet_name), checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_subnet_name), 0))

        # Test delete vnet
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group), checks=JMESPathCheck("length([?name == '{}'])".format(self.vnet_name), 1))
        self.cmd('network vnet delete --resource-group {} --name {}'.format(self.resource_group, self.vnet_name))
        # Expecting the vnet we deleted to not be listed after delete
        self.cmd('network vnet list --resource-group {}'.format(self.resource_group), NoneCheck())


class NetworkVNetPeeringScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vnet_peering')
    def test_network_vnet_peering(self, resource_group):
        rg = resource_group
        # create two vnets with non-overlapping prefixes
        self.cmd('network vnet create -g {} -n vnet1'.format(rg))
        self.cmd('network vnet create -g {} -n vnet2 --subnet-name GatewaySubnet --address-prefix 11.0.0.0/16 --subnet-prefix 11.0.0.0/24'.format(rg))
        # create supporting resources for gateway
        self.cmd('network public-ip create -g {} -n ip1'.format(rg))
        ip_id = self.cmd('network public-ip show -g {} -n ip1 --query id'.format(rg)).get_output_in_json()
        vnet_id = self.cmd('network vnet show -g {} -n vnet2 --query id'.format(rg)).get_output_in_json()
        # create the gateway on vnet2
        self.cmd('network vnet-gateway create -g {} -n gateway1 --public-ip-address {} --vnet {}'.format(rg, ip_id, vnet_id))

        vnet1_id = self.cmd('network vnet show -g {} -n vnet1 --query id'.format(rg)).get_output_in_json()
        vnet2_id = self.cmd('network vnet show -g {} -n vnet2 --query id'.format(rg)).get_output_in_json()
        # set up gateway sharing from vnet1 to vnet2
        self.cmd('network vnet peering create -g {} -n peering2 --vnet-name vnet2 --remote-vnet-id {} --allow-gateway-transit'.format(rg, vnet1_id), checks=[
            JMESPathCheckV2('allowGatewayTransit', True),
            JMESPathCheckV2('remoteVirtualNetwork.id', vnet1_id),
            JMESPathCheckV2('peeringState', 'Initiated')
        ])
        self.cmd('network vnet peering create -g {} -n peering1 --vnet-name vnet1 --remote-vnet-id {} --use-remote-gateways --allow-forwarded-traffic'.format(rg, vnet2_id), checks=[
            JMESPathCheckV2('useRemoteGateways', True),
            JMESPathCheckV2('remoteVirtualNetwork.id', vnet2_id),
            JMESPathCheckV2('peeringState', 'Connected'),
            JMESPathCheckV2('allowVirtualNetworkAccess', False)
        ])
        self.cmd('network vnet peering show -g {} -n peering1 --vnet-name vnet1'.format(rg),
                 checks=JMESPathCheckV2('name', 'peering1'))
        self.cmd('network vnet peering list -g {} --vnet-name vnet2'.format(rg), checks=[
            JMESPathCheckV2('[0].name', 'peering2'),
            JMESPathCheckV2('length(@)', 1)
        ])
        self.cmd('network vnet peering update -g {} -n peering1 --vnet-name vnet1 --set useRemoteGateways=false'.format(rg), checks=[
            JMESPathCheckV2('useRemoteGateways', False),
            JMESPathCheckV2('allowForwardedTraffic', True)
        ])
        self.cmd('network vnet peering delete -g {} -n peering1 --vnet-name vnet1'.format(rg))
        self.cmd('network vnet peering list -g {} --vnet-name vnet1'.format(rg), checks=NoneCheck())
        # must delete the second peering and the gateway or the resource group delete will fail
        self.cmd('network vnet peering delete -g {} -n peering2 --vnet-name vnet2'.format(rg))
        self.cmd('network vnet-gateway delete -g {} -n gateway1'.format(rg))


class NetworkVpnConnectionIpSecPolicy(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_connection_ipsec')
    def test_network_vpn_connection_ipsec(self, resource_group):

        kwargs = {
            'rg': resource_group,
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
        }

        self.cmd('network vnet create -g {rg} -n {vnet1} --address-prefix {vnet_prefix1} {vnet_prefix2}'.format(**kwargs))
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet1} -n {fe_sub1} --address-prefix {fe_sub_prefix1}'.format(**kwargs))
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet1} -n {be_sub1} --address-prefix {be_sub_prefix1}'.format(**kwargs))
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet1} -n {gw_sub1} --address-prefix {gw_sub_prefix1}'.format(**kwargs))
        self.cmd('network public-ip create -g {rg} -n {gw1ip}'.format(**kwargs))

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --public-ip-address {gw1ip} --vnet {vnet1} --sku {gw1_sku}'.format(**kwargs))
        self.cmd('network local-gateway create -g {rg} -n {lgw1} --gateway-ip-address {lgw1ip} --local-address-prefixes {lgw1_prefix1} {lgw1_prefix2}'.format(**kwargs))
        self.cmd('network vpn-connection create -g {rg} -n {conn1} --vnet-gateway1 {gw1} --local-gateway2 {lgw1} --shared-key AzureA1b2C3'.format(**kwargs))

        self.cmd('network vpn-connection ipsec-policy add -g {rg} --connection-name {conn1} --ike-encryption AES256 --ike-integrity SHA384 --dh-group DHGroup24 --ipsec-encryption GCMAES256 --ipsec-integrity GCMAES256 --pfs-group PFS24 --sa-lifetime 7200 --sa-max-size 2048'.format(**kwargs))
        self.cmd('network vpn-connection ipsec-policy list -g {rg} --connection-name {conn1}'.format(**kwargs))
        self.cmd('network vpn-connection ipsec-policy clear -g {rg} --connection-name {conn1}'.format(**kwargs))
        self.cmd('network vpn-connection ipsec-policy list -g {rg} --connection-name {conn1}'.format(**kwargs))

        # TODO: Continue with the VNET-to-VNET scenario... >_>


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

        self.cmd('network vnet create --resource-group {} --name {} --address-prefix {} --subnet-name {} --subnet-prefix {}'.format(self.resource_group, self.vnet_name, vnet_addr_prefix, subnet_name, subnet_addr_prefix))
        self.cmd('network nsg create --resource-group {} --name {}'.format(self.resource_group, nsg_name))

        # Test we can update the address space and nsg
        self.cmd('network vnet subnet update --resource-group {} --vnet-name {} --name {} --address-prefix {} --network-security-group {}'.format(self.resource_group, self.vnet_name, subnet_name, subnet_addr_prefix_new, nsg_name), checks=[JMESPathCheck('addressPrefix', subnet_addr_prefix_new), JMESPathCheck('ends_with(@.networkSecurityGroup.id, `{}`)'.format('/' + nsg_name), True)])

        # test generic update
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --set addressPrefix=123.0.0.0/24'.format(self.resource_group, self.vnet_name, subnet_name), checks=JMESPathCheck('addressPrefix', '123.0.0.0/24'))

        # Test we can get rid of the nsg.
        self.cmd('network vnet subnet update --resource-group {} --vnet-name {} --name {} --address-prefix {} --network-security-group {}'.format(self.resource_group, self.vnet_name, subnet_name, subnet_addr_prefix_new, '\"\"'), checks=JMESPathCheck('networkSecurityGroup', None))

        self.cmd('network vnet delete --resource-group {} --name {}'.format(self.resource_group, self.vnet_name))
        self.cmd('network nsg delete --resource-group {} --name {}'.format(self.resource_group, nsg_name))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkSubnetEndpointServiceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_subnet_endpoint_service_test')
    def test_network_subnet_endpoint_service(self, resource_group):
        kwargs = {
            'rg': resource_group,
            'vnet': 'vnet1',
            'subnet': 'subnet1'
        }
        self.cmd('network vnet list-endpoint-services -l westus', checks=[
            JMESPathCheckV2('length(@)', 2),
            JMESPathCheckV2('@[0].name', 'Microsoft.Storage')
        ])
        self.cmd('network vnet create -g {rg} -n {vnet}'.format(**kwargs))
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.1.0/24 --service-endpoints Microsoft.Storage'.format(**kwargs),
                 checks=JMESPathCheckV2('serviceEndpoints[0].service', 'Microsoft.Storage'))
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints ""'.format(**kwargs),
                 checks=JMESPathCheckV2('serviceEndpoints', None))


class NetworkActiveActiveCrossPremiseScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

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
        sk2 = self.cmd('network vpn-connection shared-key show -g {} --connection-name {}'.format(rg, conn_151), checks=JMESPathCheck('value', shared_key2))
        self.assertNotEqual(sk1, sk2)

        lgw3 = 'lgw3'
        lgw3_ip = '131.107.72.23'
        lgw3_prefix = '10.52.255.254/32'
        bgp_peer2 = '10.52.255.254'

        # create and connect second local-gateway
        self.cmd('network local-gateway create -g {} -n {} -l {} --gateway-ip-address {} --local-address-prefixes {} --asn {} --bgp-peering-address {}'.format(rg, lgw3, lgw_loc, lgw3_ip, lgw3_prefix, lgw_asn, bgp_peer2))
        self.cmd('network vpn-connection create -g {} -n {} --vnet-gateway1 {} --local-gateway2 {} --shared-key {} --enable-bgp'.format(rg, conn_152, gw1, lgw3, shared_key))


class NetworkActiveActiveVnetVnetScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

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


@api_version_constraint(ResourceType.MGMT_NETWORK, max_api='2015-06-15')
class NetworkVpnGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_gateway')
    def test_network_vpn_gateway(self, resource_group):
        vnet1_name = 'myvnet1'
        vnet2_name = 'myvnet2'
        vnet3_name = 'myvnet3'
        gateway1_name = 'gateway1'
        gateway2_name = 'gateway2'
        gateway3_name = 'gateway3'
        ip1_name = 'pubip1'
        ip2_name = 'pubip2'
        ip3_name = 'pubip3'
        rg = resource_group

        self.cmd('network public-ip create -n {} -g {}'.format(ip1_name, rg))
        self.cmd('network public-ip create -n {} -g {}'.format(ip2_name, rg))
        self.cmd('network public-ip create -n {} -g {}'.format(ip3_name, rg))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.0.0/24'.format(rg, vnet1_name))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.1.0.0/16'.format(rg, vnet2_name))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.2.0.0/16'.format(rg, vnet3_name))

        subscription_id = MOCKED_SUBSCRIPTION_ID if not self.in_recording \
            else self.cmd('account list --query "[?isDefault].id"').get_output_in_json()[0]

        vnet1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(subscription_id, rg, vnet1_name)
        vnet2_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(subscription_id, rg, vnet2_name)

        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait'.format(rg, gateway1_name, vnet1_id, ip1_name))
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait'.format(rg, gateway2_name, vnet2_id, ip2_name))
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait --sku standard --asn 12345 --bgp-peering-address 10.2.250.250 --peer-weight 50'.format(rg, gateway3_name, vnet3_name, ip3_name))

        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gateway1_name))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gateway2_name))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gateway3_name))

        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, gateway1_name), checks=[
            JMESPathCheckV2('gatewayType', 'Vpn'),
            JMESPathCheckV2('sku.capacity', 2),
            JMESPathCheckV2('sku.name', 'Basic'),
            JMESPathCheckV2('vpnType', 'RouteBased'),
            JMESPathCheckV2('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, gateway2_name), checks=[
            JMESPathCheckV2('gatewayType', 'Vpn'),
            JMESPathCheckV2('sku.capacity', 2),
            JMESPathCheckV2('sku.name', 'Basic'),
            JMESPathCheckV2('vpnType', 'RouteBased'),
            JMESPathCheckV2('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, gateway3_name), checks=[
            JMESPathCheckV2('sku.name', 'Standard'),
            JMESPathCheckV2('enableBgp', True),
            JMESPathCheckV2('bgpSettings.asn', 12345),
            JMESPathCheckV2('bgpSettings.bgpPeeringAddress', '10.2.250.250'),
            JMESPathCheckV2('bgpSettings.peerWeight', 50)
        ])

        conn12 = 'conn1to2'
        gateway1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworkGateways/{}'.format(subscription_id, rg, gateway1_name)
        self.cmd('network vpn-connection create -n {} -g {} --shared-key 123 --vnet-gateway1 {} --vnet-gateway2 {}'.format(conn12, rg, gateway1_id, gateway2_name))
        self.cmd('network vpn-connection update -n {} -g {} --routing-weight 25'.format(conn12, rg),
                 checks=JMESPathCheckV2('routingWeight', 25))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2016-09-01')
class NetworkVpnGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_gateway')
    def test_network_vpn_gateway(self, resource_group):
        vnet1_name = 'myvnet1'
        vnet2_name = 'myvnet2'
        vnet3_name = 'myvnet3'
        gateway1_name = 'gateway1'
        gateway2_name = 'gateway2'
        gateway3_name = 'gateway3'
        ip1_name = 'pubip1'
        ip2_name = 'pubip2'
        ip3_name = 'pubip3'
        rg = resource_group

        self.cmd('network public-ip create -n {} -g {}'.format(ip1_name, rg))
        self.cmd('network public-ip create -n {} -g {}'.format(ip2_name, rg))
        self.cmd('network public-ip create -n {} -g {}'.format(ip3_name, rg))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.0.0/24'.format(rg, vnet1_name))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.1.0.0/16'.format(rg, vnet2_name))
        self.cmd('network vnet create -g {} -n {} --subnet-name GatewaySubnet --address-prefix 10.2.0.0/16'.format(rg, vnet3_name))

        subscription_id = MOCKED_SUBSCRIPTION_ID if not self.in_recording \
            else self.cmd('account list --query "[?isDefault].id"').get_output_in_json()[0]

        vnet1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(subscription_id, rg, vnet1_name)
        vnet2_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(subscription_id, rg, vnet2_name)

        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait'.format(rg, gateway1_name, vnet1_id, ip1_name))
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait'.format(rg, gateway2_name, vnet2_id, ip2_name))
        self.cmd('network vnet-gateway create -g {} -n {} --vnet {} --public-ip-address {} --no-wait --sku standard --asn 12345 --bgp-peering-address 10.2.250.250 --peer-weight 50'.format(rg, gateway3_name, vnet3_name, ip3_name))

        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gateway1_name))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gateway2_name))
        self.cmd('network vnet-gateway wait -g {} -n {} --created'.format(rg, gateway3_name))

        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, gateway1_name), checks=[
            JMESPathCheckV2('gatewayType', 'Vpn'),
            JMESPathCheckV2('sku.capacity', 2),
            JMESPathCheckV2('sku.name', 'Basic'),
            JMESPathCheckV2('vpnType', 'RouteBased'),
            JMESPathCheckV2('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, gateway2_name), checks=[
            JMESPathCheckV2('gatewayType', 'Vpn'),
            JMESPathCheckV2('sku.capacity', 2),
            JMESPathCheckV2('sku.name', 'Basic'),
            JMESPathCheckV2('vpnType', 'RouteBased'),
            JMESPathCheckV2('enableBgp', False)
        ])
        self.cmd('network vnet-gateway show -g {} -n {}'.format(rg, gateway3_name), checks=[
            JMESPathCheckV2('sku.name', 'Standard'),
            JMESPathCheckV2('enableBgp', True),
            JMESPathCheckV2('bgpSettings.asn', 12345),
            JMESPathCheckV2('bgpSettings.bgpPeeringAddress', '10.2.250.250'),
            JMESPathCheckV2('bgpSettings.peerWeight', 50)
        ])

        conn12 = 'conn1to2'
        conn21 = 'conn2to1'
        gateway1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworkGateways/{}'.format(subscription_id, rg, gateway1_name)
        self.cmd('network vpn-connection create -n {} -g {} --shared-key 123 --vnet-gateway1 {} --vnet-gateway2 {}'.format(conn12, rg, gateway1_id, gateway2_name))
        self.cmd('network vpn-connection update -n {} -g {} --routing-weight 25'.format(conn12, rg),
                 checks=JMESPathCheckV2('routingWeight', 25))
        self.cmd('network vpn-connection create -n {} -g {} --shared-key 123 --vnet-gateway2 {} --vnet-gateway1 {}'.format(conn21, rg, gateway1_id, gateway2_name))

        self.cmd('network vnet-gateway list-learned-routes -g {} -n {}'.format(rg, gateway1_name))
        self.cmd('network vnet-gateway list-advertised-routes -g {} -n {} --peer 10.1.1.1'.format(rg, gateway1_name))
        self.cmd('network vnet-gateway list-bgp-peer-status -g {} -n {} --peer 10.1.1.1'.format(rg, gateway1_name))


@api_version_constraint(ResourceType.MGMT_NETWORK, max_api='2017-06-01')
class NetworkVpnClientPackageScenarioTest(ScenarioTest):

    @ResourceGroupPreparer('cli_test_vpn_client_package')
    def test_vpn_client_package(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'vnet': 'vnet1',
            'public_ip': 'pip1',
            'gateway_prefix': '100.1.1.0/24',
            'gateway': 'vgw1',
            'cert': 'cert1',
            'cert_path': os.path.join(TEST_DIR, 'test-root-cert.cer')
        }

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet'.format(**kwargs))
        self.cmd('network public-ip create -g {rg} -n {public_ip}'.format(**kwargs))
        self.cmd('network vnet-gateway create -g {rg} -n {gateway} --address-prefix {gateway_prefix} --vnet {vnet} --public-ip-address {public_ip}'.format(**kwargs))
        self.cmd('network vnet-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert} --public-cert-data "{cert_path}"'.format(**kwargs))
        output = self.cmd('network vnet-gateway vpn-client generate -g {rg} -n {gateway} --processor-architecture X86'.format(**kwargs)).get_output_in_json()
        self.assertTrue('.exe' in output, 'Expected EXE file in output.\nActual: {}'.format(output))
        output = self.cmd('network vnet-gateway vpn-client generate -g {rg} -n {gateway} --processor-architecture Amd64'.format(**kwargs)).get_output_in_json()
        self.assertTrue('.exe' in output, 'Expected EXE file in output.\nActual: {}'.format(output))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-06-01')
class NetworkVpnClientPackageScenarioTest(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer('cli_test_vpn_client_package')
    def test_vpn_client_package(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'vnet': 'vnet1',
            'public_ip': 'pip1',
            'gateway_prefix': '100.1.1.0/24',
            'gateway': 'vgw1',
            'cert': 'cert1',
            'cert_path': os.path.join(TEST_DIR, 'test-root-cert.cer')
        }

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet'.format(**kwargs))
        self.cmd('network public-ip create -g {rg} -n {public_ip}'.format(**kwargs))
        self.cmd('network vnet-gateway create -g {rg} -n {gateway} --address-prefix {gateway_prefix} --vnet {vnet} --public-ip-address {public_ip}'.format(**kwargs))
        self.cmd('network vnet-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert} --public-cert-data "{cert_path}"'.format(**kwargs))
        output = self.cmd('network vnet-gateway vpn-client generate -g {rg} -n {gateway}'.format(**kwargs)).get_output_in_json()
        self.assertTrue('.zip' in output, 'Expected ZIP file in output.\nActual: {}'.format(str(output)))
        output = self.cmd('network vnet-gateway vpn-client show-url -g {rg} -n {gateway}'.format(**kwargs)).get_output_in_json()
        self.assertTrue('.zip' in output, 'Expected ZIP file in output.\nActual: {}'.format(str(output)))


class NetworkTrafficManagerScenarioTest(ScenarioTest):

    @ResourceGroupPreparer('cli_test_traffic_manager')
    def test_network_traffic_manager(self, resource_group):
        self.resource_group = resource_group
        tm_name = 'mytmprofile'
        endpoint_name = 'myendpoint'
        unique_dns_name = 'mytrafficmanager001100a'

        self.cmd('network traffic-manager profile check-dns -n myfoobar1')
        self.cmd('network traffic-manager profile create -n {} -g {} --routing-method priority --unique-dns-name {}'.format(tm_name, self.resource_group, unique_dns_name), checks=JMESPathCheckV2('TrafficManagerProfile.trafficRoutingMethod', 'Priority'))
        self.cmd('network traffic-manager profile show -g {} -n {}'.format(self.resource_group, tm_name), checks=JMESPathCheckV2('dnsConfig.relativeName', unique_dns_name))
        self.cmd('network traffic-manager profile update -n {} -g {} --routing-method weighted'.format(tm_name, self.resource_group), checks=JMESPathCheckV2('trafficRoutingMethod', 'Weighted'))
        self.cmd('network traffic-manager profile list -g {}'.format(self.resource_group))

        # Endpoint tests
        self.cmd('network traffic-manager endpoint create -n {} --profile-name {} -g {} --type externalEndpoints --weight 50 --target www.microsoft.com'.format(endpoint_name, tm_name, self.resource_group), checks=JMESPathCheckV2('type', 'Microsoft.Network/trafficManagerProfiles/externalEndpoints'))
        self.cmd('network traffic-manager endpoint update -n {} --profile-name {} -g {} --type externalEndpoints --weight 25 --target www.contoso.com'.format(endpoint_name, tm_name, self.resource_group), checks=[JMESPathCheckV2('weight', 25), JMESPathCheckV2('target', 'www.contoso.com')])
        self.cmd('network traffic-manager endpoint show -g {} --profile-name {} -t externalEndpoints -n {}'.format(self.resource_group, tm_name, endpoint_name))
        self.cmd('network traffic-manager endpoint list -g {} --profile-name {} -t externalEndpoints'.format(self.resource_group, tm_name), checks=JMESPathCheckV2('length(@)', 1))

        # ensure that a profile with endpoints can be updated
        self.cmd('network traffic-manager profile update -n {} -g {}'.format(tm_name, self.resource_group))

        self.cmd('network traffic-manager endpoint delete -g {} --profile-name {} -t externalEndpoints -n {}'.format(self.resource_group, tm_name, endpoint_name))
        self.cmd('network traffic-manager endpoint list -g {} --profile-name {} -t externalEndpoints'.format(self.resource_group, tm_name), checks=JMESPathCheckV2('length(@)', 0))

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
        self.cmd('network dns zone list -g {}'.format(rg), checks=JMESPathCheck('length(@)', 1))

        base_record_sets = 2
        self.cmd('network dns zone show -n {} -g {}'.format(zone_name, rg), checks=[JMESPathCheck('numberOfRecordSets', base_record_sets)])

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
            self.cmd('network dns record-set {0} create -n myrs{0} -g {1} --zone-name {2}'.format(t, rg, zone_name))
            add_command = 'set-record' if t == 'cname' else 'add-record'
            self.cmd('network dns record-set {0} {4} -g {1} --zone-name {2} --record-set-name myrs{0} {3}'.format(t, rg, zone_name, args[t], add_command))
            # test creating the record set at the same time you add records
            self.cmd('network dns record-set {0} {4} -g {1} --zone-name {2} --record-set-name myrs{0}alt {3}'.format(t, rg, zone_name, args[t], add_command))

        self.cmd('network dns record-set {0} add-record -g {1} --zone-name {2} --record-set-name myrs{0} {3}'.format('a', rg, zone_name, '--ipv4-address 10.0.0.11'))
        self.cmd('network dns record-set soa update -g {0} --zone-name {1} {2}'.format(rg, zone_name, args['soa']))

        long_value = '0123456789' * 50
        self.cmd('network dns record-set txt add-record -g {} -z {} -n longtxt -v {}'.format(rg, zone_name, long_value))

        typed_record_sets = 2 * len(record_types) + 1
        self.cmd('network dns zone show -n {} -g {}'.format(zone_name, rg), checks=[JMESPathCheck('numberOfRecordSets', base_record_sets + typed_record_sets)])
        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'.format('a', rg, zone_name), checks=[JMESPathCheck('length(arecords)', 2)])

        # test list vs. list type
        self.cmd('network dns record-set list -g {} -z {}'.format(rg, zone_name), checks=JMESPathCheck('length(@)', base_record_sets + typed_record_sets))

        self.cmd('network dns record-set txt list -g {} -z {}'.format(rg, zone_name), checks=JMESPathCheck('length(@)', 3))

        for t in record_types:
            self.cmd('network dns record-set {0} remove-record -g {1} --zone-name {2} --record-set-name myrs{0} {3}'.format(t, rg, zone_name, args[t]))

        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'.format('a', rg, zone_name), checks=[JMESPathCheck('length(arecords)', 1)])

        self.cmd('network dns record-set {0} remove-record -g {1} --zone-name {2} --record-set-name myrs{0} {3}'.format('a', rg, zone_name, '--ipv4-address 10.0.0.11'))

        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'.format('a', rg, zone_name), checks=NoneCheck())

        self.cmd('network dns record-set {0} delete -n myrs{0} -g {1} --zone-name {2} -y'.format('a', rg, zone_name))
        self.cmd('network dns record-set {0} show -n myrs{0} -g {1} --zone-name {2}'.format('a', rg, zone_name), allowed_exceptions='does not exist in resource group')

        self.cmd('network dns zone delete -g {} -n {} -y'.format(rg, zone_name), checks=NoneCheck())


class NetworkZoneImportExportTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_dns_zone_import_export')
    def test_network_dns_zone_import_export(self, resource_group):
        zone_name = 'myzone.com'
        zone_file_path = os.path.join(TEST_DIR, 'zone_files', 'zone1.txt')

        self.cmd('network dns zone import -n {} -g {} --file-name "{}"'.format(zone_name, resource_group, zone_file_path))
        self.cmd('network dns zone export -n {} -g {}'.format(zone_name, resource_group))

# TODO: Troubleshoot VNET gateway issue and re-enable
# class NetworkWatcherScenarioTest(ScenarioTest):
#    import mock

#    def _mock_thread_count():
#        return 1

#    @mock.patch('azure.cli.command_modules.vm._actions._get_thread_count', _mock_thread_count)
#    @ResourceGroupPreparer(name_prefix='cli_test_network_watcher', location='westcentralus')
#    @StorageAccountPreparer(name_prefix='clitestnw', location='westcentralus')
#    def test_network_watcher(self, resource_group, storage_account):

#        location = 'westcentralus'
#        vm = 'vm1'
#        nsg = '{}NSG'.format(vm)
#        capture = 'capture1'

#        self.cmd('network watcher configure -g {} --locations westus westus2 westcentralus --enabled'.format(resource_group))
#        self.cmd('network watcher configure --locations westus westus2 --tags foo=doo')
#        self.cmd('network watcher configure -l westus2 --enabled false')
#        self.cmd('network watcher list')

#        # set up resource to troubleshoot
#        self.cmd('storage container create -n troubleshooting --account-name {}'.format(storage_account))
#        sa = self.cmd('storage account show -g {} -n {}'.format(resource_group, storage_account)).get_output_in_json()
#        storage_path = sa['primaryEndpoints']['blob'] + 'troubleshooting'
#        self.cmd('network vnet create -g {} -n vnet1 --subnet-name GatewaySubnet'.format(resource_group))
#        self.cmd('network public-ip create -g {} -n vgw1-pip'.format(resource_group))
#        self.cmd('network vnet-gateway create -g {} -n vgw1 --vnet vnet1 --public-ip-address vgw1-pip --no-wait'.format(resource_group))

#        # create VM with NetworkWatcher extension
#        self.cmd('vm create -g {} -n {} --image UbuntuLTS --authentication-type password --admin-username deploy --admin-password PassPass10!)'.format(resource_group, vm))
#        self.cmd('vm extension set -g {} --vm-name {} -n NetworkWatcherAgentLinux --publisher Microsoft.Azure.NetworkWatcher'.format(resource_group, vm))

#        self.cmd('network watcher show-topology -g {}'.format(resource_group))

#        self.cmd('network watcher test-ip-flow -g {} --vm {} --direction inbound --local 10.0.0.4:22 --protocol tcp --remote 100.1.2.3:*'.format(resource_group, vm))
#        self.cmd('network watcher test-ip-flow -g {} --vm {} --direction outbound --local 10.0.0.4:* --protocol tcp --remote 100.1.2.3:80'.format(resource_group, vm))

#        self.cmd('network watcher show-security-group-view -g {} --vm {}'.format(resource_group, vm))

#        self.cmd('network watcher show-next-hop -g {} --vm {} --source-ip 123.4.5.6 --dest-ip 10.0.0.6'.format(resource_group, vm))

#        self.cmd('network watcher test-connectivity -g {} --source-resource {} --dest-address www.microsoft.com --dest-port 80'.format(resource_group, vm))

#        self.cmd('network watcher flow-log configure -g {} --nsg {} --enabled --retention 5 --storage-account {}'.format(resource_group, nsg, storage_account))
#        self.cmd('network watcher flow-log configure -g {} --nsg {} --retention 0'.format(resource_group, nsg))
#        self.cmd('network watcher flow-log show -g {} --nsg {}'.format(resource_group, nsg))

#        # test packet capture
#        self.cmd('network watcher packet-capture create -g {} --vm {} -n {} --file-path capture/capture.cap'.format(resource_group, vm, capture))
#        self.cmd('network watcher packet-capture show -l {} -n {}'.format(location, capture))
#        self.cmd('network watcher packet-capture stop -l {} -n {}'.format(location, capture))
#        self.cmd('network watcher packet-capture show-status -l {} -n {}'.format(location, capture))
#        self.cmd('network watcher packet-capture list -l {}'.format(location, capture))
#        self.cmd('network watcher packet-capture delete -l {} -n {}'.format(location, capture))
#        self.cmd('network watcher packet-capture list -l {}'.format(location, capture))

#        # test troubleshooting
#        self.cmd('network vnet-gateway wait -g {} -n vgw1 --created'.format(resource_group))
#        self.cmd('network watcher troubleshooting start --resource vgw1 -t vnetGateway -g {} --storage-account {} --storage-path {}'.format(resource_group, storage_account, storage_path))
#        self.cmd('network watcher troubleshooting show --resource vgw1 -t vnetGateway -g {}'.format(resource_group))


if __name__ == '__main__':
    unittest.main()
