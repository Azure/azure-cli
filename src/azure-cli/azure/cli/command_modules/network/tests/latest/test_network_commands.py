# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
import os
import unittest
import tempfile

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import supported_api_version, ResourceType
from azure.core.exceptions import HttpResponseError
from .recording_processors import StorageAccountSASReplacer

from azure.cli.testsdk import (
    ScenarioTest, LiveScenarioTest, LocalContextScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, live_only,
    KeyVaultPreparer, record_only)

from knack.util import CLIError

from msrestazure.tools import resource_id

from .credential_replacer import ExpressRoutePortLOAContentReplacer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class NetworkApplicationSecurityGroupScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_asg')
    def test_network_asg(self, resource_group):

        self.kwargs.update({
            'asg': 'asg1'
        })

        count1 = len(self.cmd('network asg list').get_output_in_json())
        self.cmd('network asg create -g {rg} -n {asg} --tags foo=doo',
                 checks=self.check('tags.foo', 'doo'))
        self.cmd('network asg update -g {rg} -n {asg} --tags foo=bar',
                 checks=self.check('tags.foo', 'bar'))
        count2 = len(self.cmd('network asg list').get_output_in_json())
        self.assertTrue(count2 == count1 + 1)
        self.cmd('network asg show -g {rg} -n {asg}', checks=[
            self.check('name', '{asg}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags.foo', 'bar')
        ])
        self.cmd('network asg delete -g {rg} -n {asg}')
        count3 = len(self.cmd('network asg list').get_output_in_json())
        self.assertTrue(count3 == count1)


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

        # test network lb update command
        self.cmd('network lb update -g {rg} -n {lb} --set tags.CostCenter=MyTestGroup')
        self.cmd('network lb show -g {rg} -n {lb}', checks=[
            self.check('tags.CostCenter', 'MyTestGroup')
        ])

        self.cmd('network public-ip show -g {rg} -n {ip}', checks=[
            self.check('sku.name', 'Standard'),
            self.check('publicIpAllocationMethod', 'Static')
        ])


class NetworkPrivateEndpoints(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_private_endpoints')
    def test_network_private_endpoints(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'sku': 'Standard',
            'vnet': 'vnet1',
            'subnet1': 'subnet1',
            'subnet2': 'subnet2',
            'location': 'centralus',
            'ip': 'pubip1',
            'lks1': 'lks1',
            'lks2': 'lks2',
            'pe': 'pe1',
            'rg': resource_group,
            'nic': 'nic1',
        })

        # Create PLS
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet1} -l {location}')
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --public-ip-address {ip} --sku {sku}')
        self.cmd('network vnet subnet update -g {rg} -n {subnet1} --vnet-name {vnet} --disable-private-link-service-network-policies')
        self.cmd('network vnet subnet create -g {rg} -n {subnet2} --vnet-name {vnet} --address-prefixes 10.0.2.0/24')
        self.cmd('network vnet subnet update -g {rg} -n {subnet2} --vnet-name {vnet} --disable-private-endpoint-network-policies')
        pls1 = self.cmd('network private-link-service create -g {rg} -n {lks1} --vnet-name {vnet} --subnet {subnet1} --lb-name {lb} --lb-frontend-ip-configs LoadBalancerFrontEnd -l {location}', checks=[
            self.check('type', 'Microsoft.Network/privateLinkServices'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['lks1'])
        ]).get_output_in_json()
        self.kwargs['pls_id'] = pls1['id']
        self.cmd('network private-endpoint list-types -l {location}')

        self.cmd('network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet2} --private-connection-resource-id {pls_id} --connection-name tttt -l {location} --nic-name {nic}', checks=[
            self.check('name', 'pe1'),
            self.check('provisioningState', 'Succeeded'),
            self.check('customNetworkInterfaceName', self.kwargs['nic']),
        ])

        # temporarily disable the test
        '''
        self.cmd('network private-endpoint update -g {rg} -n {pe} --request-message "test"', checks=[
            self.check('privateLinkServiceConnections[0].requestMessage', 'test')
        ])
        '''

        self.cmd('network private-endpoint list')
        self.cmd('network private-endpoint list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        pe_connection_name = self.cmd('network private-link-service show -g {rg} -n {lks1}').get_output_in_json()['privateEndpointConnections'][0]['name']
        self.kwargs['pe_connect'] = pe_connection_name
        self.cmd('network private-link-service connection update -g {rg} -n {pe_connect} --service-name {lks1} --connection-status Rejected --action-required "need action"')
        self.cmd('network private-endpoint show -g {rg} -n {pe}', checks=[
            self.check('privateLinkServiceConnections[0].privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('privateLinkServiceConnections[0].privateLinkServiceConnectionState.actionsRequired', "need action")
        ])
        self.cmd('network private-link-service connection delete -g {rg} -n {pe_connect} --service-name {lks1}')
        self.cmd('network private-link-service show -g {rg} -n {lks1}', checks=[
            self.check('length(privateEndpointConnections)', 0)
        ])
        self.cmd('network private-endpoint delete -g {rg} -n {pe}')

    @ResourceGroupPreparer(name_prefix="cli_test_network_private_endpoint_", location="eastus")
    @StorageAccountPreparer(name_prefix="ipconfig", kind="StorageV2")
    def test_network_private_endpoint_ip_config(self, storage_account):
        self.kwargs.update({
            "sa": storage_account,
            "loc": "eastus",
            "vnet": self.create_random_name("vnet-", 24),
            "subnet": self.create_random_name("subnet-", 24),
            "pe": self.create_random_name("pe-", 24),
            "connection": self.create_random_name("connection-", 24),
            "ipconfig1": "ipconfig1",
            "ipconfig2": "ipconfig2",
        })

        # prepare network
        self.cmd("network vnet create -n {vnet} -l {loc} -g {rg} --address-prefixes 10.0.0.0/16 --subnet-name {subnet} --subnet-prefixes 10.0.0.0/24")
        self.cmd("network vnet subnet update -n {subnet} -g {rg} --vnet-name {vnet} --disable-private-endpoint-network-policies true")

        # create private endpoint connection
        pl_resources = self.cmd("storage account private-link-resource list --account-name {sa} -g {rg}").get_output_in_json()
        self.kwargs["group_id"] = pl_resources[0]["groupId"]
        self.kwargs["sa_id"] = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()["id"]
        self.cmd(
            "network private-endpoint create -n {pe} -g {rg} --vnet-name {vnet} --subnet {subnet} --connection-name {connection} --group-id {group_id} --private-connection-resource-id {sa_id} "
            "--ip-config name={ipconfig1} group-id={group_id} member-name=blob private-ip-address=10.0.0.4 "
            "--ip-config name={ipconfig2} group-id={group_id} member-name=blob2 private-ip-address=10.0.0.6",
            checks=[
                self.check("length(ipConfigurations)", 2),
                self.check("ipConfigurations[0].name", self.kwargs["ipconfig1"]),
                self.check("ipConfigurations[1].name", self.kwargs["ipconfig2"]),
            ]
        )

        # check ip configuration operations
        self.cmd(
            "network private-endpoint ip-config remove -n {ipconfig2} -g {rg} --endpoint-name {pe}",
            checks=[
                self.check("length(ipConfigurations)", 1),
                self.check("ipConfigurations[0].name", self.kwargs["ipconfig1"]),
            ]
        )
        self.cmd(
            "network private-endpoint ip-config add -n {ipconfig2} -g {rg} --endpoint-name {pe} --group-id {group_id} --member-name blob2 --private-ip-address 10.0.0.6",
            checks=[
                self.check("length(ipConfigurations)", 2),
                self.check("ipConfigurations[1].name", self.kwargs["ipconfig2"]),
            ]
        )
        self.cmd(
            "network private-endpoint ip-config list -g {rg} --endpoint-name {pe}",
            checks=[
                self.check("length(@)", 2),
                self.check("@[0].name", self.kwargs["ipconfig1"]),
                self.check("@[1].name", self.kwargs["ipconfig2"]),
            ]
        )

    @ResourceGroupPreparer(name_prefix="cli_test_network_private_endpoint_", location="eastus")
    @StorageAccountPreparer(name_prefix="asg", kind="StorageV2")
    def test_network_private_endpoint_asg(self, storage_account):
        self.kwargs.update({
            "sa": storage_account,
            "loc": "eastus",
            "vnet": self.create_random_name("vnet-", 24),
            "subnet": self.create_random_name("subnet-", 24),
            "pe": self.create_random_name("pe-", 24),
            "connection": self.create_random_name("connection-", 24),
            "asg1": "asg1",
            "asg2": "asg2",
        })

        # prepare network
        self.cmd("network vnet create -n {vnet} -l {loc} -g {rg} --address-prefixes 10.0.0.0/16 --subnet-name {subnet} --subnet-prefixes 10.0.0.0/24")
        self.cmd("network vnet subnet update -n {subnet} -g {rg} --vnet-name {vnet} --disable-private-endpoint-network-policies true")

        # create private endpoint connection
        pl_resources = self.cmd("storage account private-link-resource list --account-name {sa} -g {rg}").get_output_in_json()
        self.kwargs["group_id"] = pl_resources[0]["groupId"]
        self.kwargs["sa_id"] = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()["id"]
        self.kwargs["id1"] = self.cmd("network asg create -n {asg1} -g {rg}").get_output_in_json()["id"]
        self.kwargs["id2"] = self.cmd("network asg create -n {asg2} -g {rg}").get_output_in_json()["id"]
        self.cmd(
            "network private-endpoint create -n {pe} -g {rg} --vnet-name {vnet} --subnet {subnet} --connection-name {connection} --group-id {group_id} --private-connection-resource-id {sa_id} "
            "--asg id={id1} "
            "--asg id={id2}",
            checks=[
                self.check("length(applicationSecurityGroups)", 2),
                self.check("applicationSecurityGroups[0].id", self.kwargs["id1"]),
                self.check("applicationSecurityGroups[1].id", self.kwargs["id2"]),
            ]
        )

        # check application security group operations
        self.cmd(
            "network private-endpoint asg remove -g {rg} --endpoint-name {pe} --asg-id {id2}",
            checks=[
                self.check("length(applicationSecurityGroups)", 1),
                self.check("applicationSecurityGroups[0].id", self.kwargs["id1"]),
            ]
        )
        self.cmd(
            "network private-endpoint asg add -g {rg} --endpoint-name {pe} --asg-id {id2}",
            checks=[
                self.check("length(applicationSecurityGroups)", 2),
                self.check("applicationSecurityGroups[1].id", self.kwargs["id2"]),
            ]
        )
        self.cmd(
            "network private-endpoint asg list -g {rg} --endpoint-name {pe}",
            checks=[
                self.check("length(@)", 2),
                self.check("@[0].id", self.kwargs["id1"]),
                self.check("@[1].id", self.kwargs["id2"]),
            ]
        )

    @ResourceGroupPreparer(name_prefix='fanqiu_cli_test_network_private_endpoints', location='CentralUSEuap')
    @StorageAccountPreparer(name_prefix='saplr', kind='StorageV2')
    def test_network_private_endpoint_private_dns_zone_group(self, resource_group, storage_account):
        from msrestazure.azure_exceptions import CloudError
        self.kwargs.update({
            'sa': storage_account,
            'loc': 'CentralUSEuap',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'zone_name1': 'www.clizone1.com',
            'zone_name2': 'www.clizone2.com',
            'private_dns_zone_group_name': 'clidnsgroup',
            'private_zone_name1': 'clizone1',
            'private_zone_name2': 'clizone2'
        })

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pr = self.cmd('storage account private-link-resource list --account-name {sa} -g {rg}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']

        storage = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()
        self.kwargs['sa_id'] = storage['id']
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {sa_id} '
            '--group-ids blob').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])
        self.kwargs['pe_id'] = private_endpoint['privateLinkServiceConnections'][0]['id']

        # Show the connection at storage account
        storage = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', storage)
        self.assertEqual(len(storage['privateEndpointConnections']), 1)
        self.assertEqual(storage['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
                         'Approved')

        self.kwargs['sa_pec_id'] = storage['privateEndpointConnections'][0]['id']
        self.kwargs['sa_pec_name'] = storage['privateEndpointConnections'][0]['name']

        self.cmd('storage account private-endpoint-connection show --account-name {sa} -g {rg} --name {sa_pec_name}',
                 checks=self.check('id', '{sa_pec_id}'))

        self.cmd('network private-endpoint show -g {rg} -n {pe}', checks=[
            self.check('length(customDnsConfigs)', 1)
        ])
        self.cmd('network private-dns zone create -n {zone_name1} -g {rg}')
        self.cmd('network private-dns zone create -n {zone_name2} -g {rg}')

        self.cmd('network private-endpoint dns-zone-group create --endpoint-name {pe} -g {rg} -n {private_dns_zone_group_name} '
                 '--zone-name {private_zone_name1} --private-dns-zone {zone_name1}',
                 checks=[
                     self.check('name', '{private_dns_zone_group_name}')
                 ])

        self.cmd('network private-endpoint dns-zone-group add --endpoint-name {pe} -g {rg} -n {private_dns_zone_group_name} '
                 '--zone-name {private_zone_name2} --private-dns-zone {zone_name2}',
                 checks=[
                     self.check('length(privateDnsZoneConfigs)', 2)
                 ])

        self.cmd('network private-endpoint dns-zone-group show --endpoint-name {pe} -g {rg} -n {private_dns_zone_group_name}', checks=[
            self.check('length(privateDnsZoneConfigs)', 2)
        ])
        self.cmd('network private-endpoint dns-zone-group list --endpoint-name {pe} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network private-endpoint dns-zone-group remove --endpoint-name {pe} -g {rg} -n {private_dns_zone_group_name} '
                 '--zone-name {private_zone_name2}',
                 checks=[
                     self.check('length(privateDnsZoneConfigs)', 1)
                 ])
        self.cmd('network private-endpoint dns-zone-group show --endpoint-name {pe} -g {rg} -n {private_dns_zone_group_name}', checks=[
            self.check('length(privateDnsZoneConfigs)', 1)
        ])
        self.cmd('network private-endpoint dns-zone-group delete --endpoint-name {pe} -g {rg} -n {private_dns_zone_group_name}')


class NetworkPrivateLinkService(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_private_link_service')
    def test_network_private_link_service(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'sku': 'Standard',
            'vnet': 'vnet1',
            'subnet1': 'subnet1',
            'subnet2': 'subnet2',
            'location': 'centralus',
            'ip': 'pubip1',
            'lks1': 'lks1',
            'lks2': 'lks2',
            'sub1': '00000000-0000-0000-0000-000000000000'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet1} -l {location}')
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --public-ip-address {ip} --sku {sku}')
        self.cmd('network vnet subnet update -g {rg} -n {subnet1} --vnet-name {vnet} --disable-private-link-service-network-policies')
        self.cmd('network vnet subnet create -g {rg} -n {subnet2} --vnet-name {vnet} --address-prefixes 10.0.2.0/24')
        self.cmd('network vnet subnet update -g {rg} -n {subnet2} --vnet-name {vnet} --disable-private-endpoint-network-policies')
        self.cmd('network private-link-service create -g {rg} -n {lks1} --vnet-name {vnet} --subnet {subnet1} --lb-name {lb} --lb-frontend-ip-configs LoadBalancerFrontEnd -l {location}  --enable-proxy-protocol', checks=[
            self.check('type', 'Microsoft.Network/privateLinkServices'),
            self.check('length(ipConfigurations)', 1),
            self.check('length(loadBalancerFrontendIpConfigurations)', 1),
            self.check('enableProxyProtocol', True)
        ])

        self.cmd('network private-link-service update -g {rg} -n {lks1} --visibility {sub1} {sub1} --auto-approval {sub1} {sub1}  --enable-proxy-protocol False', checks=[
            self.check('length(visibility.subscriptions)', 2),
            self.check('length(autoApproval.subscriptions)', 2),
            self.check('enableProxyProtocol', False)
        ])
        self.cmd('network private-link-service list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('@[0].type', 'Microsoft.Network/privateLinkServices')
        ])
        self.cmd('network private-link-service show -g {rg} -n {lks1}', checks=[
            self.check('type', 'Microsoft.Network/privateLinkServices'),
            self.check('length(ipConfigurations)', 1),
            self.check('length(loadBalancerFrontendIpConfigurations)', 1)
        ])

        self.cmd('network private-link-service delete -g {rg} -n {lks1}')

        self.cmd('network vnet subnet update -g {rg} -n {subnet1} --vnet-name {vnet} --disable-private-link-service-network-policies false', checks=[
            self.check('privateLinkServiceNetworkPolicies', 'Enabled')
        ])


class NetworkLoadBalancerWithZone(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_zone')
    def test_network_lb_zone(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'lb2': 'lb4',
            'lb3': 'lb5',
            'zone': '2',
            'location': 'eastus2',
            'ip': 'pubip1',
            'ip2': 'pubip2'
        })

        # LB with public ip
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --public-ip-zone {zone} --public-ip-address {ip}')
        # No zone on LB and its front-ip-config
        self.cmd('network lb show -g {rg} -n {lb}', checks=[
            self.check("frontendIpConfigurations[0].zones", None),
            self.check("zones", None)
        ])
        # Zone on public-ip which LB uses to infer the zone
        self.cmd('network public-ip show -g {rg} -n {ip}', checks=[
            self.check('zones[0]', self.kwargs['zone'])
        ])

        # LB w/o public ip, so called ILB
        self.kwargs['lb'] = 'lb2'
        self.cmd('network lb create -g {rg} -l {location} -n {lb} --frontend-ip-zone {zone} --public-ip-address "" --vnet-name vnet1 --subnet subnet1')
        # Zone on front-ip-config, and still no zone on LB resource
        self.cmd('network lb show -g {rg} -n {lb}', checks=[
            self.check("frontendIpConfigurations[0].zones[0]", self.kwargs['zone']),
            self.check("zones", None)
        ])
        # add a second frontend ip configuration
        self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb} -n LoadBalancerFrontEnd2 -z {zone}  --vnet-name vnet1 --subnet subnet1', checks=[
            self.check("zones", [self.kwargs['zone']])
        ])

        # test for private-ip-address-version
        self.cmd('network lb create -g {rg} -n {lb2} -l westcentralus --sku Standard')
        self.cmd('network public-ip create -n {ip2} -g {rg} -l westcentralus --sku Standard --allocation-method Static --version IPv6')
        self.cmd('network lb frontend-ip create --lb-name {lb2} -n ipv6 -g {rg} --private-ip-address-version IPv6 --public-ip-address {ip2}', checks=[
            self.check('name', 'ipv6'),
            self.check('privateIpAddressVersion', 'IPv6'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('network lb create -g {rg} -n {lb3} --sku Standard -l westcentralus --private-ip-address-version IPv6', checks=[
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAddressVersion', 'IPv6')
        ])

    @ResourceGroupPreparer(name_prefix='test_network_lb_frontend_ip_zone', location='eastus2')
    def test_network_lb_frontend_ip_zone(self, resource_group):
        self.kwargs.update({
            'location': 'eastus2',
        })

        # LB with subnet : internal LB
        self.cmd('network lb create -g {rg} -l {location} -n lb --vnet-name vnet --subnet subnet --sku Standard')
        self.cmd('network lb frontend-ip create -g {rg} --lb-name lb -n LoadBalancerFrontEnd2 -z 1 2 3 --vnet-name vnet --subnet subnet', checks=[
            self.check("length(zones)", 3)
        ])


class NetworkPublicIpWithSku(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_lb_sku')
    def test_network_public_ip_sku(self, resource_group):

        self.kwargs.update({
            'standard_sku': 'Standard',
            'basic_sku': 'Basic',
            'regional_tier': 'Regional',
            'global_tier': 'Global',
            'location': 'eastus2',
            'ip1': 'pubip1',
            'ip2': 'pubip2',
            'ip3': 'pubip3',
            'ip4': 'pubip4'
        })

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip1}')
        self.cmd('network public-ip show -g {rg} -n {ip1}', checks=[
            self.check('sku.name', self.kwargs.get('basic_sku')),
            self.check('sku.tier', self.kwargs.get('regional_tier')),
            self.check('publicIpAllocationMethod', 'Dynamic')
        ])

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip2} --sku {standard_sku} --tags foo=doo')
        self.cmd('network public-ip show -g {rg} -n {ip2}', checks=[
            self.check('sku.name', self.kwargs.get('standard_sku')),
            self.check('sku.tier', self.kwargs.get('regional_tier')),
            self.check('publicIpAllocationMethod', 'Static'),
            self.check('tags.foo', 'doo')
        ])

        self.cmd('network public-ip create -g {rg} -l {location} -n {ip3} --sku {standard_sku} --tier {global_tier}')
        self.cmd('network public-ip show -g {rg} -n {ip3}', checks=[
            self.check('sku.name', self.kwargs.get('standard_sku')),
            self.check('sku.tier', self.kwargs.get('global_tier')),
            self.check('publicIpAllocationMethod', 'Static')
        ])

        from azure.core.exceptions import HttpResponseError
        with self.assertRaisesRegex(HttpResponseError, 'Global publicIP addresses are only supported for standard SKU public IP addresses'):
            self.cmd('network public-ip create -g {rg} -l {location} -n {ip4} --tier {global_tier}')


class NetworkCustomIpPrefix(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_custom_ip_prefix', location='eastus2')
    def test_network_custom_ip_prefix(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'prefix': 'prefix1'
        })

        # Test custom prefix CRUD
        self.cmd('network custom-ip prefix create -g {rg} -n {prefix} --cidr 40.40.40.0/24')
        self.cmd('network custom-ip prefix update -g {rg} -n {prefix} --tags foo=doo')
        # self.cmd('network custom-ip prefix update -g {rg} -n {prefix} --state Commissioning')
        self.cmd('network custom-ip prefix list -g {rg}',
                 checks=self.check('length(@)', 1))
        # Delete operation isn't ready.
        # self.cmd('network custom-ip prefix delete -g {rg} -n {prefix}')
        # self.cmd('network custom-ip prefix list -g {rg}',
        #          checks=self.is_empty())

    @record_only()
    def test_network_custom_ip_prefix_update_state(self):
        self.kwargs.update({
            'rg': 'cli_test_custom_ip_prefix',
            'prefix': 'prefix1'
        })

        self.cmd('network custom-ip prefix show -g {rg} -n {prefix}',
                 checks=self.check('commissionedState', 'Provisioned'))

        self.cmd('network custom-ip prefix update -g {rg} -n {prefix} --state commission',
                 checks=self.check('commissionedState', 'Commissioning'))


class NetworkPublicIpPrefix(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_network_public_ip_prefix', location='eastus2')
    def test_network_public_ip_prefix(self, resource_group):

        self.kwargs.update({
            'prefix': 'prefix1',
            'pip': 'pip1'
        })

        # Test prefix CRUD
        self.cmd('network public-ip prefix create -g {rg} -n {prefix} --length 30',
                 checks=self.check('prefixLength', 30))
        self.cmd('network public-ip prefix update -g {rg} -n {prefix} --tags foo=doo')

        # test prefix show command
        self.cmd('network public-ip prefix show -g {rg} -n {prefix}',
                 checks=self.check('tags.foo', 'doo'))

        self.cmd('network public-ip prefix list -g {rg}',
                 checks=self.check('length(@)', 1))
        self.cmd('network public-ip prefix delete -g {rg} -n {prefix}')
        self.cmd('network public-ip prefix list -g {rg}',
                 checks=self.is_empty())

        # Test public IP create with prefix
        self.cmd('network public-ip prefix create -g {rg} -n {prefix} --length 30')
        self.cmd('network public-ip create -g {rg} -n {pip} --public-ip-prefix {prefix} --sku Standard',
                 checks=self.check("publicIp.publicIpPrefix.id.contains(@, '{prefix}')", True))

        # Test IP address version
        self.kwargs.update({
            'prefix_name_ipv4': 'public_ip_prefix_0',
            'prefix_name_ipv5': 'public_ip_prefix_1',
            'prefix_name_ipv6': 'public_ip_prefix_2'
        })

        # Check the default ip address version value
        self.cmd('network public-ip prefix create -g {rg} -n {prefix_name_ipv4} --length 30', checks=[
            self.check('publicIpAddressVersion', 'IPv4')
        ])

        # Check the creation of public IP prefix with IPv6 address option
        # Note: prefix length for IPv6 is minimal 124 and maximal 127 respectively
        self.cmd('network public-ip prefix create -g {rg} -n {prefix_name_ipv6} --length 127 --version IPv6', checks=[
            self.check('publicIpAddressVersion', 'IPv6')
        ])

        # Check with unsupported IP address version: IPv5
        with self.assertRaisesRegex(SystemExit, '2'):
            self.cmd('network public-ip prefix create -g {rg} -n {prefix_name_ipv6} --length 127 --version IPv5')

    @ResourceGroupPreparer(name_prefix='cli_test_network_public_ip_prefix_zone', location='eastus2')
    def test_network_public_ip_prefix_zone(self, resource_group):
        self.kwargs.update({
            'prefix': 'prefix1',
        })

        # Test prefix with multi zones
        self.cmd('network public-ip prefix create -g {rg} -n {prefix} --length 30 --zone 1 2 3', checks=[
            self.check('prefixLength', 30),
            self.check('length(zones)', 3)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_network_public_ip_prefix_with_ip_address', location='eastus2')
    def test_network_public_ip_prefix_with_ip_address(self, resource_group):
        self.kwargs.update({
            'prefix_name_ipv4': 'public_ip_prefix_0',
            'pip': 'pip1'
        })

        ip_prefix = self.cmd('network public-ip prefix create -g {rg} -n {prefix_name_ipv4} --length 28', checks=[
            self.check('publicIpAddressVersion', 'IPv4')
        ]).get_output_in_json()

        ip_address = '.'.join(ip_prefix['ipPrefix'].split('.')[:3]) + '10'

        # Create public ip with ip address
        self.cmd('network public-ip create -g {rg} -n {pip} --public-ip-prefix {prefix_name_ipv4} --sku Standard --ip-address ' + ip_address,
                 checks=self.check("publicIp.publicIpPrefix.id.contains(@, '{prefix_name_ipv4}')", True))


class NetworkMultiIdsShowScenarioTest(ScenarioTest):
    @live_only()
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
        self.cmd('network application-gateway update -g {rg} -n ag1 --no-wait')
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
        self.cmd('network application-gateway show-backend-health -g {rg} -n ag1')

        self.cmd('network application-gateway stop --resource-group {rg} -n ag1')
        self.cmd('network application-gateway start --resource-group {rg} -n ag1')
        self.cmd('network application-gateway delete --resource-group {rg} -n ag1')
        self.cmd('network application-gateway list --resource-group {rg}', checks=self.check('length(@)', ag_count - 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_basic_with_waf_v2_sku')
    def test_network_app_gateway_with_waf_v2_sku(self, resource_group):
        self.cmd('network public-ip create -g {rg} -n pubip1 --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n ag1 --sku WAF_v2 --public-ip-address pubip1')

        self.cmd('network application-gateway list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?resourceGroup == '{}']) == length(@)".format(resource_group), True)
        ])

        self.cmd('network application-gateway show --resource-group {rg} --name ag1', checks=[
            self.check('type(@)', 'object'),
            self.check('name', 'ag1'),
            self.check('resourceGroup', resource_group),
            self.check('frontendIpConfigurations[0].privateIpAllocationMethod', 'Dynamic')
        ])
        self.cmd('network application-gateway show-backend-health -g {rg} -n ag1 '
                 '--host-name-from-http-settings --path /test --timeout 100 '
                 '--http-settings appGatewayBackendHttpSettings --address-pool appGatewayBackendPool')

    @ResourceGroupPreparer(name_prefix='test_network_appgw_creation_with_public_and_private_ip')
    def test_network_appgw_creation_with_public_and_private_ip(self, resource_group):
        self.kwargs.update({
            "appgw": "applicationGateway",
            "ip": "publicIP",
        })

        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')

        self.cmd("network application-gateway create -g {rg} -n {appgw} "
                 "--sku Standard_v2 "
                 "--enable-private-link "
                 "--private-ip-address 10.0.0.17 "
                 "--public-ip-address {ip}")
        show_data = self.cmd("network application-gateway show -g {rg} -n {appgw}").get_output_in_json()

        self.assertEqual(len(show_data["frontendIpConfigurations"]), 2)

        # Those assertions are not stable, because the order in array frontendIpConfigurations is not fixed
        # self.assertTrue(show_data["frontendIpConfigurations"][0]["publicIpAddress"]["id"].endswith(self.kwargs["ip"]))
        # self.assertTrue(show_data["frontendIpConfigurations"][1]["id"].endswith("appGatewayPrivateFrontendIP"))  # default name
        # self.assertEqual(show_data["frontendIpConfigurations"][1]["privateIpAddress"], "10.0.0.17")
        # self.assertEqual(show_data["frontendIpConfigurations"][1]["privateLinkConfiguration"], None)
        # service buggy, this properties won't be populcated so fast even in Azure CLI 2.12.0
        # self.assertTrue(show_data["frontendIpConfigurations"][1]["privateLinkConfiguration"]["id"].endswith("PrivateLinkDefaultConfiguration"))

        self.cmd("network application-gateway delete -g {rg} -n {appgw}")


class NetworkAppGatewayIndentityScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_identity')
    @KeyVaultPreparer(name_prefix='cli-test-keyvault-', sku='premium')
    def test_network_app_gateway_with_identity(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'gw': 'gateway',
            'one_off_identity': 'id1',
            'access_identity': 'id2',
            'ip': 'ip1',
            'cert': 'MyCertificate'
        })

        # create a managed identity
        self.cmd('identity create -g {rg} -n {one_off_identity}').get_output_in_json()
        access_identity_result = self.cmd('identity create -g {rg} -n {access_identity}').get_output_in_json()
        self.kwargs.update({
            'access_identity_principal': access_identity_result['principalId']
        })

        self.cmd('keyvault set-policy -g {rg} -n {kv} '
                 '--object-id {access_identity_principal} --secret-permissions get list set')

        # create a certificate
        keyvault_cert_policy = self.cmd('az keyvault certificate get-default-policy').get_output_in_json()
        self.kwargs.update({
            'keyvault_cert_policy': keyvault_cert_policy
        })
        self.cmd('keyvault certificate create '
                 '--vault-name {kv} '
                 '--name {cert} '
                 '--policy "{keyvault_cert_policy}"')
        cert_result = self.cmd('keyvault certificate show --vault-name {kv} --name {cert}').get_output_in_json()
        self.kwargs.update({
            'secret_id': cert_result['sid']
        })

        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')

        # create application-gateway with one_off_identity
        self.cmd('network application-gateway create '
                 '-g {rg} -n {gw} '
                 '--sku Standard_v2 --public-ip-address {ip} '
                 '--identity {one_off_identity} ')
        self.cmd('network application-gateway show -g {rg} -n {gw}', checks=[
            self.check('identity.type', 'userAssigned')
        ])

        # remove one_off_identity
        self.cmd('network application-gateway identity remove -g {rg} --gateway-name {gw}', checks=[
            self.check('identity', None)
        ])
        # assign access_identity
        self.cmd('network application-gateway identity assign '
                 '-g {rg} --gateway-name {gw} --identity {access_identity}',
                 checks=[
                     self.check('identity.type', 'userAssigned')
                 ])
        self.cmd('network application-gateway identity show -g {rg} --gateway-name {gw}', checks=[
            self.check('type', 'userAssigned')
        ])

        self.cmd('network application-gateway ssl-cert create '
                 ' -g {rg} --gateway-name {gw} '
                 '--name MySSLCert '
                 '--key-vault-secret-id {secret_id}')

        self.cmd('network application-gateway root-cert create -g {rg} --gateway-name {gw} -n cert1 --keyvault-secret {secret_id}', checks=[
            self.check('trustedRootCertificates[0].keyVaultSecretId', '{secret_id}')
        ])


    @ResourceGroupPreparer(name_prefix='cli_test_ag_cert_name_')
    @KeyVaultPreparer(name_prefix='cli-test-keyvault-', sku='premium')
    def test_network_app_gateway_with_cert_name(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'gw': 'gateway',
            'access_identity': 'id1',
            'ip': 'ip1',
            'cert': 'MyCertificate',
            'ssl_cert_name': 'TestCertName'
        })

        # create a managed identity
        access_identity_result = self.cmd('identity create -g {rg} -n {access_identity}').get_output_in_json()
        self.kwargs.update({
            'access_identity_principal': access_identity_result['principalId']
        })

        self.cmd('keyvault set-policy -g {rg} -n {kv} '
                 '--object-id {access_identity_principal} --secret-permissions get list set')

        # create a certificate
        keyvault_cert_policy = self.cmd('az keyvault certificate get-default-policy').get_output_in_json()
        self.kwargs.update({
            'keyvault_cert_policy': keyvault_cert_policy
        })
        self.cmd('keyvault certificate create '
                 '--vault-name {kv} '
                 '--name {cert} '
                 '--policy "{keyvault_cert_policy}"')
        cert_result = self.cmd('keyvault certificate show --vault-name {kv} --name {cert}').get_output_in_json()
        self.kwargs.update({
            'secret_id': cert_result['sid']
        })

        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')

        # create application-gateway with one_off_identity
        self.cmd('network application-gateway create '
                 '-g {rg} -n {gw} '
                 '--sku Standard_v2 --public-ip-address {ip} '
                 '--identity {access_identity} '
                 '--frontend-port 1000 '
                 '--key-vault-secret-id {secret_id} '
                 '--ssl-certificate-name {ssl_cert_name}', checks=[
            self.check('applicationGateway.sslCertificates[0].name', self.kwargs['ssl_cert_name']),
            self.check('applicationGateway.sslCertificates[0].properties.keyVaultSecretId', self.kwargs['secret_id']),
        ])


class NetworkAppGatewayTrustedClientCertScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_trusted_client_cert')
    def test_network_app_gateway_with_trusted_client_cert(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'gw': 'gateway',
            'ip': 'ip1',
            'cert': os.path.join(TEST_DIR, 'client.cer'),
            'cert1': os.path.join(TEST_DIR, 'client1.cer'),
            'cname': 'cert_name',
            'cname1': 'cert_name1',
        })

        # create an ag with trusted client cert
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {gw} --sku Standard_v2 --public-ip-address {ip} '
                 '--trusted-client-cert name={cname} data="{cert}"',
                 checks=[self.check('length(applicationGateway.trustedClientCertificates)', 1)])

        self.cmd('network application-gateway client-cert add -g {rg} --gateway-name {gw} '
                 '--name {cname1} --data "{cert1}"',
                 checks=[self.check('length(trustedClientCertificates)', 2)])

        self.cmd('network application-gateway client-cert list -g {rg} --gateway-name {gw}',
                 checks=[self.check('length(@)', 2)])

        self.cmd('network application-gateway client-cert update -g {rg} --gateway-name {gw} '
                 '--name {cname1} --data "{cert}"')

        cert = self.cmd('network application-gateway client-cert show -g {rg} --gateway-name {gw} --name {cname}').get_output_in_json()

        self.cmd('network application-gateway client-cert show -g {rg} --gateway-name {gw} --name {cname1}',
                 checks=[self.check('data', cert['data'])])

        self.cmd('network application-gateway client-cert remove -g {rg} --gateway-name {gw} --name {cname1}',
                 checks=[self.check('length(trustedClientCertificates)', 1)])


class NetworkAppGatewaySslProfileScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_ssl_profile')
    def test_network_app_gateway_with_ssl_profile(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'gw': 'gateway',
            'ip': 'ip1',
            'name': 'name',
            'name1': 'name1',
        })

        # create an ag with ssl profile
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {gw} --sku Standard_v2 --public-ip-address {ip} '
                 '--ssl-profile name={name} client-auth-configuration=True min-protocol-version=TLSv1_0 '
                 'cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 policy-type=Custom',
                 checks=[self.check('length(applicationGateway.sslProfiles)', 1)])

        self.cmd('network application-gateway ssl-profile add -g {rg} --gateway-name {gw} --name {name1} '
                 '--client-auth-configuration True --min-protocol-version TLSv1_0 '
                 '--cipher-suites TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 --policy-type Custom',
                 checks=[self.check('length(sslProfiles)', 2)])

        self.cmd('network application-gateway ssl-profile update -g {rg} --gateway-name {gw} --name {name1} '
                 '--client-auth-configuration False',
                 checks=[self.check('sslProfiles[1].clientAuthConfiguration.verifyClientCertIssuerDn', False)])

        self.cmd('network application-gateway ssl-profile show -g {rg} --gateway-name {gw} --name {name1} ',
                 checks=[self.check('clientAuthConfiguration.verifyClientCertIssuerDn', False)])

        self.cmd('network application-gateway ssl-profile list -g {rg} --gateway-name {gw}',
                 checks=[self.check('length(@)', 2)])

        self.cmd('network application-gateway ssl-profile remove -g {rg} --gateway-name {gw} --name {name} ',
                 checks=[self.check('length(sslProfiles)', 1)])


class NetworkAppGatewayZoneScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_zone', location='westus2')
    def test_network_ag_zone(self, resource_group):
        self.kwargs.update({
            'gateway': 'ag1',
            'ip': 'pubip1'
        })

        # for public-ip after '2020-08-01', when set '-z 1 3', actually return 'zones:[1,2,3]'
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard -z 1 3', checks=[
            self.check('length(publicIp.zones)', 3)
        ])
        self.cmd('network application-gateway create -g {rg} -n {gateway} --sku Standard_v2 --min-capacity 2 --max-capacity 4 --zones 1 3 --public-ip-address {ip} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {gateway} --exists')
        self.cmd('network application-gateway show -g {rg} -n {gateway}', checks=[
            self.check('zones[0]', 1)
        ])


class NetworkAppGatewayAuthCertScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_auth_cert')
    def test_network_ag_auth_cert(self, resource_group):
        self.kwargs.update({
            'gateway': 'ag1',
            'cert1': 'cert1',
            'cert1_file': os.path.join(TEST_DIR, 'AuthCert.pfx'),
            'cert2': 'cert2',
            'cert2_file': os.path.join(TEST_DIR, 'AuthCert2.pfx'),
            'cert3': 'cert3',
            'cert3_file': os.path.join(TEST_DIR, 'AuthCert3.pfx'),
            'settings': 'https_settings'
        })
        self.cmd('network application-gateway create -g {rg} -n {gateway} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {gateway} --exists')
        self.cmd('network application-gateway auth-cert create -g {rg} --gateway-name {gateway} -n {cert1} --cert-file "{cert1_file}" --no-wait')
        self.cmd('network application-gateway auth-cert create -g {rg} --gateway-name {gateway} -n {cert2} --cert-file "{cert2_file}" --no-wait')

        self.cmd( 'network application-gateway auth-cert update -g {rg} --gateway-name {gateway} -n {cert1} --cert-file "{cert3_file}" --no-wait')

        # test command of auth-cert list
        self.cmd('network application-gateway auth-cert list -g {rg} --gateway-name {gateway}',
                 checks=self.check('length(@)', 2))

        # test command of auth-cert show
        self.cmd('network application-gateway auth-cert show -g {rg} --gateway-name {gateway} -n {cert1}',
                 checks=self.check('name', 'cert1'))

        # test command of auth-cert delete
        self.cmd('network application-gateway auth-cert delete -g {rg} --gateway-name {gateway} -n {cert1} --no-wait')
        self.cmd('network application-gateway auth-cert list -g {rg} --gateway-name {gateway}',
                 checks=self.check('length(@)', 1))

        self.cmd('network application-gateway auth-cert create -g {rg} --gateway-name {gateway} -n {cert1} --cert-file "{cert1_file}" --no-wait')

        self.cmd('network application-gateway http-settings create -g {rg} --gateway-name {gateway} -n {settings} --auth-certs {cert1} {cert2} --no-wait --port 443 --protocol https')
        self.cmd('network application-gateway http-settings update -g {rg} --gateway-name {gateway} -n {settings} --auth-certs {cert2} {cert1} --no-wait')
        self.cmd('network application-gateway show -g {rg} -n {gateway}',
                 checks=self.check('length(backendHttpSettingsCollection[1].authenticationCertificates)', 2))


class NetworkAppGatewayTrustedRootCertScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_root_cert')
    def test_network_ag_root_cert(self, resource_group):
        self.kwargs.update({
            'gateway': 'ag1',
            'cert1': 'cert1',
            'cert1_file': os.path.join(TEST_DIR, 'test-root-cert.cer'),
            'cert2': 'cert2',
            'cert2_file': os.path.join(TEST_DIR, 'test-root-cert-2.cer'),
            'settings': 'https_settings',
            'ip1': 'myip1'
        })
        self.cmd('network public-ip create -g {rg} -n {ip1} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {gateway} --sku Standard_v2 --public-ip-address {ip1}')
        self.cmd('network application-gateway wait -g {rg} -n {gateway} --exists')
        self.cmd('network application-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert1} --cert-file "{cert1_file}"')
        self.cmd('network application-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert2} --cert-file "{cert2_file}"')

        # test root-cert list
        self.cmd('network application-gateway root-cert list -g {rg} --gateway-name {gateway}',
                 checks=self.check('length(@)', 2))
        # test root-cert show
        self.cmd('network application-gateway root-cert show -g {rg} --gateway-name {gateway} -n {cert1}',
                 checks=self.check('name', 'cert1'))

        # test root-cert delete
        self.cmd('network application-gateway root-cert delete -g {rg} --gateway-name {gateway} -n {cert2} --no-wait')
        self.cmd('network application-gateway root-cert list -g {rg} --gateway-name {gateway}',
                 checks=self.check('length(@)', 1))
        self.cmd('network application-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert2} --cert-file "{cert2_file}" --no-wait')

        self.cmd('network application-gateway http-settings create -g {rg} --gateway-name {gateway} -n {settings} --root-certs {cert1} {cert2} --host-name-from-backend-pool true --no-wait --port 443 --protocol https')
        self.cmd('network application-gateway http-settings update -g {rg} --gateway-name {gateway} -n {settings} --root-certs {cert2} {cert1} --no-wait')
        self.cmd('network application-gateway show -g {rg} -n {gateway}',
                 checks=self.check('length(backendHttpSettingsCollection[1].trustedRootCertificates)', 2))
        self.cmd('network application-gateway http-settings update -g {rg} --gateway-name {gateway} -n {settings} --no-wait')


class NetworkAppGatewayRedirectConfigScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_basic')
    def test_network_app_gateway_redirect_config(self, resource_group):
        self.kwargs.update({
            'gateway': 'ag1',
            'name': 'redirect1',
            'name2': 'redirect2'
        })
        self.cmd('network application-gateway create -g {rg} -n {gateway} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {gateway} --exists')
        self.cmd('network application-gateway redirect-config create --gateway-name {gateway} -g {rg} -n {name} -t permanent --include-query-string --include-path false --target-listener appGatewayHttpListener --no-wait')
        self.cmd('network application-gateway redirect-config show --gateway-name {gateway} -g {rg} -n {name}', checks=[
            self.check('includePath', False),
            self.check('includeQueryString', True),
            self.check('redirectType', 'Permanent')
        ])
        self.cmd('network application-gateway redirect-config update --gateway-name {gateway} -g {rg} -n {name} --include-path --include-query-string false --no-wait')
        self.cmd('network application-gateway redirect-config show --gateway-name {gateway} -g {rg} -n {name}', checks=[
            self.check('includePath', True),
            self.check('includeQueryString', False),
            self.check('redirectType', 'Permanent')
        ])
        # test redirect-config list command
        self.cmd('network application-gateway redirect-config create --gateway-name {gateway} -g {rg} -n {name2} -t permanent --include-query-string --include-path false --target-listener appGatewayHttpListener --no-wait')
        self.cmd('network application-gateway redirect-config list --gateway-name {gateway} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])
        # test redirect-config delete command
        self.cmd('network application-gateway redirect-config delete --gateway-name {gateway} -g {rg} -n {name2}')
        self.cmd('network application-gateway redirect-config list --gateway-name {gateway} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])



class NetworkAppGatewayExistingSubnetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_existing_subnet')
    def test_network_app_gateway_with_existing_subnet(self, resource_group):

        vnet = self.cmd('network vnet create -g {rg} -n vnet2 --subnet-name subnet1').get_output_in_json()
        subnet_id = vnet['newVNet']['subnets'][0]['id']
        self.kwargs['subnet_id'] = subnet_id

        # make sure it fails
        self.cmd('network application-gateway create -g {rg} -n ag2 --subnet {subnet_id} --subnet-address-prefix 10.0.0.0/28 --tags foo=doo', expect_failure=True)
        # now verify it succeeds
        self.cmd('network application-gateway create -g {rg} -n ag2 --subnet {subnet_id} --servers 172.0.0.1 www.mydomain.com', checks=[
            self.check('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            self.check('applicationGateway.frontendIPConfigurations[0].properties.subnet.id', subnet_id)
        ])


class NetworkAppGatewayNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_no_wait')
    def test_network_app_gateway_no_wait(self, resource_group):

        self.kwargs.update({
            'tags': {u'a': u'b', u'c': u'd'}
        })

        self.cmd('network application-gateway create -g {rg} -n ag1 --no-wait --connection-draining-timeout 180', checks=self.is_empty())
        self.cmd('network application-gateway create -g {rg} -n ag2 --no-wait --tags a=b c=d', checks=self.is_empty())
        self.cmd('network application-gateway wait -g {rg} -n ag1 --created --interval 120', checks=self.is_empty())
        self.cmd('network application-gateway wait -g {rg} -n ag2 --created --interval 120', checks=self.is_empty())
        self.cmd('network application-gateway show -g {rg} -n ag1', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('backendHttpSettingsCollection[0].connectionDraining.enabled', True),
            self.check('backendHttpSettingsCollection[0].connectionDraining.drainTimeoutInSec', 180)
        ])
        self.cmd('network application-gateway show -g {rg} -n ag2', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('tags', '{tags}')
        ])
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

        # test ssl-cert list
        self.cmd('network application-gateway ssl-cert list -g {rg} --gateway-name ag3',
                 checks=[self.check('length(@)', 1)])

        # test ssl-cert show
        self.cmd('network application-gateway ssl-cert show -g {rg} --gateway-name ag3 -n ag3SslCert',
                 checks=[self.check('name', 'ag3SslCert')])

        self.kwargs['path'] = os.path.join(TEST_DIR, 'TestCert.pfx')
        self.cmd('network application-gateway ssl-cert create -g {rg} --gateway-name ag3 -n ag3SslCert01 --cert-file "{path}" --cert-password {pass} --no-wait')
        # test ssl-cert delete
        self.cmd('network application-gateway ssl-cert delete -g {rg} --gateway-name ag3 -n ag3SslCert01 --no-wait')
        self.cmd('network application-gateway ssl-cert list -g {rg} --gateway-name ag3', checks=[
            self.check('length(@)', 1)])

        self.cmd('network application-gateway ssl-policy set -g {rg} --gateway-name ag3 --disabled-ssl-protocols TLSv1_0 TLSv1_1 --no-wait')
        self.cmd('network application-gateway ssl-policy show -g {rg} --gateway-name ag3',
                 checks=self.check('disabledSslProtocols.length(@)', 2))

        cipher_suite = 'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256'
        self.kwargs['cipher'] = cipher_suite
        self.cmd('network application-gateway ssl-policy set -g {rg} --gateway-name ag3 --min-protocol-version TLSv1_0 --cipher-suites {cipher} --no-wait')
        self.cmd('network application-gateway ssl-policy show -g {rg} --gateway-name ag3', checks=[
            self.check('cipherSuites.length(@)', 1),
            self.check('minProtocolVersion', 'TLSv1_0'),
            self.check('policyType', 'Custom')
        ])

        policy_name = 'AppGwSslPolicy20150501'
        self.kwargs['policy'] = policy_name
        self.cmd('network application-gateway ssl-policy set -g {rg} --gateway-name ag3 -n {policy} --no-wait')
        self.cmd('network application-gateway ssl-policy show -g {rg} --gateway-name ag3', checks=[
            self.check('policyName', policy_name),
            self.check('policyType', 'Predefined')
        ])
        # test predefined show
        self.cmd('network application-gateway ssl-policy predefined show -n {policy}', checks=[
            self.check('name', policy_name)
        ])

        # test predefined list
        self.cmd('network application-gateway ssl-policy predefined list', checks=[
            self.check('length(@)', 3)])

        # test ssl-policy list-options
        self.cmd('network application-gateway ssl-policy list-options', checks=[
            self.check('length(@)', 10)
        ])

    @ResourceGroupPreparer(name_prefix='test_appgw_with_tcp', location='westus')
    def test_appgw_with_tcp(self, resource_group):
        self.kwargs.update({
            'appgw': 'appgw',
            'appgw_frontend_port': 'testFrontendPort',
            'appgw_settings': 'testSettings',
            'appgw_listener': 'testListener',
            'appgw_address_pool': 'testAddressPool',
            'appgw_routing_rule': 'testRule',
            'appgw_public_ip': 'testPublicIp',
            'appgw_rule_type': 'Basic',
            'priority': 1001,
            'port': 8080
        })

        self.cmd('network public-ip create -g {rg} -n {appgw_public_ip} --sku Standard')

        self.cmd('network application-gateway create -g {rg} -n {appgw} '
                 '--public-ip-address {appgw_public_ip} --sku Standard_v2 '
                 '--priority {priority}')
        show_appgw_data = self.cmd('network application-gateway show -g {rg} -n {appgw}').get_output_in_json()
        print(show_appgw_data)
        frontend_ip = show_appgw_data['frontendIpConfigurations'][0]['name']
        self.kwargs.update({
            'appgw_frontend_ip': frontend_ip
        })

        self.cmd('network application-gateway frontend-port create -g {rg} --gateway-name {appgw} '
                 '-n {appgw_frontend_port} --port {port}')
        self.cmd('network application-gateway listener create -g {rg} --gateway-name {appgw} '
                 '--frontend-port {appgw_frontend_port} -n {appgw_listener} --frontend-ip {appgw_frontend_ip}',
                 checks=(self.check('listeners[0].name', '{appgw_listener}')))
        self.cmd('network application-gateway settings create -g {rg} --gateway-name {appgw} '
                 '--name {appgw_settings} --port {port} ',
                 checks=(self.check('backendSettingsCollection[0].name', '{appgw_settings}')))
        self.cmd(
            'network application-gateway address-pool create -g {rg} --gateway-name {appgw} -n {appgw_address_pool} '
            '--servers 10.0.0.4 10.0.0.5')
        self.cmd('network application-gateway routing-rule create -g {rg} --gateway-name {appgw} '
                 '--name {appgw_routing_rule} --listener {appgw_listener} --rule-type {appgw_rule_type} '
                 '--address-pool {appgw_address_pool} --settings {appgw_settings}',
                 checks=[
                     self.check('routingRules[0].name', '{appgw_routing_rule}')
                 ])

        self.cmd('network application-gateway delete --name {appgw} --resource-group {rg}')

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

    @ResourceGroupPreparer(name_prefix='test_network_ag_http_listener_with_waf_policy')
    def test_network_ag_http_listener_with_waf_policy(self):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway http-listener',
            'name': 'mylistener',
            'waf_1': 'waf_1',
            'waf_2': 'waf_2',
            'waf_3': 'waf_3',
            'listener_2': 'listener_2',
        })

        # prepare 2 WAF policies
        self.cmd('network application-gateway waf-policy create -g {rg} --name {waf_1}')
        self.cmd('network application-gateway waf-policy create -g {rg} --name {waf_2}')
        self.cmd('network application-gateway waf-policy create -g {rg} --name {waf_3}')

        self.cmd('network public-ip create -g {rg} -n ip-1 --sku Standard')

        # sku=WAF_v2 is necessary for updating HTTP listener's WAF configuration
        create_res = self.cmd('network application-gateway create -g {rg} --name {ag} --public-ip-address ip-1 --sku WAF_v2').get_output_in_json()
        self.assertEqual(len(create_res['applicationGateway']['httpListeners']), 1)
        self.assertIsNone(create_res['applicationGateway']['httpListeners'][0].get('firewallPolicy'))

        # update the default HTTP listener's WAF policy
        update_res = self.cmd('network application-gateway http-listener update -g {rg} --gateway-name {ag} --name appGatewayHttpListener --waf-policy {waf_1}').get_output_in_json()
        self.assertTrue(update_res['firewallPolicy']['id'].endswith('waf_1'))

        # create another HTTP listener with WAF policy and update it to another WAF policy
        self.cmd('network application-gateway frontend-port create -g {rg} --gateway-name {ag} --port 9020 --name 9020')
        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} --name {listener_2} --frontend-port 9020 --waf-policy {waf_2}')
        update_res = self.cmd('network application-gateway http-listener update -g {rg} --gateway-name {ag} --name {listener_2} --waf-policy {waf_3}').get_output_in_json()
        self.assertTrue(update_res['firewallPolicy']['id'].endswith('waf_3'))

        self.cmd('network application-gateway show -g {rg} --name {ag}')

    @ResourceGroupPreparer(name_prefix='cli_test_ag_http_listener')
    def test_network_ag_http_listener_with_multi_host_names(self, resource_group):

        self.kwargs.update({
            'ag': 'ag1',
            'res': 'application-gateway http-listener',
            'name': 'mylistener',
            'gateway_ip': 'ip1',
            'port': 'cliport'
        })

        self.cmd('network public-ip create -g {rg} -n {gateway_ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {ag} '
                 '--sku WAF_v2 '
                 '--public-ip-address {gateway_ip} ')
        self.cmd('network application-gateway frontend-port create -g {rg} --gateway-name {ag} -n {port} --port 18080')

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --frontend-port {port} --host-names "*.contoso.com" "www.microsoft.com"')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('length(hostNames)', 2),
            self.check('hostNames[0]', "*.contoso.com"),
            self.check('hostNames[1]', "www.microsoft.com")
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --host-names "*.contoso.com" "www.bing.com"')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('length(hostNames)', 2),
            self.check('hostNames[0]', "*.contoso.com"),
            self.check('hostNames[1]', "www.bing.com")
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

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --affinity-cookie-name mycookie --connection-draining-timeout 60 --cookie-based-affinity --host-name-from-backend-pool --protocol https --timeout 50 --port 70')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('affinityCookieName', 'mycookie'),
            self.check('connectionDraining.drainTimeoutInSec', 60),
            self.check('connectionDraining.enabled', True),
            self.check('cookieBasedAffinity', 'Enabled'),
            self.check('pickHostNameFromBackendAddress', True),
            self.check('port', 70),
            self.check('protocol', 'Https'),
            self.check('requestTimeout', 50)
        ])
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --affinity-cookie-name mycookie2 --connection-draining-timeout 0 --cookie-based-affinity disabled --host-name-from-backend-pool false --protocol http --timeout 40 --port 71')
        self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('affinityCookieName', 'mycookie2'),
            self.check('connectionDraining.drainTimeoutInSec', 1),
            self.check('connectionDraining.enabled', False),
            self.check('cookieBasedAffinity', 'Disabled'),
            self.check('pickHostNameFromBackendAddress', False),
            self.check('port', 71),
            self.check('protocol', 'Http'),
            self.check('requestTimeout', 40)
        ])
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 2))
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_probe')
    def test_network_ag_probe(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'gateway_ip': 'gateway_ip',
            'ag': 'ag1',
            'name': 'myprobe'
        })

        self.cmd('network public-ip create -g {rg} -n {gateway_ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {ag} '
                 '--sku WAF_v2 '
                 '--public-ip-address {gateway_ip} ')

        self.cmd('network application-gateway probe create -g {rg} --gateway-name {ag} -n {name} --no-wait '
                 '--path /test '
                 '--protocol http '
                 '--interval 25 '
                 '--timeout 100 '
                 '--threshold 10 '
                 '--min-servers 2 '
                 '--host www.test.com '
                 '--match-status-codes 200 204 '
                 '--host-name-from-http-settings false '
                 '--port 2048 ')
        self.cmd('network application-gateway probe show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('path', '/test'),
            self.check('protocol', 'Http'),
            self.check('interval', 25),
            self.check('timeout', 100),
            self.check('unhealthyThreshold', 10),
            self.check('minServers', 2),
            self.check('host', 'www.test.com'),
            self.check('length(match.statusCodes)', 2),
            self.check('pickHostNameFromBackendHttpSettings', False),
            self.check('port', 2048)
        ])
        self.cmd('network application-gateway probe update -g {rg} --gateway-name {ag} -n {name} --no-wait '
                 '--path /test2 '
                 '--protocol https '
                 '--interval 26 '
                 '--timeout 101 '
                 '--threshold 11 '
                 '--min-servers 3 '
                 '--host "" '
                 '--match-status-codes 201 '
                 '--host-name-from-http-settings '
                 '--port 4096 ')
        self.cmd('network application-gateway probe show -g {rg} --gateway-name {ag} -n {name}', checks=[
            self.check('path', '/test2'),
            self.check('protocol', 'Https'),
            self.check('interval', 26),
            self.check('timeout', 101),
            self.check('unhealthyThreshold', 11),
            self.check('minServers', 3),
            self.check('host', ''),
            self.check('length(match.statusCodes)', 1),
            self.check('pickHostNameFromBackendHttpSettings', True),
            self.check('port', 4096)
        ])
        self.cmd('network application-gateway probe list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 1))
        self.cmd('network application-gateway probe delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network application-gateway probe list -g {rg} --gateway-name {ag}', checks=self.check('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_ag_rule')
    def test_network_ag_rule(self, resource_group):

        self.kwargs.update({
            'ip': 'pip1',
            'ag': 'ag1',
            'res': 'application-gateway rule',
            'name': 'myrule',
            'name2': 'myrule2',
            'set': 'myruleset'
        })
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {ag} --public-ip-address {ip} --sku Standard_v2 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')

        # Make the default rule has priority.
        # Otherwise, server will raise ApplicationGatewayRequestRoutingRulePartialPriorityDefined
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n rule1 --priority 1')

        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com')
        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener2 --no-wait --frontend-port appGatewayFrontendPort --host-name www.test2.com')

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name} --no-wait --http-listener mylistener --priority 12')
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}').get_output_in_json()
        self.assertTrue(rule['httpListener']['id'].endswith('mylistener'))
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name} --no-wait --http-listener mylistener2 --priority 32')
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name}').get_output_in_json()
        self.assertTrue(rule['httpListener']['id'].endswith('mylistener2'))

        self.cmd('network application-gateway rewrite-rule set create -g {rg} --gateway-name {ag} -n {set}')

        # test rewrite-rule set update command
        self.cmd('network application-gateway rewrite-rule set update -g {rg} --gateway-name {ag} -n {set}')

        self.cmd('network {res} create -g {rg} --gateway-name {ag} -n {name2} --no-wait --rewrite-rule-set {set} --http-listener mylistener --priority 10')
        rule = self.cmd('network {res} show -g {rg} --gateway-name {ag} -n {name2}').get_output_in_json()
        self.kwargs['set_id'] = rule['rewriteRuleSet']['id']
        self.cmd('network {res} update -g {rg} --gateway-name {ag} -n {name2} --rewrite-rule-set {set_id} --priority 21', checks=[
            self.check('rewriteRuleSet.id', '{set_id}')
        ])

        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=[
            self.check('length(@)', 3)
        ])
        self.cmd('network {res} delete -g {rg} --gateway-name {ag} --no-wait -n {name}')
        self.cmd('network {res} list -g {rg} --gateway-name {ag}', checks=[
            self.check('length(@)', 2)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_ag_url_path_map')
    def test_network_ag_url_path_map(self, resource_group):
        self.kwargs.update({
            'ip': 'pip1',
            'ag': 'ag1',
            'name': 'mypathmap',
            'rulename': 'myurlrule',
            'rulename2': 'myurlrule2',
            'pool': 'mypool',
            'set': 'myruleset',
            'settings': 'http_settings',
            'rg': resource_group
        })
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {ag} --public-ip-address {ip} --sku Standard_v2 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')

        self.cmd('network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com')

        self.cmd('network application-gateway rewrite-rule set create -g {rg} --gateway-name {ag} -n {set}')
        self.cmd('network application-gateway address-pool create -g {rg} --gateway-name {ag} -n {pool} --no-wait')
        self.cmd('network application-gateway http-settings create -g {rg} --gateway-name {ag} -n {settings} --port 443 --protocol https')
        self.cmd('network application-gateway url-path-map create -g {rg} --gateway-name {ag} -n {name} --rule-name {rulename} --paths /mypath1/* --address-pool {pool} '
                 '--default-address-pool {pool} --http-settings {settings} --default-http-settings {settings} '
                 '--default-rewrite-rule-set {set} --rewrite-rule-set {set}')

        # test url-path-map list
        self.cmd('network application-gateway url-path-map list -g {rg} --gateway-name {ag}',
                 checks=[self.check('length(@)', 1)])

        # test url-path-map show
        self.cmd('network application-gateway url-path-map show -g {rg} --gateway-name {ag} -n {name}',
                 checks=[self.check('name', 'mypathmap')])

        self.cmd('network application-gateway url-path-map update -g {rg} --gateway-name {ag} -n {name} --default-rewrite-rule-set {set}')
        self.cmd('network application-gateway url-path-map rule create -g {rg} --gateway-name {ag} -n {rulename2} --path-map-name {name} '
                 '--paths /mypath122/* --address-pool {pool} --http-settings {settings} --rewrite-rule-set {set}')

        # test url-path-map rule delete
        self.cmd('network application-gateway url-path-map rule delete -g {rg} --gateway-name {ag} -n {rulename2} --path-map-name {name}')

        # test url-path-map delete
        self.cmd('network application-gateway url-path-map delete -g {rg} --gateway-name {ag} -n {name}')
        self.cmd('network application-gateway url-path-map list -g {rg} --gateway-name {ag}',
                 checks=[self.check('length(@)', 0)])


    @ResourceGroupPreparer(name_prefix='cli_test_ag_url_path_map_edge_case')
    def test_network_ag_url_path_map_edge_case(self, resource_group):
        self.kwargs.update({
            'ip': 'pip1',
            'ag': 'ag1',
            'name': 'mypathmap',
            'rulename': 'myurlrule',
            'rulename2': 'myurlrule2',
            'pool': 'mypool',
            'set': 'myruleset',
            'settings': 'http_settings',
            'redirect_config': 'myconfig',
            'rg': resource_group
        })
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')
        self.cmd(
            'network application-gateway create -g {rg} -n {ag} --public-ip-address {ip} --sku Standard_v2 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')

        self.cmd(
            'network application-gateway http-listener create -g {rg} --gateway-name {ag} -n mylistener --no-wait --frontend-port appGatewayFrontendPort --host-name www.test.com')

        self.cmd('network application-gateway rewrite-rule set create -g {rg} --gateway-name {ag} -n {set}')
        self.cmd('network application-gateway redirect-config create -g {rg} --gateway-name {ag} -n {redirect_config} '
                 '--target-listener mylistener --type Permanent')
        self.cmd('network application-gateway address-pool create -g {rg} --gateway-name {ag} -n {pool} --no-wait')
        self.cmd(
            'network application-gateway http-settings create -g {rg} --gateway-name {ag} -n {settings} --port 443 --protocol https')
        self.cmd(
            'network application-gateway url-path-map create -g {rg} --gateway-name {ag} -n {name} --rule-name {rulename} --paths /mypath1/* '
            '--redirect-config {redirect_config} --default-redirect-config {redirect_config}')
        self.cmd(
            'network application-gateway url-path-map rule create -g {rg} --gateway-name {ag} -n {rulename2} --path-map-name {name} '
            '--paths /mypath122/* --address-pool {pool} --http-settings {settings}')
        with self.assertRaisesRegex(CLIError, "Cannot reference a BackendAddressPool when Redirect Configuration is specified."):
            self.cmd(
                'network application-gateway url-path-map rule create -g {rg} --gateway-name {ag} -n {rulename2} --path-map-name {name} '
                '--paths /mypath122/* --address-pool {pool} --http-settings {settings} --redirect-config {redirect_config}')


class NetworkAppGatewayRewriteRuleset(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_rewrite_rulesets')
    def test_network_app_gateway_rewrite_rulesets(self, resource_group):

        self.kwargs.update({
            'gw': 'gw1',
            'ip': 'pip1',
            'set': 'ruleset1',
            'rule': 'rule1',
            'rule2': 'rule2',
            'rule3': 'rule3',
            'var': 'http_req_Authorization'
        })
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard')
        self.cmd('network application-gateway create -g {rg} -n {gw} --public-ip-address {ip} --sku Standard_v2 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {gw} --exists')

        # create ruleset
        self.cmd('network application-gateway rewrite-rule set create -g {rg} --gateway-name {gw} -n {set} --no-wait')
        self.cmd('network application-gateway rewrite-rule set show -g {rg} --gateway-name {gw} -n {set}')

        # manage rewrite rules
        self.cmd('network application-gateway rewrite-rule create -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule} --sequence 123 --request-headers foo=bar --response-headers cat=hat --no-wait')
        self.cmd('network application-gateway rewrite-rule update -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule} --sequence 321 --request-headers bar=foo --response-headers hat=cat --no-wait')
        self.cmd('network application-gateway rewrite-rule update -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule} --set ruleSequence=321 --remove actionSet.responseHeaderConfigurations 0 --no-wait')
        self.cmd('network application-gateway rewrite-rule show -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule}')
        self.cmd('network application-gateway rewrite-rule list -g {rg} --gateway-name {gw} --rule-set-name {set}')
        self.cmd('network application-gateway rewrite-rule list-request-headers')
        self.cmd('network application-gateway rewrite-rule list-response-headers')

        # manage rewrite rules with url configuration
        self.cmd('network application-gateway rewrite-rule create -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule2} '
                 '--sequence 123 --request-headers foo=bar --response-headers cat=hat '
                 '--modified-path "/def" --modified-query-string "a=b&c=d%20f"',
                 checks=[
                     self.check('actionSet.urlConfiguration.modifiedPath', '/def'),
                     self.check('actionSet.urlConfiguration.modifiedQueryString', 'a=b&c=d%20f'),
                     self.check('actionSet.urlConfiguration.reroute', False)
                 ])
        self.cmd('network application-gateway rewrite-rule update -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule2} '
                 '--sequence 321 --request-headers bar=foo --response-headers hat=cat '
                 '--modified-path "/def2" --modified-query-string "a=b&c=d%20f12" --enable-reroute',
                 checks=[
                     self.check('actionSet.urlConfiguration.modifiedPath', '/def2'),
                     self.check('actionSet.urlConfiguration.modifiedQueryString', 'a=b&c=d%20f12'),
                     self.check('actionSet.urlConfiguration.reroute', True)
                 ])
        self.cmd('network application-gateway rewrite-rule update -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule2} --set ruleSequence=321 --remove actionSet.responseHeaderConfigurations 0 --no-wait')
        self.cmd('network application-gateway rewrite-rule show -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule2}')

        # ISSUE#17373 create rewrite rule without
        self.cmd('network application-gateway rewrite-rule create -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule3} --sequence 123 --modified-path "/" --no-wait')

        # manage rewrite rule conditions
        self.cmd('network application-gateway rewrite-rule condition create -g {rg} --gateway-name {gw} --rule-set-name {set} --rule-name {rule} --variable {var} --pattern "^Bearer" --ignore-case false --negate --no-wait')
        self.cmd('network application-gateway rewrite-rule condition update -g {rg} --gateway-name {gw} --rule-set-name {set} --rule-name {rule} --variable {var} --pattern "^Bearers" --no-wait')
        self.cmd('network application-gateway rewrite-rule condition show -g {rg} --gateway-name {gw} --rule-set-name {set} --rule-name {rule} --variable {var}')
        self.cmd('network application-gateway rewrite-rule condition list -g {rg} --gateway-name {gw} --rule-set-name {set} --rule-name {rule}')
        self.cmd('network application-gateway rewrite-rule condition delete -g {rg} --gateway-name {gw} --rule-set-name {set} --rule-name {rule} --variable {var} --no-wait')
        self.cmd('network application-gateway rewrite-rule condition list -g {rg} --gateway-name {gw} --rule-set-name {set} --rule-name {rule}')
        self.cmd('network application-gateway rewrite-rule condition list-server-variables')

        self.cmd('network application-gateway rewrite-rule delete -g {rg} --gateway-name {gw} --rule-set-name {set} -n {rule} --no-wait')
        self.cmd('network application-gateway rewrite-rule list -g {rg} --gateway-name {gw} --rule-set-name {set}')

        self.cmd('network application-gateway rewrite-rule set delete -g {rg} --gateway-name {gw} -n {set} --no-wait')
        self.cmd('network application-gateway rewrite-rule set list -g {rg} --gateway-name {gw}')


class NetworkAppGatewayPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ag_public_ip')
    def test_network_app_gateway_with_public_ip(self, resource_group):

        self.kwargs['ip'] = 'publicip4'
        self.cmd('network application-gateway create -g {rg} -n test4 --subnet subnet1 --vnet-name vnet4 --vnet-address-prefix 10.0.0.1/16 --subnet-address-prefix 10.0.0.1/28 --public-ip-address {ip}', checks=[
            self.check("applicationGateway.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{ip}')", True),
            self.check('applicationGateway.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic')
        ])


class NetworkAppGatewayWafConfigScenarioTest20170301(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_config')
    def test_network_app_gateway_waf_config(self, resource_group):

        self.kwargs.update({
            'ip': 'pip1',
            'ag': 'ag1'
        })
        self.cmd('network application-gateway create -g {rg} -n {ag} --subnet subnet1 --vnet-name vnet1 --public-ip-address {ip} --sku WAF_Medium --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')
        self.cmd('network application-gateway show -g {rg} -n {ag}', checks=[
            self.check("frontendIpConfigurations[0].publicIpAddress.contains(id, '{ip}')", True),
            self.check('frontendIpConfigurations[0].privateIpAllocationMethod', 'Dynamic')
        ])
        self.cmd('network application-gateway waf-config set -g {rg} --gateway-name {ag} --enabled true --firewall-mode prevention --rule-set-version 2.2.9 --disabled-rule-groups crs_30_http_policy --disabled-rules 981175 981176 --no-wait')
        self.cmd('network application-gateway waf-config show -g {rg} --gateway-name {ag}', checks=[
            self.check('enabled', True),
            self.check('firewallMode', 'Prevention'),
            self.check('length(disabledRuleGroups)', 2),
            self.check('length(disabledRuleGroups[1].rules)', 2)
        ])
        # test list rule sets
        self.cmd('network application-gateway waf-config list-rule-sets --group *', checks=[
            self.check('length(@)', 5)
        ])


class NetworkAppGatewayWafV2ConfigScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_v2_config')
    def test_network_app_gateway_waf_v2_config(self, resource_group):

        self.kwargs.update({
            'ip': 'pip1',
            'ag': 'ag1'
        })
        self.cmd('network public-ip create -g {rg} -n {ip} --sku standard')
        self.cmd('network application-gateway create -g {rg} -n {ag} --subnet subnet1 --vnet-name vnet1 --public-ip-address {ip} --sku WAF_v2 --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists')
        self.cmd('network application-gateway waf-config set -g {rg} --gateway-name ag1 --enabled true --firewall-mode prevention --rule-set-version 3.0 --exclusion RequestHeaderNames StartsWith abc --exclusion RequestArgNames Equals def --no-wait')
        self.cmd('network application-gateway waf-config show -g {rg} --gateway-name ag1', checks=[
            self.check('enabled', True),
            self.check('length(exclusions)', 2)
        ])


class NetworkAppGatewayWafPolicyScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_policy_')
    def test_network_app_gateway_waf_policy_with_application_gateway(self, resource_group):
        self.kwargs.update({
            'waf': 'agp1',
            'custom-rule1': 'rule1',
            'custom-rule2': 'rule2',
            'ip1': 'pip1',
            'ag1': 'ag1',
            'ip2': 'pip2',
            'ag2': 'ag2',
            'rg': resource_group,
            'csr_grp1': 'REQUEST-921-PROTOCOL-ATTACK',
            'csr_grp2': 'REQUEST-913-SCANNER-DETECTION'
        })

        # create a waf policy
        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf}')
        self.cmd('network application-gateway waf-policy update -g {rg} -n {waf} --tags test=best',
                 checks=self.check('tags.test', 'best'))
        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}')
        self.cmd('network application-gateway waf-policy list -g {rg}',
                 checks=self.check('length(@)', 1))

        # test waf-policy delete
        self.cmd('network application-gateway waf-policy delete -g {rg} -n {waf}')
        self.cmd('network application-gateway waf-policy list -g {rg}',
                 checks=[
                     self.check('length(@)', 0)
                 ])
        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf}')

        # add two custom rules of this waf-policy
        self.cmd('network application-gateway waf-policy custom-rule create -g {rg} '
                 '--policy-name {waf} -n {custom-rule1} '
                 '--priority 50 --action log --rule-type MatchRule',
                 checks=self.check('priority', 50))
        self.cmd('network application-gateway waf-policy custom-rule create -g {rg} '
                 '--policy-name {waf} -n {custom-rule2} '
                 '--priority 100 --action log --rule-type MatchRule')

        # test custom-rule list
        self.cmd('network application-gateway waf-policy custom-rule list -g {rg} '
                 '--policy-name {waf}',
                 checks=[
                     self.check('length(@)', 2)
                 ])

        # test match-condition list
        self.cmd('network application-gateway waf-policy custom-rule match-condition list -g {rg} --name {custom-rule1} --policy-name {waf}',
                 checks=[
                     self.check('length(@)', 0)
                 ])

        # update some policy settings of this waf-policy
        self.cmd('network application-gateway waf-policy policy-setting update -g {rg} --policy-name {waf} '
                 '--state Enabled --file-upload-limit-in-mb 64 --mode Prevention')

        # test waf-policy policy-setting list
        self.cmd('network application-gateway waf-policy policy-setting list -g {rg} --policy-name {waf}', checks=[
            self.check('length(@)', 5)
        ])

        # add two managed rule set to the managed rules of this waf-policy
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0',
                 checks=[
                     self.check('managedRules.managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRules.managedRuleSets[0].ruleSetVersion', '3.0')
                 ])
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0 '
                 '--group-name {csr_grp1} --rules 921100 921110')
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0 '
                 '--group-name {csr_grp2} --rules 913100')

        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type Microsoft_BotManagerRuleSet --version 0.1',
                 checks=[
                     self.check('managedRules.managedRuleSets[1].ruleSetType', 'Microsoft_BotManagerRuleSet'),
                     self.check('managedRules.managedRuleSets[1].ruleSetVersion', '0.1')
                 ])

        # add one exclusion rule to the managed rules of this waf-policy
        self.cmd('network application-gateway waf-policy managed-rule exclusion add -g {rg} --policy-name {waf} '
                 '--match-variable "RequestHeaderNames" --selector-match-operator "StartsWith" --selector "Bing"')

        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}', checks=[
            self.check('customRules | length(@)', 2),
            self.check('customRules[0].priority', 50),
            self.check('customRules[1].priority', 100),
            self.check('managedRules.managedRuleSets[0].ruleSetType', 'OWASP'),
            self.check('managedRules.managedRuleSets[0].ruleSetVersion', '3.0'),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 2),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '921100'),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[1].ruleGroupName', self.kwargs['csr_grp2']),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[1].rules[0].ruleId', '913100'),
            self.check('managedRules.managedRuleSets[1].ruleSetType', 'Microsoft_BotManagerRuleSet'),
            self.check('managedRules.managedRuleSets[1].ruleSetVersion', '0.1'),
            self.check('policySettings.fileUploadLimitInMb', 64),
            self.check('policySettings.maxRequestBodySizeInKb', 128),
            self.check('policySettings.mode', 'Prevention'),
            self.check('policySettings.requestBodyCheck', False),
            self.check('policySettings.state', 'Enabled')
        ])

        # prepare two IPs
        self.cmd('network public-ip create -g {rg} -n {ip1} --sku standard')
        self.cmd('network public-ip create -g {rg} -n {ip2} --sku standard')

        # create two application gateways and assign with the same waf-policy
        self.cmd('network application-gateway create -g {rg} -n {ag1} '
                 '--subnet subnet1 --vnet-name vnet1 --public-ip-address {ip1} --sku WAF_v2 --waf-policy {waf}')
        self.cmd('network application-gateway create -g {rg} -n {ag2} '
                 '--subnet subnet2 --vnet-name vnet2 --public-ip-address {ip2} --sku WAF_v2 --waf-policy {waf}')

        self.cmd('network application-gateway show -g {rg} -n {ag1}',
                 checks=self.check("firewallPolicy.contains(id, '{waf}')", True))
        self.cmd('network application-gateway show -g {rg} -n {ag2}',
                 checks=self.check("firewallPolicy.contains(id, '{waf}')", True))

        # test assigned application-gateways
        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}', checks=[
            self.check('applicationGateways | length(@)', 2),
            self.check("contains(applicationGateways[0].id, '{ag1}')", True),
            self.check("contains(applicationGateways[1].id, '{ag2}')", True)
        ])

        # test custom-rule delete
        self.cmd('network application-gateway waf-policy custom-rule delete -g {rg} '
                 '--policy-name {waf} -n {custom-rule2}')
        self.cmd('network application-gateway waf-policy custom-rule list -g {rg} '
                 '--policy-name {waf}',
                 checks=[
                     self.check('length(@)', 1)
                 ])


    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_custom_rule_')
    def test_network_app_gateway_waf_custom_rule(self, resource_group):
        self.kwargs.update({
            'waf': 'agp1',
            'rule': 'rule1',
            'ip': 'pip1',
            'ag': 'ag1',
            'rg': resource_group,
            'custom-rule1':'custom-rule1'
        })

        # create a waf-policy with empty custom rule
        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf}')
        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}', checks=[
            self.check('customRules | length(@)', 0)
        ])

        # create a custom rule
        self.cmd('network application-gateway waf-policy custom-rule create -g {rg} '
                 '--policy-name {waf} -n {rule} '
                 '--priority 50 --action LOG --rule-type MatchRule',
                 checks=[
                     self.check('priority', 50),
                     self.check('ruleType', 'MatchRule'),
                     self.check('action', 'Log'),
                     self.check('matchConditions | length(@)', 0)
                 ])
        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}', checks=[
            self.check('customRules | length(@)', 1)
        ])
        self.cmd('network application-gateway waf-policy custom-rule show -g {rg} '
                 '--policy-name {waf} -n {rule}',
                 checks=[
                     self.check('priority', 50),
                     self.check('ruleType', 'MatchRule'),
                     self.check('action', 'Log'),
                     self.check('matchConditions | length(@)', 0)
                 ])

        # add match condition to the previous created custom rule
        self.cmd('network application-gateway waf-policy custom-rule match-condition add -g {rg} '
                 '--policy-name {waf} -n {rule} '
                 '--match-variables RequestHeaders.value --operator contains --values foo boo --transform lowercase')
        self.cmd('network application-gateway waf-policy custom-rule show -g {rg} '
                 '--policy-name {waf} -n {rule}',
                 checks=[
                     self.check('priority', 50),
                     self.check('ruleType', 'MatchRule'),
                     self.check('action', 'Log'),
                     self.check('matchConditions | length(@)', 1)
                 ])

        # update one of properties
        self.cmd('network application-gateway waf-policy custom-rule update -g {rg} '
                 '--policy-name {waf} -n {rule} '
                 '--priority 75',
                 checks=self.check('priority', 75))

        # add another match condition to the same custom rule
        self.cmd('network application-gateway waf-policy custom-rule match-condition add -g {rg} '
                 '--policy-name {waf} -n {rule} '
                 '--match-variables RequestHeaders.value --operator contains '
                 '--values remove this --transform lowercase')
        self.cmd('network application-gateway waf-policy custom-rule show -g {rg} '
                 '--policy-name {waf} -n {rule}',
                 checks=[
                     self.check('priority', 75),
                     self.check('ruleType', 'MatchRule'),
                     self.check('action', 'Log'),
                     self.check('matchConditions | length(@)', 2)
                 ])

        # remove one of match condition of custom rule
        self.cmd('network application-gateway waf-policy custom-rule match-condition remove -g {rg} '
                 '--policy-name {waf} -n {rule} '
                 '--index 0')
        self.cmd('network application-gateway waf-policy custom-rule show -g {rg} '
                 '--policy-name {waf} -n {rule}',
                 checks=[
                     self.check('priority', 75),
                     self.check('ruleType', 'MatchRule'),
                     self.check('action', 'Log'),
                     self.check('matchConditions | length(@)', 1)
                 ])


    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_policy_setting_')
    def test_network_app_gateway_waf_policy_setting(self, resource_group):
        self.kwargs.update({
            'waf': 'agp1',
            'ag': 'ag1',
            'rg': resource_group,
        })

        # check default policy setting values
        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf}', checks=[
            self.check('policySettings.fileUploadLimitInMb', 100),
            self.check('policySettings.maxRequestBodySizeInKb', 128),
            self.check('policySettings.mode', 'Detection'),
            self.check('policySettings.requestBodyCheck', True),
            self.check('policySettings.state', 'Disabled')
        ])

        # randomly update some properties
        self.cmd('network application-gateway waf-policy policy-setting update -g {rg} --policy-name {waf} '
                 '--state Enabled --file-upload-limit-in-mb 64 --mode Prevention',
                 checks=[
                     self.check('policySettings.fileUploadLimitInMb', 64),
                     self.check('policySettings.maxRequestBodySizeInKb', 128),
                     self.check('policySettings.mode', 'Prevention'),
                     self.check('policySettings.requestBodyCheck', False),
                     self.check('policySettings.state', 'Enabled')
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_policy_managed_rules_')
    def test_network_app_gateway_waf_policy_managed_rules(self, resource_group):
        self.kwargs.update({
            'waf': 'agp1',
            'ip': 'pip1',
            'ag': 'ag1',
            'rg': resource_group,
            'csr_grp1': 'REQUEST-921-PROTOCOL-ATTACK',
            'csr_grp2': 'REQUEST-913-SCANNER-DETECTION'
        })
        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf}')

        # case 1: Initialize(add) managed rule set
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0 '
                 '--group-name {csr_grp1} --rules 921100 921110')
        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}', checks=[
            self.check('managedRules.managedRuleSets[0].ruleSetType', 'OWASP'),
            self.check('managedRules.managedRuleSets[0].ruleSetVersion', '3.0'),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 2),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '921100')
        ])

        # case 2: Append(add) another managed rule set to same rule group
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0 '
                 '--group-name {csr_grp1} --rules 921150')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.0'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 3),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[2].ruleId', '921150')
                 ])

        # case 3: Add another managed rule set of different rule group
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0 '
                 '--group-name {csr_grp2} --rules 913100')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.0'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[1].rules | length(@)', 1),
                     self.check('managedRuleSets[0].ruleGroupOverrides[1].ruleGroupName', self.kwargs['csr_grp2']),
                     self.check('managedRuleSets[0].ruleGroupOverrides[1].rules[0].ruleId', '913100')
                 ])

        # case 4: override(update) existing managed rule set
        self.cmd('network application-gateway waf-policy managed-rule rule-set update -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.0 '
                 '--group-name {csr_grp1} --rules 921100 921150')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.0'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 2),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '921100'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[1].ruleId', '921150'),
                 ])

        # case 5: clear manage rule set by group {csr_grp1} and only {csr_grp2} left
        self.cmd('network application-gateway waf-policy managed-rule rule-set remove -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name {csr_grp1} ')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}', checks=[
            self.check('managedRuleSets[0].ruleGroupOverrides | length(@)', 1),
            self.check('managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 1),
            self.check('managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp2']),
            self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '913100'),
        ])

        # case 6: change managed rules of OWASP from 3.1 to 3.0
        self.cmd('network application-gateway waf-policy managed-rule rule-set update -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1')

        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.1'),
                     self.check('managedRuleSets[0].ruleGroupOverrides | length(@)', 0)
                 ])

        # case 7: override existing rules with one rule for OWASP 3.1
        self.cmd('network application-gateway waf-policy managed-rule rule-set update -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name REQUEST-911-METHOD-ENFORCEMENT '
                 '--rules 911100')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}', checks=[
            self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
            self.check('managedRuleSets[0].ruleSetVersion', '3.1'),
            self.check('managedRuleSets[0].ruleGroupOverrides | length(@)', 1),
            self.check('managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 1),
            self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '911100')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_policy_managed_rules_')
    def test_network_app_gateway_waf_policy_with_version_and_type(self, resource_group):
        self.kwargs.update({
            'waf': 'agp1',
            'ip': 'pip1',
            'ag': 'ag1',
            'rg': resource_group,
            'csr_grp1': 'REQUEST-921-PROTOCOL-ATTACK',
            'csr_grp2': 'REQUEST-913-SCANNER-DETECTION'
        })
        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf} --version 3.1 --type OWASP')

        # case 1: Initialize(add) managed rule set
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name {csr_grp1} --rules 921120 921110')
        self.cmd('network application-gateway waf-policy show -g {rg} -n {waf}', checks=[
            self.check('managedRules.managedRuleSets[0].ruleSetType', 'OWASP'),
            self.check('managedRules.managedRuleSets[0].ruleSetVersion', '3.1'),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 2),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
            self.check('managedRules.managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '921120')
        ])

        # case 2: Append(add) another managed rule set to same rule group
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name {csr_grp1} --rules 921150')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.1'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 3),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[2].ruleId', '921150')
                 ])

        # # case 3: Add another managed rule set of different rule group
        self.cmd('network application-gateway waf-policy managed-rule rule-set add -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name {csr_grp2} --rules 913100')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.1'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[1].rules | length(@)', 1),
                     self.check('managedRuleSets[0].ruleGroupOverrides[1].ruleGroupName', self.kwargs['csr_grp2']),
                     self.check('managedRuleSets[0].ruleGroupOverrides[1].rules[0].ruleId', '913100')
                 ])

        # case 4: override(update) existing managed rule set
        self.cmd('network application-gateway waf-policy managed-rule rule-set update -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name {csr_grp1} --rules 921130 921140')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.1'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules | length(@)', 2),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp1']),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[0].ruleId', '921130'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].rules[1].ruleId', '921140')
                 ])

        # # case 5: clear manage rule set by group {csr_grp1}
        self.cmd('network application-gateway waf-policy managed-rule rule-set remove -g {rg} --policy-name {waf} '
                 '--type OWASP --version 3.1 '
                 '--group-name {csr_grp1} ')
        self.cmd('network application-gateway waf-policy managed-rule rule-set list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('managedRuleSets[0].ruleSetType', 'OWASP'),
                     self.check('managedRuleSets[0].ruleSetVersion', '3.1'),
                     self.check('managedRuleSets[0].ruleGroupOverrides[0].ruleGroupName', self.kwargs['csr_grp2'])
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_app_gateway_waf_policy_managed_rules_exclusion')
    def test_network_app_gateway_waf_policy_managed_rules_exclusions(self, resource_group):
        self.kwargs.update({
            'waf': 'agp1',
            'ip': 'pip1',
            'ag': 'ag1',
            'rg': resource_group
        })

        self.cmd('network application-gateway waf-policy create -g {rg} -n {waf}')

        # add one exclusion rule
        self.cmd('network application-gateway waf-policy managed-rule exclusion add -g {rg} --policy-name {waf} '
                 '--match-variable "RequestHeaderNames" --selector-match-operator "StartsWith" --selector "Bing"')
        self.cmd('network application-gateway waf-policy managed-rule exclusion list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('exclusions | length(@)', 1)
                 ])

        # add another exclusion rule
        self.cmd('network application-gateway waf-policy managed-rule exclusion add -g {rg} --policy-name {waf} '
                 '--match-variable "RequestHeaderNames" --selector-match-operator "Contains" --selector "Azure"')
        self.cmd('network application-gateway waf-policy managed-rule exclusion list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('exclusions | length(@)', 2)
                 ])

        # clear all exclusion rules
        self.cmd('network application-gateway waf-policy managed-rule exclusion remove  -g {rg} --policy-name {waf} ')
        self.cmd('network application-gateway waf-policy managed-rule exclusion list -g {rg} --policy-name {waf}',
                 checks=[
                     self.check('exclusions | length(@)', 0)
                 ])

    @ResourceGroupPreparer(name_prefix="cli_test_app_gateway_waf_policy_exclusion_rule_set_")
    def test_network_app_gateway_waf_policy_exclusion_rule_set(self, resource_group):
        self.kwargs.update({
            "waf": "agp",
            "rule_group1": "REQUEST-921-PROTOCOL-ATTACK",
            "rule_group2": "REQUEST-931-APPLICATION-ATTACK-RFI",
        })
        # create a waf-policy
        self.cmd("network application-gateway waf-policy create -g {rg} -n {waf}")
        # add one rule group to exclusion
        self.cmd(
            "network application-gateway waf-policy managed-rule exclusion rule-set add -g {rg} --policy-name {waf} \
            --match-variable RequestHeaderNames --match-operator StartsWith --selector Bing \
            --type OWASP --version 3.2 \
            --group-name {rule_group1} --rule-ids 921140 921150",
            checks=[
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups[0].ruleGroupName", self.kwargs["rule_group1"]),
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups[0].rules | length(@)", 2),
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups[0].rules[0].ruleId", "921140"),
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups[0].rules[1].ruleId", "921150"),
            ]
        )
        # add another rule group to exclusion
        self.cmd(
            "network application-gateway waf-policy managed-rule exclusion rule-set add -g {rg} --policy-name {waf} \
            --match-variable RequestHeaderNames --match-operator StartsWith --selector Bing \
            --type OWASP --version 3.2 \
            --group-name {rule_group2} --rule-ids 931100",
            checks=[
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups | length(@)", 2),
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups[1].ruleGroupName", self.kwargs["rule_group2"]),
                self.check("managedRules.exclusions[0].exclusionManagedRuleSets[0].ruleGroups[1].rules[0].ruleId", "931100"),
            ]
        )
        # remove the first rule group
        self.cmd(
            "network application-gateway waf-policy managed-rule exclusion rule-set remove -g {rg} --policy-name {waf} \
            --match-variable RequestHeaderNames --match-operator StartsWith --selector Bing \
            --type OWASP --version 3.2 --group-name {rule_group1}"
        )
        self.cmd(
            "network application-gateway waf-policy managed-rule exclusion rule-set list -g {rg} --policy-name {waf}",
            checks=[
                self.check("exclusions[0].exclusionManagedRuleSets[0].ruleGroups | length(@)", 1),
                self.check("exclusions[0].exclusionManagedRuleSets[0].ruleGroups[0].ruleGroupName", self.kwargs["rule_group2"]),
                self.check("exclusions[0].exclusionManagedRuleSets[0].ruleGroups[0].rules[0].ruleId", "931100"),
            ]
        )


class NetworkDdosProtectionScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ddos_protection')
    def test_network_ddos_protection_plan(self, resource_group):

        self.kwargs.update({
            'vnet1': 'vnet1',
            'vnet2': 'vnet2',
            'ddos': 'ddos1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet1}')
        self.kwargs['vnet2_id'] = self.cmd('network vnet create -g {rg} -n {vnet2}').get_output_in_json()['newVNet']['id']
        # can be attached through DDoS create
        self.kwargs['ddos_id'] = self.cmd('network ddos-protection create -g {rg} -n {ddos} --vnets {vnet1} {vnet2_id} --tags foo=doo').get_output_in_json()['id']
        self.cmd('network ddos-protection show -g {rg} -n {ddos}')

        # can be detached through VNet update
        self.cmd('network vnet update -g {rg} -n {vnet1} --ddos-protection-plan ""')
        self.cmd('network vnet update -g {rg} -n {vnet2} --ddos-protection-plan ""')
        self.cmd('network ddos-protection show -g {rg} -n {ddos}')

        # can be attached through VNet update
        self.cmd('network vnet update -g {rg} -n {vnet1} --ddos-protection-plan {ddos}')
        self.cmd('network vnet update -g {rg} -n {vnet2} --ddos-protection-plan {ddos_id}')
        self.cmd('network ddos-protection show -g {rg} -n {ddos}')

        # can be detached through DDoS update
        self.cmd('network ddos-protection update -g {rg} -n {ddos} --tags doo=foo --vnets ""')
        self.cmd('network ddos-protection show -g {rg} -n {ddos}')

        # can be attached through DDoS update
        self.cmd('network ddos-protection update -g {rg} -n {ddos} --vnets {vnet2_id} --tags foo=boo')
        self.cmd('network ddos-protection show -g {rg} -n {ddos}')

        self.cmd('network ddos-protection list -g {rg}')
        with self.assertRaises(Exception):
            self.cmd('network ddos-protection delete -g {rg} -n {ddos}')

        # remove all vnets and retry
        self.cmd('network ddos-protection update -g {rg} -n {ddos} --vnets ""')
        self.cmd('network ddos-protection delete -g {rg} -n {ddos}')


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
        self.cmd('network public-ip update -g {rg} -n {ip2} --allocation-method static --dns-name wowza2 --idle-timeout 10 --tags foo=doo', checks=[
            self.check('publicIpAllocationMethod', 'Static'),
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
        self.cmd('network public-ip create -g {rg} -n ip --sku Standard -z 1 2 3', checks=[
            self.check('length(publicIp.zones)', 3)
        ])


class NetworkZonedPublicIpScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_zoned_public_ip')
    def test_network_zoned_public_ip(self, resource_group):
        self.kwargs['ip'] = 'pubip'
        self.cmd('network public-ip create -g {rg} -n {ip} -l centralus -z 2',
                 checks=self.check('publicIp.zones[0]', '2'))

        table_output = self.cmd('network public-ip show -g {rg} -n {ip} -otable').output
        self.assertEqual(table_output.splitlines()[2].split(), ['pubip', resource_group, 'centralus', '2', 'IPv4', 'Dynamic', '4', 'Succeeded'])


class NetworkRouteFilterScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_network_route_filter')
    def test_network_route_filter(self, resource_group):
        self.kwargs['filter'] = 'filter1'
        self.kwargs['rg'] = resource_group
        self.cmd('network route-filter create -g {rg} -n {filter} --tags foo=doo')
        self.cmd('network route-filter update -g {rg} -n {filter}')
        self.cmd('network route-filter show -g {rg} -n {filter}')
        self.cmd('network route-filter list -g {rg}')

        # temporalily disable this test
        # self.cmd('network route-filter rule list-service-communities')
        self.cmd('network route-filter rule create -g {rg} --filter-name {filter} -n rule1 --communities 12076:5040 12076:5030 --access allow')
        self.cmd('network route-filter rule update -g {rg} --filter-name {filter} -n rule1 --set access=Deny')
        self.cmd('network route-filter rule show -g {rg} --filter-name {filter} -n rule1')
        self.cmd('network route-filter rule list -g {rg} --filter-name {filter}')
        self.cmd('network route-filter rule delete -g {rg} --filter-name {filter} -n rule1')

        self.cmd('network route-filter delete -g {rg} -n {filter}')


class NetworkExpressRouteScenarioTest(ScenarioTest):

    def _test_express_route_peering(self):

        def _create_peering(peering, peer_asn, vlan, primary_prefix, secondary_prefix):
            self.kwargs.update({
                'peering': peering,
                'asn': peer_asn,
                'vlan': vlan,
                'pri_prefix': primary_prefix,
                'sec_prefix': secondary_prefix
            })
            self.cmd('network express-route peering create -g {rg} --circuit-name {er} --peering-type {peering} --peer-asn {asn} --vlan-id {vlan} --primary-peer-subnet {pri_prefix} --secondary-peer-subnet {sec_prefix}')

        # create private peerings
        _create_peering('AzurePrivatePeering', 10001, 101, '102.0.0.0/30', '103.0.0.0/30')

        self.cmd('network express-route peering create -g {rg} --circuit-name {er} --peering-type MicrosoftPeering --peer-asn 10002 --vlan-id 103 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30 --advertised-public-prefixes 104.0.0.0/30 --customer-asn 10000 --routing-registry-name level3')
        self.cmd('network express-route peering show -g {rg} --circuit-name {er} -n MicrosoftPeering', checks=[
            self.check('microsoftPeeringConfig.advertisedPublicPrefixes[0]', '104.0.0.0/30'),
            self.check('microsoftPeeringConfig.customerAsn', 10000),
            self.check('microsoftPeeringConfig.routingRegistryName', 'LEVEL3')
        ])

        self.cmd('network express-route peering delete -g {rg} --circuit-name {er} -n MicrosoftPeering')

        self.cmd('network express-route peering list --resource-group {rg} --circuit-name {er}',
                 checks=self.check('length(@)', 1))

        self.cmd('network express-route peering update -g {rg} --circuit-name {er} -n AzurePrivatePeering --set vlanId=200',
                 checks=self.check('vlanId', 200))

    def _test_express_route_auth(self):

        self.cmd('network express-route auth create -g {rg} --circuit-name {er} -n auth1',
                 checks=self.check('authorizationUseStatus', 'Available'))

        self.cmd('network express-route auth list --resource-group {rg} --circuit-name {er}',
                 checks=self.check('length(@)', 1))

        self.cmd('network express-route auth show -g {rg} --circuit-name {er} -n auth1',
                 checks=self.check('authorizationUseStatus', 'Available'))

        self.cmd('network express-route auth delete -g {rg} --circuit-name {er} -n auth1')

        self.cmd('network express-route auth list --resource-group {rg} --circuit-name {er}', checks=self.is_empty())

    @record_only()  # record_only as the express route is extremely expensive, contact service team for an available ER
    @ResourceGroupPreparer(name_prefix='cli_test_express_route')
    def test_network_express_route(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'er': 'circuit1',
            'rt': 'Microsoft.Network/expressRouteCircuits'
        }

        self.cmd('network express-route list-service-providers', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == 'Microsoft.Network/expressRouteServiceProviders']) == length(@)", True)
        ])

        # Premium SKU required to create MicrosoftPeering settings
        self.cmd('network express-route create -g {rg} -n {er} --bandwidth 50 --provider "Ibiza Test Provider" --peering-location Area51 --sku-tier Premium --tags foo=doo')
        self.cmd('network express-route list', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True)
        ])
        self.cmd('network express-route list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
        self.cmd('network express-route show --resource-group {rg} --name {er}', checks=[
            self.check('type(@)', 'object'),
            self.check('type', '{rt}'),
            self.check('name', '{er}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags.foo', 'doo')
        ])
        self.cmd('network express-route get-stats --resource-group {rg} --name {er}',
                 checks=self.check('type(@)', 'object'))

        self.cmd('network express-route update -g {rg} -n {er} --set tags.test=Test', checks=[
            self.check('tags.test', 'Test')
        ])

        self.cmd('network express-route update -g {rg} -n {er} --tags foo=boo',
                 checks=self.check('tags.foo', 'boo'))

        self._test_express_route_auth()

        self._test_express_route_peering()

        # because the circuit isn't actually provisioned, these commands will not return anything useful
        # so we will just verify that the command makes it through the SDK without error.
        self.cmd('network express-route list-arp-tables --resource-group {rg} --name {er} --peering-name azureprivatepeering --path primary')
        self.cmd('network express-route list-route-tables --resource-group {rg} --name {er} --peering-name azureprivatepeering --path primary')
        self.cmd('network express-route list-route-tables-summary --resource-group {rg} --name {er} --peering-name azureprivatepeering --path primary')

        self.cmd('network express-route delete --resource-group {rg} --name {er}')
        # Expecting no results as we just deleted the only express route in the resource group
        self.cmd('network express-route list --resource-group {rg}', checks=self.is_empty())

        with self.assertRaisesRegex(CLIError, 'Please provide a complete resource ID'):
            self.cmd('network express-route gateway connection show --ids /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.Network/expressRouteGateways/aaa')

    @unittest.skip('Test is wrong, please fix. rg not found')
    @ResourceGroupPreparer(name_prefix='cli_test_express_route')
    def test_network_express_route_connection_routing_configuration(self, resource_group):
        self.kwargs = {
            'rg': 'dedharrtv3final',
            'gw': '16297a6ff5314c0f8d0eb580aa7861b3-eastus-er-gw',
            'connection': 'yuerconnection',
            'peering': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dedharrtv3final/providers/Microsoft.Network/expressRouteCircuits/clicktfinal/peerings/AzurePrivatePeering',
            'route_table1': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dedharrtv3final/providers/Microsoft.Network/virtualHubs/blhub/hubRouteTables/routetable1',
            'route_table2': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dedharrtv3final/providers/Microsoft.Network/virtualHubs/blhub/hubRouteTables/routetable2'
        }

        self.cmd('network express-route gateway connection update '
                 '-n {connection} '
                 '-g {rg} '
                 '--gateway-name {gw} '
                 '--peering {peering} '
                 '--associated-route-table {route_table1} '
                 '--propagated-route-tables {route_table1} {route_table2} '
                 '--labels label1 label2',
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('name', self.kwargs['connection']),
                     self.check('routingConfiguration.associatedRouteTable.id', self.kwargs['route_table1']),
                     self.check('length(routingConfiguration.propagatedRouteTables.ids)', 2),
                     self.check('routingConfiguration.propagatedRouteTables.ids[0].id', self.kwargs['route_table1']),
                     self.check('routingConfiguration.propagatedRouteTables.ids[1].id', self.kwargs['route_table2']),
                     self.check('length(routingConfiguration.propagatedRouteTables.labels)', 2),
                     self.check('routingConfiguration.propagatedRouteTables.labels[0]', 'label1'),
                     self.check('routingConfiguration.propagatedRouteTables.labels[1]', 'label2')])

        self.cmd('network express-route gateway connection show -n {connection} -g {rg} --gateway-name {gw}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['connection']),
            self.check('routingConfiguration.associatedRouteTable.id', self.kwargs['route_table1']),
            self.check('length(routingConfiguration.propagatedRouteTables.ids)', 2),
            self.check('routingConfiguration.propagatedRouteTables.ids[0].id', self.kwargs['route_table1']),
            self.check('routingConfiguration.propagatedRouteTables.ids[1].id', self.kwargs['route_table2']),
            self.check('length(routingConfiguration.propagatedRouteTables.labels)', 2),
            self.check('routingConfiguration.propagatedRouteTables.labels[0]', 'label1'),
            self.check('routingConfiguration.propagatedRouteTables.labels[1]', 'label2')
        ])


class NetworkExpressRoutePortScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[
            ExpressRoutePortLOAContentReplacer()
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_express_route_port', location='eastus')
    @KeyVaultPreparer(name_prefix='test-er-port-kv', location='eastus')
    def test_network_express_route_port(self, resource_group, key_vault):
        self.kwargs.update({
            'rg': resource_group,
            'location': 'eastus',
            'name': 'expressRouteTest',
            'peeringRG': 'Equinix-Ashburn-DC2',
            'encapsulation': 'QinQ',
            'bandwidth': '10 Gbps',
            'cipher': 'GcmAes128',
            'kv': key_vault,
            'CAK_name': 'CAK',
            'CAK_value': 'b4355b9ccaf727d2ba7744ee991ce00e',
            'CKN_name': 'CKN',
            'CKN_value': '93e9ce8469eff0536784fc4ad253b5a6',
        })
        self.kwargs['CAK_id'] = self.cmd('keyvault secret set --name {CAK_name} --vault-name {kv} --value {CAK_value}').get_output_in_json()['id']
        self.kwargs['CKN_id'] = self.cmd('keyvault secret set --name {CKN_name} --vault-name {kv} --value {CKN_value}').get_output_in_json()['id']
        identity = self.cmd('identity create -g {rg} -n {name}').get_output_in_json()
        self.cmd('keyvault set-policy -n {kv} --secret-permissions get --object-id ' + identity['principalId'])

        self.cmd('network express-route port location list')

        self.cmd('network express-route port location show -l {peeringRG}', checks=[
            self.check('name', self.kwargs['peeringRG'])
        ])

        self.cmd('network express-route port create -g {rg} -n {name} --location {location} --peering-location {peeringRG} --encapsulation {encapsulation} --bandwidth {bandwidth}', checks=[
            self.check('name', self.kwargs['name']),
            self.check('length(links)', 2),
        ])
        self.cmd('network express-route port list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network express-route port show -g {rg} -n {name}')

        self.cmd('network express-route port identity assign -g {rg} -n {name} --identity ' + identity['id'])

        self.cmd('network express-route port identity show -g {rg} -n {name}')

        self.cmd('network express-route port link list -g {rg} --port-name {name}', checks=[
            self.check('length(@)', 2)
        ])
        self.cmd('network express-route port link show -g {rg} --port-name {name} -n link1', checks=[
            self.check('name', 'link1')
        ])

        self.cmd('network express-route port link update -g {rg} --port-name {name} -n link1 '
                 '--macsec-ckn-secret-identifier {CKN_id} --macsec-cak-secret-identifier {CAK_id} '
                 '--macsec-cipher {cipher} --admin-state', checks=[
            self.check('adminState', 'Enabled'),
            self.check('macSecConfig.cakSecretIdentifier', self.kwargs['CAK_id']),
            self.check('macSecConfig.cknSecretIdentifier', self.kwargs['CKN_id']),
            self.check('macSecConfig.cipher', self.kwargs['cipher']),
        ])

        self.cmd('network express-route port generate-loa --customer-name MyCustomer -g {rg} --name {name} -f loa1')


class NetworkExpressRouteIPv6PeeringScenarioTest(ScenarioTest):

    @record_only()  # record_only as the express route is extremely expensive, contact service team for an available ER
    @ResourceGroupPreparer(name_prefix='cli_test_express_route_ipv6_peering')
    def test_network_express_route_ipv6_peering(self, resource_group):

        self.kwargs['er'] = 'circuit1'

        # Premium SKU required to create MicrosoftPeering settings
        self.cmd('network express-route create -g {rg} -n {er} --bandwidth 50 --provider "Ibiza Test Provider" --peering-location Area51 --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er} --peering-type MicrosoftPeering --peer-asn 10002 --vlan-id 103 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30 --advertised-public-prefixes 104.0.0.0/30 --customer-asn 10000 --routing-registry-name level3')
        self.cmd('network express-route peering update -g {rg} --circuit-name {er} -n MicrosoftPeering --ip-version ipv6 --primary-peer-subnet 2001:db00::/126 --secondary-peer-subnet 2002:db00::/126 --advertised-public-prefixes 2001:db00::/126 --customer-asn 100001 --routing-registry-name level3')
        self.cmd('network express-route peering show -g {rg} --circuit-name {er} -n MicrosoftPeering', checks=[
            self.check('microsoftPeeringConfig.advertisedPublicPrefixes[0]', '104.0.0.0/30'),
            self.check('microsoftPeeringConfig.customerAsn', 10000),
            self.check('microsoftPeeringConfig.routingRegistryName', 'LEVEL3'),
            self.check('ipv6PeeringConfig.microsoftPeeringConfig.advertisedPublicPrefixes[0]', '2001:db00::/126'),
            self.check('ipv6PeeringConfig.microsoftPeeringConfig.customerAsn', 100001),
            self.check('ipv6PeeringConfig.state', 'Enabled')
        ])
        self.cmd('network express-route peering get-stats -g {rg} --circuit-name {er} -n MicrosoftPeering', checks=[
            self.check('type(@)', 'object'),
        ])

    @record_only()  # record_only as the express route is extremely expensive, contact service team for an available ER
    @ResourceGroupPreparer(name_prefix='cli_test_express_route_ipv6_peering2', location='eastus')
    def test_network_express_route_ipv6_peering2(self, resource_group):
        self.kwargs['er'] = 'test_circuit'
        # create with ipv6
        self.cmd('network express-route create -g {rg} -n {er} --bandwidth 50 --provider "Ibiza Test Provider" '
                 '--peering-location Area51 --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er} --peering-type AzurePrivatePeering '
                 '--peer-asn 10002 --vlan-id 103 --ip-version ipv6 --primary-peer-subnet 2002:db00::/126 '
                 '--secondary-peer-subnet 2003:db00::/126',
                 checks=[self.check('ipv6PeeringConfig.primaryPeerAddressPrefix', '2002:db00::/126'),
                         self.check('ipv6PeeringConfig.secondaryPeerAddressPrefix', '2003:db00::/126')])


class NetworkExpressRouteGlobalReachScenarioTest(ScenarioTest):

    @record_only()  # record_only as the express route is extremely expensive, contact service team for an available ER
    @ResourceGroupPreparer(name_prefix='cli_test_express_route_global_reach')
    def test_network_express_route_global_reach(self, resource_group):
        from azure.core.exceptions import HttpResponseError
        self.kwargs.update({
            'er1': 'er1',
            'er2': 'er2',
            'conn12': 'conn12',
        })

        self.cmd('network express-route create -g {rg} -n {er1} --allow-global-reach --bandwidth 50 --peering-location Area51 --provider "Microsoft ER Test" --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er1} --peering-type AzurePrivatePeering --peer-asn 10001 --vlan-id 101 --primary-peer-subnet 102.0.0.0/30 --secondary-peer-subnet 103.0.0.0/30')

        self.cmd('network express-route create -g {rg} -n {er2} --allow-global-reach --bandwidth 50 --peering-location "Denver Test" --provider "Test Provider NW" --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er2} --peering-type AzurePrivatePeering --peer-asn 10002 --vlan-id 102 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30')

        # These commands won't succeed because circuit creation requires a manual step from the service.
        with self.assertRaisesRegex(HttpResponseError, 'is Not Provisioned'):
            self.cmd('network express-route peering connection create -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12} --peer-circuit {er2} --address-prefix 104.0.0.0/29')
        self.cmd('network express-route peering connection show -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12}')
        self.cmd('network express-route peering connection list -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering')
        self.cmd('network express-route peering connection delete -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12}')

    @record_only()  # record_only as the express route is extremely expensive, contact service team for an available ER
    @ResourceGroupPreparer(name_prefix='cli_test_express_route_peer_connection')
    def test_network_express_route_peer_connection(self, resource_group):
        from msrestazure.azure_exceptions import CloudError

        self.kwargs.update({
            'er1': 'er1',
            'er2': 'er2',
            'peconn12': 'peconn12',
        })

        self.cmd('network express-route create -g {rg} -n {er1} --allow-global-reach --bandwidth 50 --peering-location Area51 --provider "Microsoft ER Test" --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er1} --peering-type AzurePrivatePeering --peer-asn 10001 --vlan-id 101 --primary-peer-subnet 102.0.0.0/30 --secondary-peer-subnet 103.0.0.0/30')

        self.cmd('network express-route create -g {rg} -n {er2} --allow-global-reach --bandwidth 50 --peering-location "Denver Test" --provider "Test Provider NW" --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er2} --peering-type AzurePrivatePeering --peer-asn 10002 --vlan-id 102 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30')

        # cannot create it, so this test will fail due to resource is not found.
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network express-route peering peer-connection show -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {peconn12}')
        self.cmd('network express-route peering peer-connection list -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering')

    @record_only()  # record_only as the express route is extremely expensive, contact service team for an available ER
    @ResourceGroupPreparer(name_prefix='cli_test_express_route_global_reach_config')
    def test_network_express_route_global_reach_config(self, resource_group):
        from azure.core.exceptions import HttpResponseError
        self.kwargs.update({
            'er1': 'er1',
            'er2': 'er2',
            'conn12': 'conn12',
        })

        self.cmd('network express-route create -g {rg} -n {er1} --allow-global-reach --bandwidth 50 --peering-location Area51 --provider "Microsoft ER Test" --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er1} --peering-type AzurePrivatePeering --peer-asn 10001 --vlan-id 101 --primary-peer-subnet 102.0.0.0/30 --secondary-peer-subnet 103.0.0.0/30')

        self.cmd('network express-route create -g {rg} -n {er2} --allow-global-reach --bandwidth 50 --peering-location "Denver Test" --provider "Test Provider NW" --sku-tier Premium')
        self.cmd('network express-route peering create -g {rg} --circuit-name {er2} --peering-type AzurePrivatePeering --peer-asn 10002 --vlan-id 102 --primary-peer-subnet 104.0.0.0/30 --secondary-peer-subnet 105.0.0.0/30')

        # These commands won't succeed because circuit creation requires a manual step from the service.
        with self.assertRaisesRegex(HttpResponseError, 'is Not Provisioned'):
            self.cmd('network express-route peering connection create -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12} --peer-circuit {er2} --address-prefix 104.0.0.0/29')
        with self.assertRaisesRegex(HttpResponseError, 'ParentResourceIsInFailedState'):
            self.cmd('network express-route peering connection ipv6-config set -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12} --address-prefix .../125')
        with self.assertRaisesRegex(HttpResponseError, 'ParentResourceIsInFailedState'):
            self.cmd('network express-route peering connection ipv6-config remove -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12}')
        self.cmd('network express-route peering connection delete -g {rg} --circuit-name {er1} --peering-name AzurePrivatePeering -n {conn12}')


class NetworkCrossRegionLoadBalancerScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cr_load_balancer')
    def test_network_cross_region_lb(self, resource_group):

        self.kwargs.update({
            'lb': 'cross-region-lb',
            'rg': resource_group,
            'rt': 'Microsoft.Network/loadBalancers',
            'pub_ip': 'publicip4'
        })

        # test lb create with min params (new ip)
        self.cmd('network cross-region-lb create -n {lb}1 -g {rg}', checks=[
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            self.check('loadBalancer.frontendIPConfigurations[0].resourceGroup', '{rg}')
        ])

        # test internet facing load balancer with new static public IP
        self.cmd('network cross-region-lb create -n {lb}2 -g {rg} --public-ip-address-allocation static --tags foo=doo')
        self.cmd('network public-ip show -g {rg} -n PublicIP{lb}2', checks=[
            self.check('publicIpAllocationMethod', 'Static'),
            self.check('tags.foo', 'doo')
        ])

        # test internet facing load balancer with existing public IP (by name)
        self.cmd('network public-ip create -n {pub_ip} -g {rg} --sku Standard --tier Global')
        self.cmd('network cross-region-lb create -n {lb}3 -g {rg} --public-ip-address {pub_ip}', checks=[
            self.check('loadBalancer.frontendIPConfigurations[0].properties.privateIPAllocationMethod', 'Dynamic'),
            self.check('loadBalancer.frontendIPConfigurations[0].resourceGroup', '{rg}'),
            self.check("loadBalancer.frontendIPConfigurations[0].properties.publicIPAddress.contains(id, '{pub_ip}')", True)
        ])

        self.cmd('network cross-region-lb list', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True)
        ])
        self.cmd('network cross-region-lb list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?type == '{rt}']) == length(@)", True),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
        self.cmd('network cross-region-lb show --resource-group {rg} --name {lb}1', checks=[
            self.check('type(@)', 'object'),
            self.check('type', '{rt}'),
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{lb}1')
        ])
        # test cross-region-lb update
        self.cmd(
            'network cross-region-lb update --resource-group {rg} --name {lb}1 --set tags.CostCenter=MyBusinessGroup',
            checks=[
                self.check('tags.CostCenter', 'MyBusinessGroup')
            ])
        self.cmd('network cross-region-lb delete --resource-group {rg} --name {lb}1')
        # Expecting no results as we just deleted the only lb in the resource group
        self.cmd('network cross-region-lb list --resource-group {rg}', checks=self.check('length(@)', 2))

    @ResourceGroupPreparer(name_prefix='cli_test_cross_region_load_balancer_ip_config')
    def test_network_cross_region_load_balancer_ip_config(self, resource_group):

        for i in range(1, 4):  # create 3 public IPs to use for the test
            self.cmd('network public-ip create -g {{rg}} -n publicip{} --sku Standard'.format(i))

        # create internet-facing LB with public IP (lb1)
        self.cmd('network cross-region-lb create -g {rg} -n lb1 --public-ip-address publicip1')

        # Test frontend IP configuration for internet-facing LB
        self.cmd('network cross-region-lb frontend-ip create -g {rg} --lb-name lb1 -n ipconfig1 --public-ip-address publicip2')
        self.cmd('network cross-region-lb frontend-ip list -g {rg} --lb-name lb1',
                 checks=self.check('length(@)', 2))
        self.cmd('network cross-region-lb frontend-ip update -g {rg} --lb-name lb1 -n ipconfig1 --public-ip-address publicip3')
        self.cmd('network cross-region-lb frontend-ip show -g {rg} --lb-name lb1 -n ipconfig1',
                 checks=self.check("publicIpAddress.contains(id, 'publicip3')", True))

        # test generic update
        self.kwargs['ip2_id'] = resource_id(subscription=self.get_subscription_id(), resource_group=self.kwargs['rg'], namespace='Microsoft.Network', type='publicIPAddresses', name='publicip2')
        self.cmd('network cross-region-lb frontend-ip update -g {rg} --lb-name lb1 -n ipconfig1 --set publicIpAddress.id="{ip2_id}"',
                 checks=self.check("publicIpAddress.contains(id, 'publicip2')", True))
        self.cmd('network cross-region-lb frontend-ip delete -g {rg} --lb-name lb1 -n ipconfig1')
        self.cmd('network cross-region-lb frontend-ip list -g {rg} --lb-name lb1',
                 checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_cross_region_lb_address_pool', location='eastus2')
    def test_network_cross_region_lb_address_pool(self, resource_group):

        self.kwargs.update({
            'lb': self.create_random_name('cross_region_lb', 24),
            'rg': resource_group
        })

        self.cmd('network cross-region-lb create -g {rg} -n {lb}')

        for i in range(1, 4):
            self.cmd('network cross-region-lb address-pool create -g {{rg}} --lb-name {{lb}} -n bap{}'.format(i),
                     checks=self.check('name', 'bap{}'.format(i)))
        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 4))
        self.cmd('network lb address-pool show -g {rg} --lb-name {lb} -n bap1',
                 checks=self.check('name', 'bap1'))
        self.cmd('network lb address-pool delete -g {rg} --lb-name {lb} -n bap1',
                 checks=self.is_empty())
        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))

    @ResourceGroupPreparer(name_prefix='cli_test_cross_region_lb_address_pool_addresses', location='eastus2')
    def test_network_cross_region_lb_address_pool_addresses(self, resource_group):

        self.kwargs.update({
            'regional_lb1': self.create_random_name('regional_lb', 24),
            'regional_lb2': self.create_random_name('regional_lb', 24),
            'lb': self.create_random_name('cross_region_lb', 24),
            'address_pool': self.create_random_name('address_pool', 24),
            'backend_address1': self.create_random_name('backend_address', 24),
            'backend_address2': self.create_random_name('backend_address', 24),
            'rg': resource_group,
            'lb_address_pool_file_path': os.path.join(TEST_DIR, 'test-cross-region-lb-address-pool-config.json')
        })

        regional_lb_frontend_ip_address1 = self.cmd('network lb create -n {regional_lb1} -g {rg} --sku Standard').get_output_in_json()['loadBalancer']['frontendIPConfigurations'][0]['id']
        regional_lb_frontend_ip_address2 = self.cmd('network lb create -n {regional_lb2} -g {rg} --sku Standard').get_output_in_json()['loadBalancer']['frontendIPConfigurations'][0]['id']

        self.kwargs.update({
            'regional_lb_frontend_ip_address1': regional_lb_frontend_ip_address1,
            'regional_lb_frontend_ip_address2': regional_lb_frontend_ip_address2
        })
        self.cmd('network cross-region-lb create -g {rg} -n {lb}')

        self.cmd('network cross-region-lb address-pool create -g {rg} --lb-name {lb} -n {address_pool} '
                 '--backend-address name={backend_address1} frontend-ip-address={regional_lb_frontend_ip_address1} ',
                 checks=self.check('name', self.kwargs['address_pool']))

        self.cmd('network cross-region-lb address-pool address add -g {rg} --lb-name {lb} --pool-name {address_pool} --name {backend_address2} --frontend-ip-address {regional_lb_frontend_ip_address2}', checks=self.check('name', self.kwargs['address_pool']))

        self.cmd('network cross-region-lb address-pool address remove -g {rg} --lb-name {lb} --pool-name {address_pool} --name {backend_address2}', checks=self.check('name', self.kwargs['address_pool']))

        self.cmd('network cross-region-lb address-pool address list -g {rg} --lb-name {lb} --pool-name {address_pool}', checks=self.check('length(@)', 1))

        self.cmd('network cross-region-lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))
        self.cmd('network cross-region-lb address-pool show -g {rg} --lb-name {lb} -n {address_pool}',
                 checks=self.check('name', self.kwargs['address_pool']))
        self.cmd('network cross-region-lb address-pool delete -g {rg} --lb-name {lb} -n {address_pool}',
                 checks=self.is_empty())
        self.cmd('network cross-region-lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_cross_region_lb_probes', location='eastus2')
    def test_network_cross_region_lb_probes(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.kwargs['lb2'] = 'lb2'
        self.cmd('network cross-region-lb create -g {rg} -n {lb}')

        for i in range(1, 4):
            self.cmd('network cross-region-lb probe create -g {{rg}} --lb-name {{lb}} -n probe{0} --port {0} --protocol http --path "/test{0}"'.format(i))
        self.cmd('network lb probe list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))
        self.cmd('network cross-region-lb probe update -g {rg} --lb-name {lb} -n probe1 --interval 20 --threshold 5')
        self.cmd('network cross-region-lb probe update -g {rg} --lb-name {lb} -n probe2 --protocol tcp --path ""')
        self.cmd('network cross-region-lb probe show -g {rg} --lb-name {lb} -n probe1', checks=[
            self.check('intervalInSeconds', 20),
            self.check('numberOfProbes', 5)
        ])
        # test generic update
        self.cmd('network cross-region-lb probe update -g {rg} --lb-name {lb} -n probe1 --set intervalInSeconds=15 --set numberOfProbes=3', checks=[
            self.check('intervalInSeconds', 15),
            self.check('numberOfProbes', 3)
        ])

        self.cmd('network cross-region-lb probe show -g {rg} --lb-name {lb} -n probe2', checks=[
            self.check('protocol', 'Tcp'),
            self.check('path', None)
        ])
        self.cmd('network cross-region-lb probe delete -g {rg} --lb-name {lb} -n probe3')
        self.cmd('network cross-region-lb probe list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))

        # test standard LB supports https probe
        self.cmd('network cross-region-lb create -g {rg} -n {lb2}')
        self.cmd('network cross-region-lb probe create -g {rg} --lb-name {lb2} -n probe1 --port 443 --protocol https --path "/test1"')
        self.cmd('network cross-region-lb probe list -g {rg} --lb-name {lb2}', checks=self.check('[0].protocol', 'Https'))

    @ResourceGroupPreparer(name_prefix='cli_test_cross_region_lb_rules')
    def test_network_cross_region_lb_rules(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.cmd('network cross-region-lb create -g {rg} -n {lb}')

        self.cmd('network cross-region-lb rule create -g {rg} --lb-name {lb} -n rule2 --frontend-port 60 --backend-port 60 --protocol tcp')
        self.cmd('network cross-region-lb address-pool create -g {rg} --lb-name {lb} -n bap1')
        self.cmd('network cross-region-lb address-pool create -g {rg} --lb-name {lb} -n bap2')
        self.cmd('network cross-region-lb rule create -g {rg} --lb-name {lb} -n rule1 --frontend-ip-name LoadBalancerFrontEnd --frontend-port 40 --backend-pool-name bap1 --backend-port 40 --protocol tcp')

        self.cmd('network cross-region-lb rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))
        self.cmd('network cross-region-lb rule update -g {rg} --lb-name {lb} -n rule1 --floating-ip true --idle-timeout 20 --load-distribution sourceip --protocol udp')
        self.cmd('network cross-region-lb rule update -g {rg} --lb-name {lb} -n rule2 --backend-pool-name bap2 --load-distribution sourceipprotocol')
        self.cmd('network cross-region-lb rule show -g {rg} --lb-name {lb} -n rule1', checks=[
            self.check('enableFloatingIp', True),
            self.check('idleTimeoutInMinutes', 20),
            self.check('loadDistribution', 'SourceIP'),
            self.check('protocol', 'Udp')
        ])
        # test generic update
        self.cmd('network cross-region-lb rule update -g {rg} --lb-name {lb} -n rule1 --set idleTimeoutInMinutes=5',
                 checks=self.check('idleTimeoutInMinutes', 5))

        self.cmd('network cross-region-lb rule show -g {rg} --lb-name {lb} -n rule2', checks=[
            self.check("backendAddressPool.contains(id, 'bap2')", True),
            self.check('loadDistribution', 'SourceIPProtocol')
        ])
        self.cmd('network cross-region-lb rule delete -g {rg} --lb-name {lb} -n rule1')
        self.cmd('network cross-region-lb rule delete -g {rg} --lb-name {lb} -n rule2')
        self.cmd('network cross-region-lb rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 0))


class NetworkLoadBalancerScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_load_balancer', location='eastus2')
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
            self.check('tags.foo', 'doo')
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


class NetworkLoadBalancerIpConfigScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_load_balancer_ip_config', location='eastus2')
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
            self.check("contains(frontendIpConfigurations[0].id, '{frontend1}')", True)
        ])
        self.cmd('network lb outbound-rule create -g {rg} --lb-name {lb} -n {rule2} --address-pool {backend} --frontend-ip-configs {frontend2} --idle-timeout 20 --protocol all', checks=[
            self.check('idleTimeoutInMinutes', 20),
            self.check("contains(backendAddressPool.id, '{backend}')", True),
            self.check("contains(frontendIpConfigurations[0].id, '{frontend2}')", True)
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
            self.check("contains(frontendIpConfigurations[0].id, '{frontend1}')", True)
        ])
        self.cmd('network lb outbound-rule delete -g {rg} --lb-name {lb} -n {rule1}')
        self.cmd('network lb outbound-rule list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 1))


class NetworkLoadBalancerSubresourceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_rules', location='eastus2')
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

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_rules_v2', location='eastus2')
    def test_network_lb_nat_rules_v2(self, resource_group):
        self.kwargs['lb'] = 'lb1'
        self.cmd('network lb create -g {rg} -n {lb} --sku Standard')

        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule3 --protocol tcp  --backend-port 3 '
                 '--frontend-port-range-start 0 --frontend-port-range-end 3', checks=[
                 self.check('name', 'rule3'),
                 self.check('frontendPortRangeStart', 0),
                 self.check('frontendPortRangeEnd', 3)])
        self.cmd('network lb inbound-nat-rule update -g {rg} --lb-name {lb} -n rule3 --floating-ip true --idle-timeout 10 --frontend-port-range-end 5',
                 checks=self.check('frontendPortRangeEnd', 5))
        self.cmd('network lb inbound-nat-rule delete -g {rg} --lb-name {lb} -n rule3')

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_rules_v3', location='eastus2euap')
    def test_network_lb_nat_rules_v3(self, resource_group):
        self.kwargs.update({
            'lb': 'lb1',
            'backend': 'lb1bepool',
        })

        self.cmd('network lb create -g {rg} -n {lb} --sku Standard')

        # test lb inbound-nat-rule create with new param --backend-pool-name
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n rule3 --protocol tcp --backend-port 30 '
                 '--frontend-port-range-start 0 --frontend-port-range-end 3 --backend-pool-name {backend}', checks=[
            self.check('name', 'rule3'),
            self.check('frontendPortRangeStart', 0),
            self.check('frontendPortRangeEnd', 3),
            self.check("contains(backendAddressPool.id, '{backend}')", True)])
        self.cmd(
            'network lb inbound-nat-rule update -g {rg} --lb-name {lb} -n rule3 --floating-ip true --idle-timeout 10 --frontend-port-range-end 5',
            checks=self.check('frontendPortRangeEnd', 5))
        self.cmd('network lb inbound-nat-rule delete -g {rg} --lb-name {lb} -n rule3')

    @ResourceGroupPreparer(name_prefix='cli_test_lb_nat_pools', location='eastus2')
    def test_network_lb_nat_pools(self, resource_group):

        self.kwargs['lb'] = 'lb1'
        self.cmd('network lb create -g {rg} -n {lb}')

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool create -g {{rg}} --lb-name {{lb}} -n rule{0} --protocol tcp --frontend-port-range-start {0}  --frontend-port-range-end {1} --backend-port {0}'.format(count, count + 999))
        self.cmd('network lb inbound-nat-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 3))
        self.cmd('network lb inbound-nat-pool update -g {rg} --lb-name {lb} -n rule1000 --protocol udp --backend-port 50 --floating-ip --idle-timeout 20')
        self.cmd('network lb inbound-nat-pool show -g {rg} --lb-name {lb} -n rule1000', checks=[
            self.check('protocol', 'Udp'),
            self.check('backendPort', 50),
            self.check('enableFloatingIp', True),
            self.check('idleTimeoutInMinutes', 20)
        ])
        # test generic update
        self.cmd('network lb inbound-nat-pool update -g {rg} --lb-name {lb} -n rule1000 --set protocol=Tcp',
                 checks=self.check('protocol', 'Tcp'))

        for count in range(1000, 4000, 1000):
            self.cmd('network lb inbound-nat-pool delete -g {{rg}} --lb-name {{lb}} -n rule{}'.format(count))
        self.cmd('network lb inbound-nat-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 0))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_address_pool', location='eastus2')
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

    @ResourceGroupPreparer(name_prefix='cli_test_lb_address_pool_addresses', location='eastus2')
    def test_network_lb_address_pool_addresses(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'vnet': 'clitestvnet',
            'nic': 'clitestnic',
            'rg': resource_group,
            'lb_address_pool_file_path': os.path.join(TEST_DIR, 'test-address-pool-config.json'),
            'subnet_name': 'subnetx'
        })
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name subnet1')
        self.cmd('network vnet subnet create -g {rg} -n {subnet_name} --vnet-name {vnet} --address-prefixes 10.0.1.0/24')
        self.cmd('network nic create -g {rg} -n {nic} --subnet subnet1 --vnet-name {vnet}')
        self.cmd('network lb create -g {rg} -n {lb} --sku Standard')

        self.kwargs['subnet'] = self.cmd('network vnet show -g {rg} -n {vnet}').get_output_in_json()['subnets'][0]['id']

        # create with vnet
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap1 --vnet {vnet} '
                 '--backend-address name=addr1 ip-address=10.0.0.1 '
                 '--backend-address name=addr2 ip-address=10.0.0.2 '
                 '--backend-address name=addr3 ip-address=10.0.0.3',
                 checks=self.check('name', 'bap1'))

        # create with subnet
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap2 --vnet {vnet} '
                 '--backend-address name=addr1 ip-address=10.0.0.1 subnet={subnet} '
                 '--backend-address name=addr2 ip-address=10.0.0.2 subnet={subnet_name} '
                 '--backend-address name=addr3 ip-address=10.0.0.3 subnet={subnet}',
                 checks=self.check('name', 'bap2'))

        # update backendpool
        self.cmd('network lb address-pool update -g {rg} --lb-name {lb} -n bap2 --vnet {vnet} '
                 '--backend-address name=addr1 ip-address=10.0.0.3 subnet={subnet} '
                 '--backend-address name=addr2 ip-address=10.0.0.4 subnet={subnet_name} '
                 '--backend-address name=addr3 ip-address=10.0.0.5 subnet={subnet}',
                 checks=[
                     self.check('loadBalancerBackendAddresses[0].ipAddress', '10.0.0.3'),
                     self.check('loadBalancerBackendAddresses[1].ipAddress', '10.0.0.4'),
                     self.check('loadBalancerBackendAddresses[2].ipAddress', '10.0.0.5')
                 ])

        self.cmd('network lb address-pool delete -g {rg} --lb-name {lb} -n bap2 ')

        self.cmd('network lb address-pool address add -g {rg} --lb-name {lb} --pool-name bap1 --name addr6 --vnet {vnet} --ip-address 10.0.0.6', checks=self.check('name', 'bap1'))

        self.cmd('network lb address-pool address remove -g {rg} --lb-name {lb} --pool-name bap1 --name addr2', checks=self.check('name', 'bap1'))

        self.cmd('network lb address-pool address list -g {rg} --lb-name {lb} --pool-name bap1', checks=self.check('length(@)', '3'))

        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 2))
        self.cmd('network lb address-pool show -g {rg} --lb-name {lb} -n bap1',
                 checks=self.check('name', 'bap1'))
        self.cmd('network lb address-pool delete -g {rg} --lb-name {lb} -n bap1',
                 checks=self.is_empty())
        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}',
                 checks=self.check('length(@)', 1))

        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap1 --vnet {vnet} '
                 '--backend-addresses-config-file @"{lb_address_pool_file_path}"',
                 checks=self.check('name', 'bap1'))
        self.cmd('network lb address-pool address list -g {rg} --lb-name {lb} --pool-name bap1', checks=self.check('length(@)', '2'))
        self.cmd('network lb address-pool delete -g {rg} --lb-name {lb} -n bap1', checks=self.is_empty())
        self.cmd('network lb address-pool list -g {rg} --lb-name {lb}', checks=self.check('length(@)', 1))
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n bap1 --vnet {vnet}', checks=self.check('name', 'bap1'))

        self.cmd('network lb address-pool address add -g {rg} --lb-name {lb} --pool-name bap1 --name addr6 --vnet {vnet} --ip-address 10.0.0.6', checks=self.check('name', 'bap1'))

        self.cmd('network lb address-pool address list -g {rg} --lb-name {lb} --pool-name bap1', checks=self.check('length(@)', '1'))

        self.cmd('network lb address-pool address add -g {rg} --lb-name {lb} --pool-name bap1 --name addr7 --subnet {subnet} --ip-address 10.0.0.7', checks=self.check('name', 'bap1'))

        self.cmd('network lb address-pool address add -g {rg} --lb-name {lb} --pool-name bap1 --name addr8 --vnet {vnet} --subnet {subnet_name} --ip-address 10.0.0.8', checks=self.check('name', 'bap1'))

        self.cmd('network lb address-pool address list -g {rg} --lb-name {lb} --pool-name bap1', checks=self.check('length(@)', '3'))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_probes', location='eastus2')
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

        # test standard LB supports https probe
        self.cmd('network lb create -g {rg} -n {lb2} --sku standard')
        self.cmd('network lb probe create -g {rg} --lb-name {lb2} -n probe1 --port 443 --protocol https --path "/test1"')
        self.cmd('network lb probe list -g {rg} --lb-name {lb2}', checks=self.check('[0].protocol', 'Https'))

    @ResourceGroupPreparer(name_prefix='cli_test_lb_rules', location='eastus2')
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

    @ResourceGroupPreparer(name_prefix="cli_test_network_lb_port_mapping_")
    def test_network_lb_port_mapping(self):
        self.kwargs.update({
            "lb": "test-lb",
            "rule": "test-nat",
            "pool": "test-pool",
            "start": 3389,
            "end": 4000,
            "vnet": "test-vnet",
            "subnet": "test-subnet",
            "ip": "10.0.0.1",
            "address": "test-address",
        })

        # prepare backend address pool
        self.cmd("network lb create -n {lb} -g {rg} --sku standard")
        self.cmd("network lb address-pool create -n {pool} -g {rg} --lb-name {lb}")
        self.cmd("network vnet create -n {vnet} -g {rg} --subnet-name {subnet}")
        self.cmd(
            "network lb address-pool address add -n {address} -g {rg} --lb-name {lb} --pool-name {pool} "
            "--vnet {vnet} --ip-address {ip}"
        )
        self.cmd(
            "network lb inbound-nat-rule create -n {rule} -g {rg} --lb-name {lb} --backend-pool-name {pool} "
            "--backend-port {start} --frontend-port-range-start {start} --frontend-port-range-end {end} --protocol tcp"
        )

        self.cmd(
            "network lb list-mapping -n {lb} -g {rg} --backend-pool-name {pool} --request ip={ip}",
            checks=[
                self.check("inboundNatRulePortMappings[0].inboundNatRuleName", "{rule}"),
                self.check("inboundNatRulePortMappings[0].backendPort", self.kwargs["start"]),
                self.check("inboundNatRulePortMappings[0].frontendPort", self.kwargs["start"]),
                self.check("inboundNatRulePortMappings[0].protocol", "Tcp"),
            ]
        )


class NetworkLocalGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='local_gateway_scenario')
    def test_network_local_gateway(self, resource_group):

        self.kwargs.update({
            'lgw1': 'lgw1',
            'lgw2': 'lgw2',
            'rt': 'Microsoft.Network/localNetworkGateways'
        })
        self.cmd('network local-gateway create --resource-group {rg} --name {lgw1} --gateway-ip-address 10.1.1.1 --tags foo=doo')
        self.cmd('network local-gateway update --resource-group {rg} --name {lgw1} --tags foo=boo',
                 checks=self.check('tags.foo', 'boo'))
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_nic_scenario', location='eastus2')
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

        # test network nsg update
        self.cmd('network nsg update -g {rg} -n {nsg1} --set tags.CostCenter=MyBusinessGroup')
        self.cmd('network nsg show -g {rg} -n {nsg1}', checks=[
            self.check('tags.CostCenter', 'MyBusinessGroup')
        ])
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
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet_id} --ip-forwarding --private-ip-address {pri_ip} --public-ip-address {pub_ip} --internal-dns-name test --dns-servers 100.1.2.3 --lb-address-pools {address_pool_ids} --lb-inbound-nat-rules {rule_ids} --accelerated-networking --tags foo=doo', checks=[
            self.check('NewNIC.ipConfigurations[0].privateIpAllocationMethod', 'Static'),
            self.check('NewNIC.ipConfigurations[0].privateIpAddress', '{pri_ip}'),
            self.check('NewNIC.enableIpForwarding', True),
            self.check('NewNIC.enableAcceleratedNetworking', True),
            self.check('NewNIC.provisioningState', 'Succeeded'),
            self.check('NewNIC.dnsSettings.internalDnsNameLabel', 'test'),
            self.check('length(NewNIC.dnsSettings.dnsServers)', 1)
        ])
        self.cmd('network lb list-nic -g {rg} -n {lb}', checks=[
            self.check('length(@)', 1)
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
        self.cmd('network nic update -g {rg} -n {nic} --internal-dns-name noodle --ip-forwarding true --accelerated-networking false --dns-servers "" --network-security-group {nsg2}', checks=[
            self.check('enableIpForwarding', True),
            self.check('enableAcceleratedNetworking', False),
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


class NetworkNicAppGatewayScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_nic_app_gateway', location='eastus2')
    def test_network_nic_app_gateway(self, resource_group):
        from azure.core.exceptions import HttpResponseError
        import json

        self.kwargs.update({
            'nic': 'nic1',
            'ag': 'ag1',
            'vnet': 'vnet1',
            'subnet1': 'subnet1',
            'subnet2': 'subnet2',
            'ip': 'ip1',
            'lb': 'lb1',
            'bap': 'bap1',
            'pool1': 'appGatewayBackendPool',
            'pool2': 'bepool2',
            'config1': 'ipconfig1',
            'config2': 'ipconfig2'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet1} --defer')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet2} --address-prefix 10.0.1.0/24')
        self.cmd('network application-gateway create -g {rg} -n {ag} --vnet-name {vnet} --subnet {subnet1} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists --timeout 120')
        self.kwargs['ipaddres'] = json.dumps(
            {
                "ip_address": "10.20.0.69"
            }
        )
        self.cmd("network application-gateway address-pool update -g {rg} --gateway-name {ag} -n {pool1} --add backendAddresses \'{ipaddres}\'", checks=[
            self.check('length(backendAddresses)', 1)
        ])
        self.kwargs['ipaddres'] = json.dumps(
            {
                "ip_address": "10.20.0.70"
            }
        )
        self.cmd("network application-gateway address-pool update -g {rg} --gateway-name {ag} -n {pool1} --add backendAddresses \'{ipaddres}\'", checks=[
            self.check('length(backendAddresses)', 2)
        ])
        self.cmd('network application-gateway address-pool create -g {rg} --gateway-name {ag} -n {pool2} --no-wait')
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n {bap}')
        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet2} --vnet-name {vnet} --gateway-name {ag} --app-gateway-address-pools {pool1}',
                 checks=self.check('length(NewNIC.ipConfigurations[0].applicationGatewayBackendAddressPools)', 1))
        with self.assertRaisesRegex(HttpResponseError, 'not supported for secondary IpConfigurations'):
            self.cmd('network nic ip-config create -g {rg} --nic-name {nic} -n {config2} --subnet {subnet2} --vnet-name {vnet} --gateway-name {ag} --app-gateway-address-pools {pool2}')
        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config1} --gateway-name {ag} --app-gateway-address-pools {pool1} {pool2}',
                 checks=self.check('length(applicationGatewayBackendAddressPools)', 2))
        self.cmd('az network nic ip-config address-pool add -g {rg} --nic-name {nic} --lb-name {lb} --address-pool {bap} --ip-config-name {config1}')


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
            self.check('privateIpAllocationMethod', 'Dynamic')
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
            self.check('privateIpAddress', '{private_ip}'),
            self.check('privateIpAllocationMethod', 'Static')])
        # test generic update
        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --set privateIpAddress=10.0.0.50',
                 checks=self.check('privateIpAddress', '10.0.0.50'))

        # test ability to add and remove IDs one at a time with subcommands
        self.cmd('network nic ip-config inbound-nat-rule remove -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --inbound-nat-rule rule1',
                 checks=self.check('length(loadBalancerInboundNatRules)', 1))
        self.cmd('network nic ip-config inbound-nat-rule add -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --inbound-nat-rule rule1',
                 checks=self.check('length(loadBalancerInboundNatRules)', 2))

        self.cmd('network nic ip-config address-pool remove -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --address-pool bap1',
                 checks=self.check('length(loadBalancerBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool add -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --address-pool bap1',
                 checks=self.check('length(loadBalancerBackendAddressPools)', 2))

        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --private-ip-address "" --public-ip-address {ip_id}', checks=[
            self.check('privateIpAllocationMethod', 'Dynamic'),
            self.check("publicIpAddress.contains(id, '{ip_id}')", True)
        ])

        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {config} --subnet {subnet} --vnet-name {vnet}',
                 checks=self.check("subnet.contains(id, '{subnet}')", True))

    @ResourceGroupPreparer(name_prefix='cli_test_nic_lb_address_pools', location='eastus2')
    def test_network_nic_lb_address_pools(self, resource_group):

        self.kwargs.update({
            'nic': 'nic1',
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'config': 'ipconfig1',
            'lb': 'lb1',
            'pool': 'pool1'
        })

        self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1')
        self.cmd('network nic create -g {rg} -n {nic} --subnet subnet1 --vnet-name vnet1')

        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n {pool}')
        self.kwargs['lb_pool_id'] = self.cmd('network lb address-pool show -g {rg} --lb-name {lb} -n {pool}').get_output_in_json()['id']

        self.cmd('network nic ip-config address-pool add -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --address-pool {pool}',
                 checks=self.check('length(loadBalancerBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool remove -g {rg} --lb-name {lb} --nic-name {nic} --ip-config-name {config} --address-pool {pool}',
                 checks=self.check('loadBalancerBackendAddressPools', None))
        self.cmd('network nic ip-config address-pool add -g {rg} --nic-name {nic} --ip-config-name {config} --address-pool {lb_pool_id}',
                 checks=self.check('length(loadBalancerBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool remove -g {rg} --nic-name {nic} --ip-config-name {config} --address-pool {lb_pool_id}',
                 checks=self.check('loadBalancerBackendAddressPools', None))

    @ResourceGroupPreparer(name_prefix='cli_test_nic_ag_address_pools')
    def test_network_nic_ag_address_pools(self, resource_group):

        self.kwargs.update({
            'nic': 'nic1',
            'vnet': 'vnet1',
            'subnet1': 'subnet1',
            'subnet2': 'subnet2',
            'config': 'ipconfig1',
            'ag': 'ag1',
            'pool': 'pool1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet1} --defer')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet2} --address-prefix 10.0.1.0/24')
        self.cmd('network application-gateway create -g {rg} -n {ag} --vnet-name {vnet} --subnet {subnet1} --no-wait')
        self.cmd('network application-gateway wait -g {rg} -n {ag} --exists --timeout 120')
        self.cmd('network application-gateway address-pool create -g {rg} --gateway-name {ag} -n {pool} --no-wait')
        self.kwargs['ag_pool_id'] = self.cmd('network application-gateway address-pool show -g {rg} --gateway-name {ag} -n {pool}').get_output_in_json()['id']

        self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet2} --vnet-name {vnet}')

        self.cmd('network nic ip-config address-pool add -g {rg} --gateway-name {ag} --nic-name {nic} --ip-config-name {config} --address-pool {pool}',
                 checks=self.check('length(applicationGatewayBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool remove -g {rg} --gateway-name {ag} --nic-name {nic} --ip-config-name {config} --address-pool {pool}',
                 checks=self.check('applicationGatewayBackendAddressPools', None))
        self.cmd('network nic ip-config address-pool add -g {rg} --nic-name {nic} --ip-config-name {config} --address-pool {ag_pool_id}',
                 checks=self.check('length(applicationGatewayBackendAddressPools)', 1))
        self.cmd('network nic ip-config address-pool remove -g {rg} --nic-name {nic} --ip-config-name {config} --address-pool {ag_pool_id}',
                 checks=self.check('applicationGatewayBackendAddressPools', None))


class NetworkNicConvenienceCommandsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_nic_convenience_test')
    def test_network_nic_convenience_commands(self, resource_group):

        self.kwargs['vm'] = 'conveniencevm1'
        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --admin-username myusername --admin-password aBcD1234!@#$ --authentication-type password --nsg-rule None')
        self.kwargs['nic_id'] = self.cmd('vm show -g {rg} -n {vm} --query "networkProfile.networkInterfaces[0].id"').get_output_in_json()
        self.cmd('network nic list-effective-nsg --ids {nic_id}',
                 checks=self.greater_than('length(@)', 0))
        self.cmd('network nic show-effective-route-table --ids {nic_id}',
                 checks=self.greater_than('length(@)', 0))


class NetworkExtendedNSGScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_extended_nsg')
    def test_network_extended_nsg(self, resource_group):

        self.kwargs.update({
            'nsg': 'nsg1',
            'rule': 'rule1'
        })
        self.cmd('network nsg create --name {nsg} -g {rg}')
        self.cmd('network nsg rule create --access allow --destination-address-prefixes 10.0.0.0/24 11.0.0.0/24 --direction inbound --nsg-name {nsg} --protocol * -g {rg} --source-address-prefix * -n {rule} --source-port-range 700-900 1000-1100 --destination-port-range 4444 --priority 1000', checks=[
            self.check('length(destinationAddressPrefixes)', 2),
            self.check('destinationAddressPrefix', ''),
            self.check('length(sourceAddressPrefixes)', 0),
            self.check('sourceAddressPrefix', '*'),
            self.check('length(sourcePortRanges)', 2),
            self.check('sourcePortRange', None),
            self.check('length(destinationPortRanges)', 0),
            self.check('destinationPortRange', '4444')
        ])
        self.cmd('network nsg rule update --destination-address-prefixes Internet --nsg-name {nsg} -g {rg} --source-address-prefix 10.0.0.0/24 11.0.0.0/24 -n {rule} --source-port-range * --destination-port-range 500-1000 2000 3000', checks=[
            self.check('length(destinationAddressPrefixes)', 0),
            self.check('destinationAddressPrefix', 'Internet'),
            self.check('length(sourceAddressPrefixes)', 2),
            self.check('sourceAddressPrefix', ''),
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
        # test route-table route update
        self.cmd('network route-table route update -g {rg} -n {route} --route-table-name {table} --next-hop-type VirtualNetworkGateway' , checks=[
            self.check('nextHopType', 'VirtualNetworkGateway')
            ])

        self.cmd('network route-table route delete --resource-group {rg} --route-table-name {table} --name {route}')
        self.cmd('network route-table route list --resource-group {rg} --route-table-name {table}', checks=self.is_empty())
        self.cmd('network route-table delete --resource-group {rg} --name {table}')
        self.cmd('network route-table list --resource-group {rg}', checks=self.is_empty())


class NetworkVNetScenarioTest(ScenarioTest):

    @AllowLargeResponse()
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

    @ResourceGroupPreparer(name_prefix='cli_vnet_with_subnet_nsg_test')
    def test_network_vnet_with_subnet_nsg(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'nsg': 'nsg',
            'rt': 'Microsoft.Network/virtualNetworks',
            'prefixes': '20.0.0.0/16 10.0.0.0/16'
        })
        result = self.cmd('network nsg create --resource-group {rg} --name {nsg}').get_output_in_json()
        self.kwargs['nsg_id'] = result['NewNSG']['id']
        self.cmd('network vnet create --resource-group {rg} --name {vnet} --address-prefixes {prefixes} '
                 '--subnet-name {subnet} --subnet-prefixes 20.0.0.0/24 --nsg {nsg}')
        self.cmd('network vnet subnet list --resource-group {rg} --vnet-name {vnet}',
                 checks=self.check('type(@)', 'array'))
        self.cmd('network vnet subnet show --resource-group {rg} --vnet-name {vnet} --name {subnet}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{subnet}'),
            self.check('networkSecurityGroup.id', '{nsg_id}')
        ])

        self.cmd('network vnet subnet delete --resource-group {rg} --vnet-name {vnet} --name {subnet}')

    @ResourceGroupPreparer(name_prefix='cli_vnet_test')
    def test_network_vnet_list_available_ips(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'rt': 'Microsoft.Network/virtualNetworks',
            'rg': resource_group
        })

        self.cmd('network vnet create --resource-group {rg} --name {vnet} --subnet-name default', checks=[
            self.check('newVNet.provisioningState', 'Succeeded'),
            self.check('newVNet.addressSpace.addressPrefixes[0]', '10.0.0.0/16')
        ])
        self.kwargs['prefixes'] = '20.0.0.0/16 10.0.0.0/16'
        self.cmd('network vnet update --resource-group {rg} --name {vnet} --address-prefixes {prefixes} --dns-servers 1.2.3.4', checks=[
            self.check('length(addressSpace.addressPrefixes)', 2),
            self.check('dhcpOptions.dnsServers[0]', '1.2.3.4')
        ])

        self.cmd('network vnet subnet create --resource-group {rg} --vnet-name {vnet} --name {subnet} --address-prefix 20.0.0.0/24')

        self.cmd('network vnet list-available-ips -g {rg} --name {vnet}', checks=[
            self.check('length(@)', 5)
        ])

    @ResourceGroupPreparer(name_prefix='cli_vnet_with_bgp_community')
    def test_network_vnet_with_bgp_community(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1',
        })

        self.cmd('network vnet create --resource-group {rg} --name {vnet} --subnet-name default --bgp-community "12076:20000"', checks=[
            self.check('newVNet.bgpCommunities.regionalCommunity', '12076:50006'),
            self.check('newVNet.bgpCommunities.virtualNetworkCommunity', '12076:20000')
        ])

        self.cmd('network vnet update --resource-group {rg} --name {vnet} --bgp-community "12076:20001"', checks=[
            self.check('bgpCommunities.regionalCommunity', '12076:50006'),
            self.check('bgpCommunities.virtualNetworkCommunity', '12076:20001')
        ])

    @ResourceGroupPreparer(name_prefix='cli_vnet_with_encryption')
    def test_network_vnet_with_encryption(self, resource_group):
        self.kwargs.update({
            'allowUnencrypted': 'AllowUnencrypted',
            'dropUnencrypted': 'DropUnencrypted',
        })
        # only create with --enable-encryption and --encryption-enforcement-policy
        self.cmd('network vnet create --address-prefixes 10.0.0.0/16 -n MyVnet1 -g {rg} --subnet-name Mysubnet --subnet-prefixes 10.0.0.0/24 --enable-encryption true --encryption-enforcement-policy allowUnencrypted')
        self.cmd('network vnet create --address-prefixes 10.1.0.0/16 -n MyVnet2 -g {rg} --subnet-name MySubnet --subnet-prefixes 10.1.0.0/24 --enable-encryption true --encryption-enforcement-policy dropUnencrypted')
        self.cmd('network vnet show -n MyVnet1 -g {rg}', checks=[
            self.check('encryption.enabled', True),
            self.check('encryption.enforcement', '{allowUnencrypted}'),
        ])
        self.cmd('network vnet show -n MyVnet2 -g {rg}', checks=[
            self.check('encryption.enabled', True),
            self.check('encryption.enforcement', '{dropUnencrypted}'),
        ])
        # only create with --enable-encryption
        self.cmd('network vnet create --address-prefixes 10.2.0.0/16 --name MyVnet3 --resource-group {rg} --subnet-name Mysubnet --subnet-prefixes 10.2.0.0/24 --enable-encryption false')
        self.cmd('network vnet create --address-prefixes 10.3.0.0/16 --name MyVnet4 --resource-group {rg} --subnet-name MySubnet --subnet-prefixes 10.3.0.0/24 --enable-encryption true', expect_failure=True)
        self.cmd('network vnet update --name MyVnet3 --resource-group {rg} --enable-encryption true --encryption-enforcement-policy allowUnencrypted', checks=[
            self.check('encryption.enabled', True),
            self.check('encryption.enforcement', '{allowUnencrypted}'),
        ])
        self.cmd('network vnet update --name MyVnet3 --resource-group {rg} --enable-encryption true --encryption-enforcement-policy dropUnencrypted', checks=[
            self.check('encryption.enabled', True),
            self.check('encryption.enforcement', '{dropUnencrypted}'),
        ])
        # only create with --encryption-enforcement-policy
        self.cmd('network vnet create --address-prefixes 10.4.0.0/16 --name MyVnet5 --resource-group {rg} --subnet-name Mysubnet --subnet-prefixes 10.4.0.0/24 --encryption-enforcement-policy allowUnencrypted', expect_failure=True)
        # create without encryption
        self.cmd('network vnet create --address-prefixes 10.5.0.0/16 --name MyVnet6 --resource-group {rg} --subnet-name Mysubnet --subnet-prefixes 10.5.0.0/24')
        self.cmd('network vnet create --address-prefixes 10.6.0.0/16 --name MyVnet7 --resource-group {rg} --subnet-name Mysubnet --subnet-prefixes 10.6.0.0/24')
        self.cmd('network vnet create --address-prefixes 10.7.0.0/16 --name MyVnet8 --resource-group {rg} --subnet-name Mysubnet --subnet-prefixes 10.7.0.0/24')
        # update
        self.cmd('network vnet update --name MyVnet6 --resource-group {rg} --enable-encryption true', expect_failure=True)
        self.cmd('network vnet update --name MyVnet7 --resource-group {rg} --encryption-enforcement-policy dropUnencrypted', expect_failure=True)
        self.cmd('network vnet update --name MyVnet8 --resource-group {rg} --enable-encryption true --encryption-enforcement-policy dropUnencrypted', checks=[
            self.check('encryption.enabled', True),
            self.check('encryption.enforcement', '{dropUnencrypted}'),
        ])
        # vnet peering
        self.cmd('network vnet peering create --name MyVnet1ToMyVnet2 --remote-vnet MyVnet2 --resource-group {rg} --vnet-name MyVnet1')
        self.cmd('network vnet peering show --name MyVnet1ToMyVnet2 --vnet-name MyVnet1 -g {rg}', checks=[
            self.check('remoteVirtualNetworkEncryption.enabled', True),
            self.check('remoteVirtualNetworkEncryption.enforcement', '{dropUnencrypted}'),
        ])

class NetworkVNetCachingScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_vnet_cache_test')
    def test_network_vnet_caching(self, resource_group):
        from time import sleep

        self.kwargs.update({
            'vnet': 'vnet1'
        })

        # test that custom commands work with caching
        self.cmd('network vnet create -g {rg} -n {vnet} --address-prefix 10.0.0.0/16 --defer')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n subnet1 --address-prefix 10.0.0.0/24 --defer')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n subnet2 --address-prefix 10.0.1.0/24 --defer')
        with self.assertRaisesRegex(SystemExit, '3'):
            # ensure vnet has not been created
            self.cmd('network vnet show -g {rg} -n {vnet}')
        self.cmd('cache show -g {rg} -n {vnet} -t VirtualNetwork')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n subnet3 --address-prefix 10.0.2.0/24')
        self.cmd('network vnet show -g {rg} -n {vnet}',
                 checks=self.check('length(subnets)', 3))
        with self.assertRaisesRegex(CLIError, 'Not found in cache'):
            self.cmd('cache show -g {rg} -n {vnet} -t VirtualNetwork')

        # test that generic update works with caching
        self.cmd('network vnet update -g {rg} -n {vnet} --set tags.a=1 --defer')
        self.cmd('network vnet update -g {rg} -n {vnet} --set tags.b=2')
        self.cmd('network vnet show -g {rg} -n {vnet}', checks=[
            self.check('length(tags)', 2),
            self.check('length(subnets)', 3)  # should reflect the write-through behavior from the earlier PUT
        ])

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_vnet_ids_query')
    def test_network_vnet_ids_query(self, resource_group):
        import json

        # This test ensures that --query works with --ids
        self.kwargs.update({
            'vnet1': 'vnet1',
            'vnet2': 'vnet2'
        })
        self.kwargs['id1'] = self.cmd('network vnet create -g {rg} -n {vnet1}').get_output_in_json()['newVNet']['id']
        self.kwargs['id2'] = self.cmd('network vnet create -g {rg} -n {vnet2}').get_output_in_json()['newVNet']['id']
        self.cmd('network vnet show --ids {id1} {id2} --query "[].name"', checks=[
            self.check('length(@)', 2),
            self.check("contains(@, '{vnet1}')", True),
            self.check("contains(@, '{vnet2}')", True),
        ])

        # This test ensures you can pipe a list of IDs to --ids
        self.kwargs['ids'] = self.cmd('network vnet list -g {rg} --query "[].id" -otsv').output
        self.cmd('network vnet show --ids {ids}',
                 checks=self.check('length(@)', 2))

        # This test ensures you can pipe JSON output to --ids Windows-style
        # ensures a single JSON string has its ids parsed out
        self.kwargs['json'] = json.dumps(self.cmd('network vnet list -g {rg}').get_output_in_json())
        self.cmd('network vnet show --ids \'{json}\'',
                 checks=self.check('length(@)', 2))

        # This test ensures you can pipe JSON output to --ids bash-style
        # ensures that a JSON string where each line is interpretted individually
        # is reassembled and treated as a single json string
        json_obj = self.cmd('network vnet list -g {rg}').get_output_in_json()
        for item in json_obj:
            del item['etag']
        split_json = json.dumps(json_obj, indent=4).split()
        split_string = ' '.join(split_json).replace('{', '{{').replace('}', '}}').replace('"', '\\"')
        self.cmd('network vnet show --ids {}'.format(split_string),
                 checks=self.check('length(@)', 2))


class NetworkVNetPeeringScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_network_vnet_flowtimeout', location='centraluseuap')
    def test_network_vnet_flowtimeout(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'time': 10,
            'time1': 20,
        })

        self.cmd('network vnet create -g {rg} -n vnet --flowtimeout {time}',
                 checks=self.check('newVNet.flowTimeoutInMinutes', '{time}'))
        self.cmd('network vnet update -g {rg} -n vnet --flowtimeout {time1}',
                 checks=self.check('flowTimeoutInMinutes', '{time1}'))

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
        # set up gateway sharing from vnet1 to vnet2. test that remote-vnet indeed accepts name or id.
        self.cmd('network vnet peering create -g {rg} -n peering2 --vnet-name vnet2 --remote-vnet {vnet1_id} --allow-gateway-transit', checks=[
            self.check('allowGatewayTransit', True),
            self.check('remoteVirtualNetwork.id', '{vnet1_id}'),
            self.check('peeringState', 'Initiated')
        ])
        self.cmd('network vnet peering create -g {rg} -n peering1 --vnet-name vnet1 --remote-vnet vnet2 --use-remote-gateways --allow-forwarded-traffic', checks=[
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

    @ResourceGroupPreparer(name_prefix='cli_test_vnet_peering')
    def test_network_vnet_peering_sync(self, resource_group):

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
        # set up gateway sharing from vnet1 to vnet2. test that remote-vnet indeed accepts name or id.
        self.cmd('network vnet peering create -g {rg} -n peering2 --vnet-name vnet2 --remote-vnet {vnet1_id} --allow-gateway-transit', checks=[
            self.check('allowGatewayTransit', True),
            self.check('remoteVirtualNetwork.id', '{vnet1_id}'),
            self.check('peeringState', 'Initiated')
        ])
        self.cmd('network vnet peering create -g {rg} -n peering1 --vnet-name vnet1 --remote-vnet vnet2 --use-remote-gateways --allow-forwarded-traffic', checks=[
            self.check('useRemoteGateways', True),
            self.check('remoteVirtualNetwork.id', '{vnet2_id}'),
            self.check('peeringState', 'Connected'),
            self.check('allowVirtualNetworkAccess', False)
        ])

        self.cmd('network vnet peering sync -g {rg} -n peering1 --vnet-name vnet1')


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
        self.cmd('network vpn-connection list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network vpn-connection list -g {rg} --vnet-gateway {gw1}', checks=[
            self.check('length(@)', 1)
        ])

        # test vpn connection show
        self.cmd('network vpn-connection show -g {rg} -n {conn1}', checks=[
            self.check('name', 'conn1')
        ])
        # test vpn connection show-device-config-script
        self.cmd('network vpn-connection show-device-config-script -g {rg} -n {conn1} --vendor "Cisco" --device-family "Cisco-ISR(IOS)" --firmware-version "Cisco-ISR-15.x--IKEv2+BGP"', checks=[
                self.check('length(@)', 10581)
            ])
        self.cmd('network vpn-connection ipsec-policy add -g {rg} --connection-name {conn1} --ike-encryption AES256 --ike-integrity SHA384 --dh-group DHGroup24 --ipsec-encryption GCMAES256 --ipsec-integrity GCMAES256 --pfs-group PFS24 --sa-lifetime 7200 --sa-max-size 2048')
        self.cmd('network vpn-connection ipsec-policy list -g {rg} --connection-name {conn1}')
        self.cmd('network vpn-connection ipsec-policy clear -g {rg} --connection-name {conn1}')
        self.cmd('network vpn-connection ipsec-policy list -g {rg} --connection-name {conn1}')



class NetworkVpnConnectionNatRule(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_network_vpn_connection_nat_rule')
    def test_network_vpn_connection_nat_rule(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet',
            'lgw1': 'lgw1',
            'lgw1ip': '131.107.72.22',
            'lgw1_prefix1': '10.61.0.0/16',
            'lgw1_prefix2': '10.62.0.0/16',
            'conn1': 'conn1',
            'subnet': 'GatewaySubnet',
            'vg': 'vnet-gateway-name',
            'ip': 'ip-name',
            'sku': 'VpnGw2',
            'nat': 'nat-name',
            'nat1': 'nat-name1',
            'i_map': '10.4.0.0/24',
            'i_map1': '10.5.0.0/24',
            'e_map': '192.168.21.0/24',
            'e_map1': '192.168.22.0/24',
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.cmd('network public-ip create -g {rg} -n {ip}')

        vg = self.cmd('network vnet-gateway create -g {rg} -n {vg} --vnet {vnet} --public-ip-address {ip} --sku {sku} '
                      '--nat-rule name={nat} mode=IngressSnat internal-mappings={i_map} external-mappings={e_map} '
                      '--nat-rule name={nat1} mode=EgressSnat internal-mappings={i_map1} external-mappings={e_map1}',
                      checks=[self.check('length(vnetGateway.natRules)', 2)]).get_output_in_json()

        self.kwargs.update({'id': vg['vnetGateway']['natRules'][0]['id']})
        self.kwargs.update({'id1': vg['vnetGateway']['natRules'][1]['id']})

        self.cmd('network local-gateway create -g {rg} -n {lgw1} --gateway-ip-address {lgw1ip} '
                 '--local-address-prefixes {lgw1_prefix1} {lgw1_prefix2}')
        self.cmd('network vpn-connection create -g {rg} -n {conn1} --vnet-gateway1 {vg} --local-gateway2 {lgw1} '
                 '--shared-key AzureA1b2C3 --ingress-nat-rule {id}',
                 checks=[self.check('length(resource.ingressNatRules)', 1)])

        self.cmd('network vpn-connection delete -g {rg} -n {conn1}')

        self.cmd('network vpn-connection create -g {rg} -n {conn1} --vnet-gateway1 {vg} --local-gateway2 {lgw1} '
                 '--shared-key AzureA1b2C3 --egress-nat-rule {id1}',
                 checks=[self.check('length(resource.egressNatRules)', 1)])


class NetworkVnetGatewayIpSecPolicy(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vnet_gateway_ipsec')
    def test_network_vnet_gateway_ipsec(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1',
            'ip': 'pip1',
            'gw': 'gw1',
            'gw_sku': 'VpnGw2',
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n {ip}')
        self.cmd('network vnet-gateway create -g {rg} -n {gw} --public-ip-address {ip} --vnet {vnet} --sku {gw_sku} --gateway-type Vpn --vpn-type RouteBased --address-prefix 40.1.0.0/24 --client-protocol IkeV2 SSTP --radius-secret 111_aaa --radius-server 30.1.1.15')
        self.cmd('network vnet-gateway ipsec-policy add -g {rg} --gateway-name {gw} --ike-encryption AES256 --ike-integrity SHA384 --dh-group DHGroup24 --ipsec-encryption GCMAES256 --ipsec-integrity GCMAES256 --pfs-group PFS24 --sa-lifetime 7200 --sa-max-size 2048')
        self.cmd('network vnet-gateway ipsec-policy list -g {rg} --gateway-name {gw}')
        self.cmd('network vnet-gateway ipsec-policy clear -g {rg} --gateway-name {gw}')
        self.cmd('network vnet-gateway ipsec-policy list -g {rg} --gateway-name {gw}')
        self.cmd('network vnet-gateway vpn-client show-health -g {rg} -n {gw}')
        self.cmd('network vnet-gateway show-supported-devices -g {rg} -n {gw} -o tsv')


class NetworkVnetGatewayMultiAuth(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_network_vnet_gateway_multi_auth')
    def test_network_vnet_gateway_multi_auth(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet',
            'ip': 'pip',
            'gw': 'gw',
            'gw_sku': 'VpnGw2',
            'aad_tenant': 'https://login.microsoftonline.com/0ab2c4f4-81e6-44cc-a0b2-b3a47a1443f4',
            'aad_issuer': 'https://sts.windows.net/0ab2c4f4-81e6-44cc-a0b2-b3a47a1443f4/',
            'aad_audience': 'a21fce82-76af-45e6-8583-a08cb3b956f9',
            'root_cert_name': 'root-cert',
            'root_cert_data': os.path.join(TEST_DIR, 'test-root-cert.cer'),
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n {ip}')
        self.cmd('network vnet-gateway create -g {rg} -n {gw} --public-ip-address {ip} --vnet {vnet} --sku {gw_sku} '
                 '--gateway-type Vpn --vpn-type RouteBased --address-prefix 40.1.0.0/24 --client-protocol OpenVPN '
                 '--aad-audience {aad_audience} --aad-issuer {aad_issuer} --aad-tenant {aad_tenant} '
                 '--root-cert-name {root_cert_name} --root-cert-data "{root_cert_data}" '
                 '--radius-secret 111_aaa --radius-server 30.1.1.15 --vpn-auth-type AAD Certificate Radius',
                 checks=[self.check('length(vnetGateway.vpnClientConfiguration.vpnAuthenticationTypes)', 3)])

    @ResourceGroupPreparer(name_prefix='test_network_vnet_gateway_multi_auth1')
    def test_network_vnet_gateway_multi_auth1(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet',
            'ip': 'pip',
            'gw': 'gw',
            'gw_sku': 'VpnGw2',
            'aad_tenant': 'https://login.microsoftonline.com/0ab2c4f4-81e6-44cc-a0b2-b3a47a1443f4',
            'aad_issuer': 'https://sts.windows.net/0ab2c4f4-81e6-44cc-a0b2-b3a47a1443f4/',
            'aad_audience': 'a21fce82-76af-45e6-8583-a08cb3b956f9',
            'root_cert_name': 'root-cert',
            'root_cert_data': os.path.join(TEST_DIR, 'test-root-cert.cer'),
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n {ip}')
        self.cmd('network vnet-gateway create -g {rg} -n {gw} --public-ip-address {ip} --vnet {vnet} --sku {gw_sku} '
                 '--gateway-type Vpn --vpn-type RouteBased --address-prefix 40.1.0.0/24 --client-protocol OpenVPN')
        self.cmd('network vnet-gateway update -g {rg} -n {gw} --vpn-auth-type AAD Certificate Radius '
                 '--aad-audience {aad_audience} --aad-issuer {aad_issuer} --aad-tenant {aad_tenant} '
                 '--root-cert-name {root_cert_name} --root-cert-data "{root_cert_data}" '
                 '--radius-secret 111_aaa --radius-server 30.1.1.15 ',
                 checks=[self.check('length(vpnClientConfiguration.vpnAuthenticationTypes)', 3)])


class NetworkVirtualRouter(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_virtual_router', location='WestCentralUS')
    @unittest.skip('Skip as service has bug for deleting peering')
    def test_network_virtual_router_scenario(self, resource_group, resource_group_location):

        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'vnet': 'vnet1',
            'ip': 'pip1',
            'gw': 'gw1',
            'gw_sku': 'HighPerformance',
            'vrouter': 'vrouter1',
            'vrouter_peering': 'peering1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet -l {location} --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n {ip} -l {location}')
        self.cmd('network vnet-gateway create -g {rg} -n {gw} --public-ip-address {ip} --vnet {vnet} --sku {gw_sku} --gateway-type ExpressRoute -l {location}')

        self.cmd('network vrouter create -n {vrouter} -l {location} -g {rg} --hosted-gateway {gw}', checks=[
            self.check('type', 'Microsoft.Network/VirtualRouters'),
            self.check('name', '{vrouter}')
        ])

        self.cmd('network vrouter show -n {vrouter} -g {rg}', checks=[
            self.check('name', '{vrouter}')
        ])

        self.cmd('network vrouter list -g {rg}', checks=[
            self.check('@[0].name', '{vrouter}')
        ])

        self.cmd('network vrouter peering create -n {vrouter_peering} --peer-asn 10000 --peer-ip 10.0.0.0 -g {rg} --vrouter-name {vrouter}', checks=[
            self.check('name', '{vrouter_peering}')
        ])

        self.cmd('network vrouter peering update -n {vrouter_peering} --peer-asn 11000 --peer-ip 11.0.0.0 -g {rg} --vrouter-name {vrouter}', checks=[
            self.check('peerAsn', '11000'),
            self.check('peerIp', '11.0.0.0')
        ])

        self.cmd('network vrouter peering show -n {vrouter_peering} -g {rg} --vrouter-name {vrouter}', checks=[
            self.check('name', '{vrouter_peering}')
        ])

        self.cmd('network vrouter peering list -g {rg} --vrouter-name {vrouter}', checks=[
            self.check('@[0].name', '{vrouter_peering}'),
            self.check('length(@)', 1)
        ])

        self.cmd('network vrouter peering delete -n {vrouter_peering} -g {rg} --vrouter-name {vrouter}')

        self.cmd('network vrouter delete -g {rg} -n {vrouter}')

    # @record_only()  # this feature need resource from service team for now.
    @unittest.skip('rg not found')
    @ResourceGroupPreparer(name_prefix='cli_test_virtual_router', location='eastus2euap')
    def test_vrouter_with_virtual_hub_support(self, resource_group, resource_group_location):
        self.kwargs.update({
            'rg': 'test_vrouter_with_virtual_hub_support',    # the subscription needs to be a specified one given by service team
            'location': resource_group_location,
            'vnet': 'vnet2',
            'subnet1': 'subnet1',
            'subnet2': 'subnet2',
            'vrouter': 'vrouter2',
            'peer': 'peer1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} '
                 '--location {location} '
                 '--subnet-name {subnet1} '
                 '--address-prefix 10.0.0.0/24')

        # a cleanup program runs in short peoridically to assign subnets a NSG within that subscription
        # which will block subnet is assigned to the virtual router
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet1} --remove networkSecurityGroup')
        vnet = self.cmd('network vnet show -g {rg} -n {vnet}').get_output_in_json()

        self.kwargs.update({
            'subnet1_id': vnet['subnets'][0]['id']
        })

        self.cmd('network vrouter create -g {rg} -l {location} -n {vrouter} --hosted-subnet {subnet1_id}', checks=[
            self.check('type', 'Microsoft.Network/virtualHubs'),
            self.check('ipConfigurations', None),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('network vrouter list -g {rg}')

        self.cmd('network vrouter show -g {rg} -n {vrouter}', checks=[
            self.check('virtualRouterAsn', 65515),
            self.check('length(virtualRouterIps)', 2),
        ])

        self.cmd('network vrouter peering create -g {rg} --vrouter-name {vrouter} -n {peer} '
                 '--peer-asn 11000 --peer-ip 10.0.0.120')

        self.cmd('network vrouter peering list -g {rg} --vrouter-name {vrouter}')

        self.cmd('network vrouter peering show -g {rg} --vrouter-name {vrouter} -n {peer}')

        # unable to update unless the ASN's range is required
        # self.cmd('network vrouter peering update -g {rg} --vrouter-name {vrouter} -n {peer} --peer-ip 10.0.0.0')

        self.cmd('network vrouter peering delete -g {rg} --vrouter-name {vrouter} -n {peer}')

        self.cmd('network vrouter delete -g {rg} -n {vrouter}')


class NetworkVirtualHubRouter(ScenarioTest):

    # @unittest.skip('CannotDeleteVirtualHubWhenItIsInUse')
    @ResourceGroupPreparer(name_prefix='cli_test_virtual_hub_router', location='centraluseuap')
    def test_network_virtual_hub_router_scenario(self, resource_group, resource_group_location):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'vnet': 'vnet2',
            'vhr_ip1': 'vhrip1',
            'subnet1': 'RouteServerSubnet',
            'vrouter': 'vrouter2',
            'peer': 'peer1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} '
                 '--location {location} '
                 '--subnet-name {subnet1} '
                 '--address-prefix 10.0.0.0/24')

        # a cleanup program runs in short peoridically to assign subnets a NSG within that subscription
        # which will block subnet is assigned to the virtual router
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet1} --remove networkSecurityGroup')
        vnet = self.cmd('network vnet show -g {rg} -n {vnet}').get_output_in_json()
        self.cmd('network public-ip create -g {rg} -n {vhr_ip1}')

        self.kwargs.update({
            'subnet1_id': vnet['subnets'][0]['id']
        })

        self.cmd('network routeserver create -g {rg} -l {location} -n {vrouter} '
                 '--hosted-subnet {subnet1_id} --public-ip-address {vhr_ip1}',
                 checks=[
                     self.check('type', 'Microsoft.Network/virtualHubs'),
                     self.check('ipConfigurations', None),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('network routeserver update -g {rg} --name {vrouter}  --allow-b2b-traffic', checks=[
            self.check('allowBranchToBranchTraffic', True)
        ])

        self.cmd('network routeserver list -g {rg}')

        self.cmd('network routeserver show -g {rg} -n {vrouter}', checks=[
            self.check('virtualRouterAsn', 65515),
            self.check('length(virtualRouterIps)', 2),
        ])

        self.cmd('network routeserver peering create -g {rg} --routeserver {vrouter} -n {peer} '
                 '--peer-asn 11000 --peer-ip 10.0.0.120')

        self.cmd('network routeserver peering list -g {rg} --routeserver {vrouter}')

        self.cmd('network routeserver peering show -g {rg} --routeserver {vrouter} -n {peer}')

        self.cmd('network routeserver peering list-advertised-routes -g {rg} --routeserver {vrouter} -n {peer}')

        self.cmd('network routeserver peering list-learned-routes -g {rg} --routeserver {vrouter} -n {peer}')

        # unable to update unless the ASN's range is required
        # self.cmd('network routeserver peering update -g {rg} --routeserver {vrouter} -n {peer} --peer-ip 10.0.0.0')

        self.cmd('network routeserver peering delete -g {rg} --routeserver {vrouter} -n {peer} -y')

        self.cmd('network routeserver delete -g {rg} -n {vrouter} -y')


class NetworkSubnetScenarioTests(ScenarioTest):

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

    @ResourceGroupPreparer(name_prefix='cli_subnet_endpoint_service_test')
    def test_network_subnet_endpoint_service(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1'
        })
        result = self.cmd('network vnet list-endpoint-services -l westus').get_output_in_json()
        self.assertGreaterEqual(len(result), 2)

        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.1.0/24 --service-endpoints Microsoft.Storage',
                 checks=self.check('serviceEndpoints[0].service', 'Microsoft.Storage'))
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints ""',
                 checks=self.check('serviceEndpoints', None))

    @ResourceGroupPreparer(name_prefix='cli_subnet_delegation')
    def test_network_subnet_delegation(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1',
        })
        result = self.cmd('network vnet subnet list-available-delegations -l westcentralus').get_output_in_json()
        self.assertTrue(len(result) > 1, True)
        result = self.cmd('network vnet subnet list-available-delegations -g {rg}').get_output_in_json()
        self.assertTrue(len(result) > 1, True)

        self.cmd('network vnet create -g {rg} -n {vnet} -l westcentralus')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.0.0/24 --delegations Microsoft.Web.serverFarms', checks=[
            self.check('delegations[0].serviceName', 'Microsoft.Web/serverFarms')
        ])
        # verify the update command, and that CLI validation will accept either serviceName or Name
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --delegations Microsoft.Sql/managedInstances',
                 checks=self.check('delegations[0].serviceName', 'Microsoft.Sql/managedInstances'))

    @ResourceGroupPreparer(name_prefix='test_subnet_with_private_endpoint_option')
    def test_subnet_with_private_endpoint_and_private_Link_options(self, resource_group):
        self.kwargs.update({
            'vnet': 'MyVnet',
            'subnet1': 'MySubnet1',
            'subnet2': 'MySubnet2',
            'subnet3': 'MySubnet3',
        })

        self.cmd('network vnet create -g {rg} -n {vnet}')

        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} '
                 '--address-prefixes 10.0.1.0/24 '
                 '--name {subnet1} '
                 '--disable-private-endpoint-network-policies true', checks=[
                     self.check('addressPrefix', '10.0.1.0/24'),
                     self.check('privateEndpointNetworkPolicies', 'Disabled'),
                     self.check('privateLinkServiceNetworkPolicies', 'Enabled')
                 ])

        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} '
                 '--address-prefixes 10.0.2.0/24 '
                 '--name {subnet2} '
                 '--disable-private-link-service-network-policies true', checks=[
                     self.check('addressPrefix', '10.0.2.0/24'),
                     self.check('privateEndpointNetworkPolicies', 'Enabled'),
                     self.check('privateLinkServiceNetworkPolicies', 'Disabled')
                 ])

        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} '
                 '--address-prefixes 10.0.3.0/24 '
                 '--name {subnet3} '
                 '--disable-private-endpoint-network-policies true '
                 '--disable-private-link-service-network-policies true', checks=[
                     self.check('addressPrefix', '10.0.3.0/24'),
                     self.check('privateEndpointNetworkPolicies', 'Disabled'),
                     self.check('privateLinkServiceNetworkPolicies', 'Disabled')
                 ])


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

    def __init__(self, method_name):
        self.sas_replacer = StorageAccountSASReplacer()
        super(NetworkActiveActiveVnetScenarioTest, self).__init__(method_name, recording_processors=[
            self.sas_replacer
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_active_active_vnet_vnet_connection')
    @StorageAccountPreparer(name_prefix='clitestvpncnn')
    def test_network_active_active_vnet_connection(self, resource_group, storage_account):
        from datetime import datetime, timedelta
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
            'conn21': 'vnet2to1',
            'bgp_peer1': '10.52.255.253',
            'bgp_peer2': '10.53.255.253',
            'storage_account': storage_account,
            'ctn': self.create_random_name(prefix='clitestvpngw', length=24),
            'expiry': (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%dT%H:%MZ')
        })

        self.cmd('storage container create --account-name {storage_account} --name {ctn}')
        sas = self.cmd(
            'storage blob generate-sas -n src --account-name {storage_account} -c {ctn} --permissions acrwd --expiry {expiry} -otsv').output.strip()
        self.kwargs['sas_url'] = 'https://{}.blob.azure.com/{}?{}'.format(self.kwargs['storage_account'],
                                                                          self.kwargs['ctn'], sas)
        self.sas_replacer.add_sas_token(sas)

        # Create one VNet with two public IPs
        self.cmd('network vnet create -g {rg} -n {vnet1} --address-prefix {vnet1_prefix} --subnet-name {subnet} --subnet-prefix {gw1_prefix}')
        self.cmd('network public-ip create -g {rg} -n {gw1_ip1}')
        self.cmd('network public-ip create -g {rg} -n {gw1_ip2}')

        # Create second VNet with two public IPs
        self.cmd('network vnet create -g {rg} -n {vnet2} --address-prefix {vnet2_prefix} --subnet-name {subnet} --subnet-prefix {gw2_prefix}')
        self.cmd('network public-ip create -g {rg} -n {gw2_ip1}')
        self.cmd('network public-ip create -g {rg} -n {gw2_ip2}')

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1} --sku HighPerformance --asn {vnet1_asn} --public-ip-addresses {gw1_ip1} {gw1_ip2} --bgp-peering-address {bgp_peer1} --no-wait')
        self.cmd('network vnet-gateway create -g {rg} -n {gw2} --vnet {vnet2} --sku HighPerformance --asn {vnet2_asn} --public-ip-addresses {gw2_ip1} {gw2_ip2} --bgp-peering-address {bgp_peer2} --no-wait')

        # wait for gateway completion to finish
        self.cmd('network vnet-gateway wait -g {rg} -n {gw1} --created')
        self.cmd('network vnet-gateway wait -g {rg} -n {gw2} --created')

        # create and connect the VNet gateways
        self.cmd('network vpn-connection create -g {rg} -n {conn12} --vnet-gateway1 {gw1} --vnet-gateway2 {gw2} --shared-key {key} --enable-bgp')
        self.cmd('network vpn-connection create -g {rg} -n {conn21} --vnet-gateway1 {gw2} --vnet-gateway2 {gw1} --shared-key {key} --enable-bgp')
        self.cmd('network vpn-connection list-ike-sas -g {rg} -n {conn12}')
        output = self.cmd('network vpn-connection packet-capture start -g {rg} -n {conn12}').output.strip()
        self.assertTrue('Successful' in output, 'Expected Successful in output.\nActual: {}'.format(output))
        # currently we cannot create traffic by cli command. So it will return an error when stop.
        with self.assertRaisesRegex(HttpResponseError, 'The response did not contain any data'):
            self.cmd('network vpn-connection packet-capture stop -g {rg} -n {conn12} --sas-url {sas_url}')


class NetworkVpnGatewayScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        self.sas_replacer = StorageAccountSASReplacer()
        super(NetworkVpnGatewayScenarioTest, self).__init__(method_name, recording_processors=[
            self.sas_replacer
        ])

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
            'ip3': 'pubip3',
            'custom_routes1': "101.168.0.6/32",
            'custom_routes2': "102.168.0.6/32"
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

        with self.assertRaisesRegex(CLIError, 'vpn_gateway_generation should not be provided if gateway_type is not Vpn.'):
            self.cmd(
                'network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1_id} --public-ip-address {ip1} --gateway-type ExpressRoute --vpn-gateway-generation Generation1')

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1_id} --public-ip-address {ip1} --vpn-gateway-generation Generation1 --custom-routes {custom_routes1} --no-wait')
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
            self.check('vpnGatewayGeneration', 'Generation1'),
            self.check('enableBgp', False),
            self.check('customRoutes.addressPrefixes[0]', self.kwargs['custom_routes1'])
        ])

        self.cmd('network vnet-gateway update -g {rg} -n {gw1} --sku Standard --custom-routes {custom_routes1} {custom_routes2}', checks=[
            self.check('length(customRoutes.addressPrefixes)', 2)
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
        self.cmd('network vpn-connection list -g {rg} --vnet-gateway {gw1}', checks=[
            self.check('length(@)', 1)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_gateway_aad_')
    def test_network_vpn_gateway_aad(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet',
            'gw': 'gw',
            'ip': 'ip',
            'aad_tenant': 'https://login.microsoftonline.com/0ab2c4f4-81e6-44cc-a0b2-b3a47a1443f4',
            'aad_issuer': 'https://sts.windows.net/0ab2c4f4-81e6-44cc-a0b2-b3a47a1443f4/',
            'aad_audience': 'a21fce82-76af-45e6-8583-a08cb3b956f9'
        })

        self.cmd('network public-ip create -g {rg} -n {ip} ')
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network vnet-gateway create -g {rg} -n {gw} '
                 '--vnet {vnet} --public-ip-address {ip} '
                 '--gateway-type Vpn --vpn-type RouteBased '
                 '--sku VpnGw1 '
                 '--client-protocol OpenVPN '
                 '--address-prefixes 201.169.0.0/16 ')
        self.cmd('network vnet-gateway show -g {rg} -n {gw}', checks=[
            self.check('sku.name', 'VpnGw1'),
            self.check('enableBgp', False),
            self.check('vpnType', 'RouteBased'),
            self.check('vpnClientConfiguration.vpnClientProtocols[0]', "OpenVPN")
        ])

        self.cmd('network vnet-gateway aad assign -g {rg} --gateway-name {gw} '
                 '--tenant {aad_tenant} '
                 '--audience {aad_audience} '
                 '--issuer {aad_issuer} ')
        self.cmd('network vnet-gateway show -g {rg} -n {gw}', checks=[
            self.check('vpnClientConfiguration.aadTenant', self.kwargs['aad_tenant']),
            self.check('vpnClientConfiguration.aadIssuer', self.kwargs['aad_issuer']),
            self.check('vpnClientConfiguration.aadAudience', self.kwargs['aad_audience'])
        ])
        self.cmd('network vnet-gateway aad show -g {rg} --gateway-name {gw}', checks=[
            self.check('aadTenant', self.kwargs['aad_tenant'])
        ])

        self.cmd('network vnet-gateway aad remove -g {rg} --gateway-name {gw}').get_output_in_json()
        self.cmd('network vnet-gateway aad show -g {rg} --gateway-name {gw}', checks=[
            self.check('aadTenant', None),
            self.check('aadIssuer', None),
            self.check('aadAudience', None)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vpn_gateway_disconnect_connects_')
    def test_network_vpn_gateway_disconnect_connects(self, resource_group):
        self.kwargs.update({
            'vnet1': 'myvnet1',
            'vnet2': 'myvnet2',
            'gw1': 'gateway1',
            'gw2': 'gateway2',
            'ip1': 'pubip1',
            'ip2': 'pubip2',
        })

        self.cmd('network public-ip create -n {ip1} -g {rg}')
        self.cmd('network public-ip create -n {ip2} -g {rg}')
        self.cmd('network vnet create -g {rg} -n {vnet1} --subnet-name GatewaySubnet --address-prefix 10.0.0.0/16')
        self.cmd('network vnet create -g {rg} -n {vnet2} --subnet-name GatewaySubnet --address-prefix 10.1.0.0/16')

        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1} --public-ip-address {ip1} '
                 '--vpn-gateway-generation Generation1 --address-prefixes 201.169.0.0/16 --no-wait')
        self.cmd('network vnet-gateway create -g {rg} -n {gw2} --vnet {vnet2} --public-ip-address {ip2} '
                 '--vpn-gateway-generation Generation1 --no-wait')

        self.cmd('network vnet-gateway wait -g {rg} -n {gw1} --created')
        self.cmd('network vnet-gateway wait -g {rg} -n {gw2} --created')

        self.kwargs.update({
            'conn12': 'conn1to2',
            'conn21': 'conn2to1',
        })

        self.cmd('network vpn-connection create -n {conn12} -g {rg} --shared-key 123 '
                 '--vnet-gateway1 {gw1} --vnet-gateway2 {gw2}')
        self.cmd('network vpn-connection create -n {conn21} -g {rg} --shared-key 123 '
                 '--vnet-gateway2 {gw1} --vnet-gateway1 {gw2}')
        self.cmd('network vnet-gateway disconnect-vpn-connections -g {rg} -n {gw1} --vpn-connections {conn12}')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vpn_gateway_package_capture', location='westus')
    @StorageAccountPreparer(name_prefix='clitestvpngw')
    def test_network_vpn_gateway_package_capture(self, resource_group, storage_account):
        from datetime import datetime, timedelta
        self.kwargs.update({
            'vnet1': 'myvnet1',
            'gw1': 'gateway1',
            'gw1_sku': 'Standard',
            'ip1': 'pubip1',
            'storage_account': storage_account,
            'ctn': self.create_random_name(prefix='clitestvpngw', length=24),
            'expiry': (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%dT%H:%MZ')
        })

        self.cmd('storage container create --account-name {storage_account} --name {ctn}')
        sas = self.cmd(
            'storage blob generate-sas -n src --account-name {storage_account} -c {ctn} --permissions acrwd --expiry {expiry} -otsv').output.strip()
        self.kwargs['sas_url'] = 'https://{}.blob.azure.com/{}?{}'.format(self.kwargs['storage_account'],
                                                                          self.kwargs['ctn'], sas)
        self.sas_replacer.add_sas_token(sas)

        self.cmd('network public-ip create -n {ip1} -g {rg}')
        self.cmd('network vnet create -g {rg} -n {vnet1} --subnet-name GatewaySubnet --address-prefix 10.0.0.0/16 --subnet-prefix 10.0.0.0/24')
        self.cmd('network vnet-gateway create -g {rg} -n {gw1} --vnet {vnet1} --public-ip-address {ip1} --sku {gw1_sku}')
        output = self.cmd('network vnet-gateway packet-capture start -g {rg} -n {gw1}').output.strip()
        self.assertTrue('Successful' in output, 'Expected Successful in output.\nActual: {}'.format(output))
        # currently we cannot create traffic by cli command. So it will return an error when stop.
        with self.assertRaisesRegex(HttpResponseError, 'The response did not contain any data'):
            self.cmd('network vnet-gateway packet-capture stop -g {rg} -n {gw1} --sas-url {sas_url}')


class NetworkVpnClientPackageScenarioTest(ScenarioTest):

    @ResourceGroupPreparer('cli_test_vpn_client_package')
    def test_vpn_client_package(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1',
            'public_ip': 'pip1',
            'gateway_prefix': '100.1.1.0/24',
            'gateway': 'vgw1',
            'gw_sku': 'Standard',
            'cert': 'cert1',
            'cert_path': os.path.join(TEST_DIR, 'test-vpn-client-package-root-cert.cer')
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n {public_ip}')
        self.cmd('network vnet-gateway create -g {rg} -n {gateway} --address-prefix {gateway_prefix} --vnet {vnet} --public-ip-address {public_ip} --sku {gw_sku}')
        self.cmd('network vnet-gateway root-cert create -g {rg} --gateway-name {gateway} -n {cert} --public-cert-data "{cert_path}"')

        # test vnet-gateway revoked-cert create
        # self.cmd('network vnet-gateway update -g {rg} -n {vg} --address-prefixes 40.1.0.0/24')
        self.cmd('network vnet-gateway revoked-cert create -g {rg} -n MyCer --gateway-name {gateway} --thumbprint e806da0b7fe24f47e76fa269dc4ed76dac4b39d0')

        # test vnet-gateway revoked-cert delete
        self.cmd('network vnet-gateway revoked-cert delete -g {rg} -n MyCer --gateway-name {gateway}')

        output = self.cmd('network vnet-gateway vpn-client generate -g {rg} -n {gateway}').get_output_in_json()
        self.assertTrue('.zip' in output, 'Expected ZIP file in output.\nActual: {}'.format(str(output)))
        output = self.cmd('network vnet-gateway vpn-client show-url -g {rg} -n {gateway}').get_output_in_json()
        self.assertTrue('.zip' in output, 'Expected ZIP file in output.\nActual: {}'.format(str(output)))
        self.cmd('network vnet-gateway vpn-client ipsec-policy set -g {rg} -n {gateway} --ike-encryption AES256 --ike-integrity SHA384 --dh-group DHGroup24 --ipsec-encryption GCMAES256 --ipsec-integrity GCMAES256 --pfs-group PFS24 --sa-lifetime 7200 --sa-max-size 2048')
        self.cmd('network vnet-gateway vpn-client ipsec-policy show -g {rg} -n {gateway}', checks=[
            self.check('dhGroup', 'DHGroup24'),
            self.check('ikeEncryption', 'AES256'),
            self.check('ikeIntegrity', 'SHA384'),
            self.check('ipsecEncryption', 'GCMAES256'),
            self.check('ipsecIntegrity', 'GCMAES256'),
            self.check('pfsGroup', 'PFS24'),
            self.check('saDataSizeKilobytes', 2048),
            self.check('saLifeTimeSeconds', 7200),
        ])


class NetworkTrafficManagerScenarioTest(ScenarioTest):

    @ResourceGroupPreparer('cli_test_traffic_manager')
    def test_network_traffic_manager(self, resource_group):

        self.kwargs.update({
            'tm': 'mytmprofile',
            'endpoint': 'myendpoint',
            'dns': 'mytrafficmanager001100a'
        })

        self.cmd('network traffic-manager profile check-dns -n myfoobar1')
        self.cmd('network traffic-manager profile create -n {tm} -g {rg} --routing-method priority --unique-dns-name {dns} --tags foo=doo',
                 checks=self.check('TrafficManagerProfile.trafficRoutingMethod', 'Priority'))
        self.cmd('network traffic-manager profile show -g {rg} -n {tm}',
                 checks=self.check('dnsConfig.relativeName', '{dns}'))
        self.cmd('network traffic-manager profile update -n {tm} -g {rg} --routing-method weighted --tags foo=boo',
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

        # test show-geographic-hierarchy
        self.cmd('network traffic-manager endpoint show-geographic-hierarchy', checks=[
            self.check('type', 'Microsoft.Network/trafficManagerGeographicHierarchies')
        ])

        # ensure a profile with endpoints can be updated
        self.cmd('network traffic-manager profile update -n {tm} -g {rg}')

        self.cmd('network traffic-manager endpoint delete -g {rg} --profile-name {tm} -t externalEndpoints -n {endpoint}')
        self.cmd('network traffic-manager endpoint list -g {rg} --profile-name {tm} -t externalEndpoints',
                 checks=self.check('length(@)', 0))

        self.cmd('network traffic-manager profile delete -g {rg} -n {tm}')

    @ResourceGroupPreparer('cli_test_traffic_manager2')
    def test_network_traffic_manager2(self, resource_group):
        self.kwargs.update({
            'tm': 'mytmprofile2',
            'dns': 'mytrafficmanager001100a2'
        })
        self.cmd('network traffic-manager profile create -n {tm} -g {rg} --routing-method Multivalue --unique-dns-name {dns} --max-return 3 --tags foo=doo',
                 checks=self.check('TrafficManagerProfile.trafficRoutingMethod', 'MultiValue'))

        self.cmd('network traffic-manager profile update -n {tm} -g {rg} --routing-method MultiValue  --max-return 4 --tags foo=boo',
                 checks=self.check('maxReturn', 4))

    @ResourceGroupPreparer('cli_test_traffic_manager_subnet')
    def test_network_traffic_manager_subnet_routing(self, resource_group):

        self.kwargs.update({
            'tm': 'tm1',
            'endpoint': 'ep1',
            'dns': self.create_random_name('testtm', 20),
            'pip': 'ip1',
            'ip_dns': self.create_random_name('testpip', 20)
        })

        self.cmd('network traffic-manager profile create -n {tm} -g {rg} --routing-method subnet --unique-dns-name {dns} --custom-headers foo=bar --status-code-ranges 200-202', checks=[
            self.check('TrafficManagerProfile.monitorConfig.expectedStatusCodeRanges[0].min', 200),
            self.check('TrafficManagerProfile.monitorConfig.expectedStatusCodeRanges[0].max', 202),
            self.check('TrafficManagerProfile.monitorConfig.customHeaders[0].name', 'foo'),
            self.check('TrafficManagerProfile.monitorConfig.customHeaders[0].value', 'bar')
        ])
        self.kwargs['ip_id'] = self.cmd('network public-ip create -g {rg} -n {pip} --dns-name {ip_dns} --query publicIp.id').get_output_in_json()
        self.cmd('network traffic-manager profile update -n {tm} -g {rg} --status-code-ranges 200-204 --custom-headers foo=doo test=best', checks=[
            self.check('monitorConfig.expectedStatusCodeRanges[0].min', 200),
            self.check('monitorConfig.expectedStatusCodeRanges[0].max', 204),
            self.check('monitorConfig.customHeaders[0].name', 'foo'),
            self.check('monitorConfig.customHeaders[0].value', 'doo'),
            self.check('monitorConfig.customHeaders[1].name', 'test'),
            self.check('monitorConfig.customHeaders[1].value', 'best')
        ])

        # Endpoint tests
        self.cmd('network traffic-manager endpoint create -n {endpoint} --profile-name {tm} -g {rg} --type azureEndpoints --target-resource-id {ip_id} --subnets 10.0.0.0 --custom-headers test=best', checks=[
            self.check('customHeaders[0].name', 'test'),
            self.check('customHeaders[0].value', 'best'),
            self.check('subnets[0].first', '10.0.0.0')
        ])
        self.cmd('network traffic-manager endpoint update -n {endpoint} --type azureEndpoints --profile-name {tm} -g {rg} --subnets 10.0.0.0:24', checks=[
            self.check('subnets[0].first', '10.0.0.0'),
            self.check('subnets[0].scope', '24')
        ])
        self.cmd('network traffic-manager endpoint update -n {endpoint} --type azureEndpoints --profile-name {tm} -g {rg} --subnets 10.0.0.0-11.0.0.0', checks=[
            self.check('subnets[0].first', '10.0.0.0'),
            self.check('subnets[0].last', '11.0.0.0')
        ])


class NetworkWatcherConfigureScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_nw', location='westcentralus')
    def test_network_watcher_configure(self, resource_group):
        self.cmd('network watcher configure -g {rg} --locations westus westus2 westcentralus eastus canadaeast --enabled')
        self.cmd('network watcher configure --locations westus westus2 eastus canadaeast --tags foo=doo')
        self.cmd('network watcher configure -l westus2 --enabled false')
        self.cmd('network watcher list')



class NetworkWatcherScenarioTest(ScenarioTest):
    from unittest import mock

    def _mock_thread_count(self):
        return 1

    @mock.patch('azure.cli.command_modules.vm._actions._get_thread_count', _mock_thread_count)
    @ResourceGroupPreparer(name_prefix='cli_test_nw_vm', location='westus')
    @AllowLargeResponse()
    def test_network_watcher_vm(self, resource_group, resource_group_location):

        self.kwargs.update({
            'loc': 'westcentralus',
            'vm': 'vm1',
            'nsg': 'nsg1',
            'capture': 'capture1',
            'private-ip': '10.0.0.9'
        })

        vm = self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --authentication-type password --admin-username deploy --admin-password PassPass10!) --nsg {nsg} --nsg-rule None --private-ip-address {private-ip}').get_output_in_json()
        self.kwargs['vm_id'] = vm['id']
        self.cmd('vm extension set -g {rg} --vm-name {vm} -n NetworkWatcherAgentLinux --publisher Microsoft.Azure.NetworkWatcher')

        self.cmd('network watcher test-connectivity -g {rg} --source-resource {vm} --dest-address www.microsoft.com --dest-port 80 --valid-status-codes 200 202')
        self.cmd('network watcher run-configuration-diagnostic --resource {vm_id} --direction Inbound --protocol TCP --source 12.11.12.14 --destination 10.1.1.4 --port 12100')
        self.cmd('network watcher show-topology -g {rg}')
        self.cmd('network watcher test-ip-flow -g {rg} --vm {vm} --direction inbound --local {private-ip}:22 --protocol tcp --remote 100.1.2.3:*')
        self.cmd('network watcher test-ip-flow -g {rg} --vm {vm} --direction outbound --local {private-ip}:* --protocol tcp --remote 100.1.2.3:80')
        self.cmd('network watcher show-security-group-view -g {rg} --vm {vm}')
        self.cmd('network watcher show-next-hop -g {rg} --vm {vm} --source-ip 10.0.0.9 --dest-ip 10.0.0.6')

    @ResourceGroupPreparer(name_prefix='cli_test_nw_flow_log', location='westus')
    @StorageAccountPreparer(name_prefix='clitestnw', location='westus', kind='StorageV2')
    def test_network_watcher_flow_log(self, resource_group, resource_group_location, storage_account):

        self.kwargs.update({
            'loc': resource_group_location,
            'nsg': 'nsg1',
            'sa': storage_account,
            'ws': self.create_random_name('testws', 20),
            'la_prop_path': os.path.join(TEST_DIR, 'loganalytics.json')
        })

        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --enabled --retention 5 --storage-account {sa}')
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --retention 0')
        self.cmd('network watcher flow-log show -g {rg} --nsg {nsg}')

        # test traffic-analytics features
        self.cmd('resource create -g {rg} -n {ws} --resource-type Microsoft.OperationalInsights/workspaces -p @"{la_prop_path}"')
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --workspace {ws} --interval 10', checks=[
            # self.check("contains(flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId, '{ws}')", True),
            # self.check("flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.trafficAnalyticsInterval", 10),
            # self.check("flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled", True)
        ])

        self.cmd('network watcher flow-log show -g {rg} --nsg {nsg}', checks=[
            # self.check("contains(flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId, '{ws}')", True),
            # self.check("flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.trafficAnalyticsInterval", 10),
            # self.check("flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled", True)
        ])
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --workspace {ws} --interval 60', checks=[
            # self.check("flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.trafficAnalyticsInterval", 60)
        ])
        self.cmd('network watcher flow-log show -g {rg} --nsg {nsg}', checks=[
            # self.check("flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.trafficAnalyticsInterval", 60)
        ])
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --traffic-analytics false', checks=[
            # self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled', False)
        ])
        self.cmd('network watcher flow-log show -g {rg} --nsg {nsg}', checks=[
            # self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled', False)
        ])
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --workspace ""', checks=[
            # self.check('flowAnalyticsConfiguration', None)
        ])
        self.cmd('network watcher flow-log show -g {rg} --nsg {nsg}', checks=[
            # self.check('flowAnalyticsConfiguration', None)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_nw_flow_log2', location='canadaeast')
    @StorageAccountPreparer(name_prefix='clitestnw', location='canadaeast', kind='StorageV2')
    def test_network_watcher_flow_log2(self, resource_group, resource_group_location, storage_account):

        self.kwargs.update({
            'loc': resource_group_location,
            'nsg': 'nsg1',
            'sa': storage_account
        })

        self.cmd('network watcher configure -g {rg} --locations westus westus2 westcentralus eastus canadaeast --enabled')
        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('network watcher flow-log configure -g {rg} --nsg {nsg} --enabled --retention 5 --storage-account {sa}')

    @mock.patch('azure.cli.command_modules.vm._actions._get_thread_count', _mock_thread_count)
    @ResourceGroupPreparer(name_prefix='cli_test_nw_packet_capture', location='westus')
    @AllowLargeResponse()
    def test_network_watcher_packet_capture(self, resource_group, resource_group_location):

        self.kwargs.update({
            'loc': resource_group_location,
            'vm': 'vm1',
            'capture': 'capture1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --authentication-type password --admin-username deploy --admin-password PassPass10!) --nsg {vm} --nsg-rule None')
        self.cmd('vm extension set -g {rg} --vm-name {vm} -n NetworkWatcherAgentLinux --publisher Microsoft.Azure.NetworkWatcher')

        self.cmd('network watcher packet-capture create -g {rg} --vm {vm} -n {capture} --file-path capture/capture.cap')
        self.cmd('network watcher packet-capture show -l {loc} -n {capture}')
        self.cmd('network watcher packet-capture stop -l {loc} -n {capture}')
        self.cmd('network watcher packet-capture show-status -l {loc} -n {capture}')
        self.cmd('network watcher packet-capture list -l {loc}')
        self.cmd('network watcher packet-capture delete -l {loc} -n {capture}')
        self.cmd('network watcher packet-capture list -l {loc}')

    @ResourceGroupPreparer(name_prefix='cli_test_nw_troubleshooting', location='westcentralus')
    @StorageAccountPreparer(name_prefix='clitestnw', location='westcentralus')
    @AllowLargeResponse()
    def test_network_watcher_troubleshooting(self, resource_group, resource_group_location, storage_account):

        self.kwargs.update({
            'loc': resource_group_location,
            'sa': storage_account
        })

        # set up resource to troubleshoot
        self.cmd('storage container create -n troubleshooting --account-name {sa}')
        sa = self.cmd('storage account show -g {rg} -n {sa}').get_output_in_json()
        self.kwargs['storage_path'] = sa['primaryEndpoints']['blob'] + 'troubleshooting'
        self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name GatewaySubnet')
        self.cmd('network public-ip create -g {rg} -n vgw1-pip')
        self.cmd('network vnet-gateway create -g {rg} -n vgw1 --vnet vnet1 --public-ip-address vgw1-pip --no-wait')

        # test troubleshooting
        self.cmd('network vnet-gateway wait -g {rg} -n vgw1 --created')
        self.cmd('network watcher troubleshooting start --resource vgw1 -t vnetGateway -g {rg} --storage-account {sa} --storage-path {storage_path}')
        self.cmd('network watcher troubleshooting show --resource vgw1 -t vnetGateway -g {rg}')


class ServiceEndpointScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='network_service_endpoint_scenario_test', location='westcentralus')
    def test_network_service_endpoints(self, resource_group, resource_group_location):

        self.kwargs.update({
            'policy': 'policy1',
            'pd_name': 'storage-def',
            'sub': self.get_subscription_id(),
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'loc': resource_group_location
        })

        self.cmd('network service-endpoint list -l {loc}')

        # test policy CRUD
        self.cmd('network service-endpoint policy create -g {rg} -n {policy} --tags test=best',
                 checks=self.check('tags.test', 'best'))
        self.cmd('network service-endpoint policy update -g {rg} -n {policy} --tags test=nest',
                 checks=self.check('tags.test', 'nest'))
        self.cmd('network service-endpoint policy list -g {rg}',
                 checks=self.check('length(@)', 1))
        self.cmd('network service-endpoint policy show -g {rg} -n {policy}',
                 checks=self.check('tags.test', 'nest'))
        self.cmd('network service-endpoint policy delete -g {rg} -n {policy}')
        self.cmd('network service-endpoint policy list -g {rg}',
                 checks=self.check('length(@)', 0))

        # test policy definition CRUD
        self.cmd('network service-endpoint policy create -g {rg} -n {policy} --tags test=best')
        self.cmd('network service-endpoint policy-definition create -g {rg} --policy-name {policy} -n {pd_name} --service Microsoft.Storage --description "Test Def" --service-resources /subscriptions/{sub}', checks=[
            self.check("length(serviceResources)", 1),
            self.check('service', 'Microsoft.Storage'),
            self.check('description', 'Test Def')
        ])
        self.cmd('network service-endpoint policy-definition update -g {rg} --policy-name {policy} -n {pd_name} --description "Better description"',
                 self.check('description', 'Better description'))
        self.cmd('network service-endpoint policy-definition list -g {rg} --policy-name {policy}',
                 checks=self.check('length(@)', 1))
        self.cmd('network service-endpoint policy-definition show -g {rg} --policy-name {policy} -n {pd_name}',
                 checks=self.check('description', 'Better description'))
        self.cmd('network service-endpoint policy-definition delete -g {rg} --policy-name {policy} -n {pd_name}')
        self.cmd('network service-endpoint policy-definition list -g {rg} --policy-name {policy}',
                 checks=self.check('length(@)', 0))

        # create a subnet with the policy
        self.cmd('network service-endpoint policy-definition create -g {rg} --policy-name {policy} -n {pd_name} --service Microsoft.Storage --service-resources /subscriptions/{sub}')
        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.0.0/24 --service-endpoints Microsoft.Storage --service-endpoint-policy {policy}',
                 checks=self.check("contains(serviceEndpointPolicies[0].id, '{policy}')", True))


class NetworkProfileScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_network_profile')
    def test_network_profile(self, resource_group):

        # no e2e scenario without create. Testing path to service only.
        self.cmd('network profile list')
        self.cmd('network profile list -g {rg}')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network profile show -g {rg} -n dummy')
        self.cmd('network profile delete -g {rg} -n dummy -y')


class NetworkServiceAliasesScenarioTest(ScenarioTest):

    @AllowLargeResponse(size_kb=99999)
    @ResourceGroupPreparer(name_prefix='test_network_service_aliases')
    def test_network_service_aliases(self, resource_group):
        self.kwargs.update({
            'rg': resource_group
        })
        self.cmd('network list-service-aliases -l centralus')
        self.cmd('network list-service-aliases -l centralus -g {rg}')

        # test list-service-tags
        self.cmd('network list-service-tags -l centralus')

class NetworkBastionHostScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='test_network_bastion_host')
    def test_network_batsion_host_create(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'vm': 'clivm',
            'vnet': 'vnet',
            'subnet1': 'AzureBastionSubnet',
            'subnet2': 'vmSubnet',
            'ip1': 'ip1',
            'num': 29,
            'bastion': 'clibastion'

        })
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet1}')
        self.cmd('network vnet subnet create -g {rg} -n {subnet2} --vnet-name {vnet} --address-prefixes 10.0.2.0/24')
        self.cmd('network public-ip create -g {rg} -n {ip1} --sku Standard')
        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --vnet-name {vnet} --subnet {subnet2} '
                 '--admin-password TestPassword11!! --admin-username testadmin --authentication-type password --nsg-rule None')
        self.cmd('network bastion create -g {rg} -n {bastion} --vnet-name {vnet} --public-ip-address {ip1} --scale-units {num} --tags a=b', checks=[
            self.check('type', 'Microsoft.Network/bastionHosts'),
            self.check('name', '{bastion}'),
            self.check('scaleUnits', '{num}'),
            self.check('sku.name', 'Standard'),
            self.check('tags.a', 'b')
        ])
        self.cmd('network bastion list')
        self.cmd('network bastion list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network bastion show -g {rg} -n {bastion}', checks=[
            self.check('type', 'Microsoft.Network/bastionHosts'),
            self.check('name', '{bastion}')
        ])
        self.cmd('network bastion delete -g {rg} -n {bastion}')


class NetworkVnetLocalContextScenarioTest(LocalContextScenarioTest):

    @ResourceGroupPreparer()
    def test_network_vnet_local_context(self):
        self.kwargs.update({
            'vnet': self.create_random_name(prefix='vnet-', length=12),
            'subnet': self.create_random_name(prefix='subnet-', length=12)
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}',
                 checks=[self.check('newVNet.name', self.kwargs['vnet'])])
        self.cmd('network vnet show', checks=[
            self.check('name', self.kwargs['vnet'])
        ])
        self.cmd('network vnet subnet show', checks=[
            self.check('name', self.kwargs['subnet'])
        ])
        with self.assertRaises(CLIError):
            self.cmd('network vnet delete')
        with self.assertRaises(CLIError):
            self.cmd('network vnet subnet delete')

        self.cmd('network vnet subnet delete -n {subnet}')
        self.cmd('network vnet delete -n {vnet}')


class NetworkVirtualNetworkGatewayNatRule(ScenarioTest):

    @ResourceGroupPreparer()
    def test_network_vnet_gateway_nat_rule(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'ip': 'ip',
            'ip1': 'ip1',
            'vnet': 'vnet',
            'vnet1': 'vnet1',
            'subnet': 'GatewaySubnet',
            'vg': 'vnet-gateway-name',
            'vg1': 'vnet-gateway-name1',
            'sku': 'VpnGw2',
        })

        # minimal parameters
        self.cmd('network public-ip create -g {rg} -n {ip}')
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.cmd('network vnet-gateway create -g {rg} -n {vg} --vnet {vnet} --public-ip-address {ip}  --sku {sku} '
                 '--nat-rule name=nat internal-mappings=10.4.0.0/24 external-mappings=192.168.21.0/24 ',
                 checks=[self.check('length(vnetGateway.natRules)', 1)])

        # minimal parameters(ip-config-id can only be set when type is Dynamic, and only allowlist sub-ids support Dynamic)
        self.cmd('network public-ip create -g {rg} -n {ip1}')
        self.cmd('network vnet create -g {rg} -n {vnet1} --subnet-name {subnet}')
        self.cmd('network vnet-gateway create -g {rg} -n {vg1} --vnet {vnet1} --public-ip-address {ip1}  --sku {sku} '
                 '--nat-rule name=nat type=Static mode=EgressSnat internal-mappings=10.4.0.0/24 '
                 'external-mappings=192.168.21.0/24',
                 checks=[self.check('length(vnetGateway.natRules)', 1)])

        # test vnet-gateway reset
        self.cmd('network vnet-gateway reset -g {rg} -n {vg}')

    @ResourceGroupPreparer()
    def test_network_vnet_gateway_nat_rule_sub_cmd(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'ip': 'ip',
            'vnet': 'vnet',
            'subnet': 'GatewaySubnet',
            'vg': 'vnet-gateway-name',
            'sku': 'VpnGw2',
            'nat': 'nat-rule-name',
            'nat1': 'nat-rule-name1',
        })

        # minimal parameters
        self.cmd('network public-ip create -g {rg} -n {ip}')
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.cmd('network vnet-gateway create -g {rg} -n {vg} --vnet {vnet} --public-ip-address {ip}  --sku {sku}')

        # sub cmd
        self.cmd('network vnet-gateway nat-rule add -g {rg} --gateway-name {vg} --name {nat} '
                 '--internal-mappings 10.4.0.0/24 --external-mappings 192.168.21.0/24',
                 checks=[self.check('length(natRules)', 1)])

        self.cmd('network vnet-gateway nat-rule add -g {rg} --gateway-name {vg} --name {nat1} '
                 '--internal-mappings 10.3.0.0/24 --external-mappings 192.168.22.0/24',
                 checks=[self.check('length(natRules)', 2)])

        self.cmd('network vnet-gateway nat-rule list -g {rg} --gateway-name {vg} ',
                 checks=[self.check('length(@)', 2)])

        self.cmd('network vnet-gateway nat-rule remove -g {rg} --gateway-name {vg} --name {nat}',
                 checks=[self.check('length(natRules)', 1)])


class NetworkSecurityPartnerProviderScenarioTest(ScenarioTest):
    def __init__(self, method_name, config_file=None, recording_dir=None, recording_name=None, recording_processors=None,
                 replay_processors=None, recording_patches=None, replay_patches=None):
        super(NetworkSecurityPartnerProviderScenarioTest, self).__init__(method_name)
        self.cmd('extension add -n virtual-wan')

    @ResourceGroupPreparer()
    def test_network_security_partner_provider(self, resource_group):
        self.kwargs.update({
            'vwan': 'clitestvwan',
            'vhub': 'clitestvhub',
            'gateway': 'cligateway',
            'name': 'clisecuritypartnerprovider',
            'rg': resource_group
        })

        self.cmd('network vwan create -n {vwan} -g {rg} --type Standard')
        self.cmd('network vhub create -g {rg} -n {vhub} --vwan {vwan}  --address-prefix 10.5.0.0/16 -l westus --sku Standard')
        self.cmd('network vpn-gateway create -g {rg} -n {gateway} --vhub {vhub}')

        self.cmd('network security-partner-provider create -n {name} -g {rg} --vhub {vhub} --provider Checkpoint', checks=[
            self.check('name', '{name}'),
            self.check('securityProviderName', 'Checkpoint')
        ])
        self.cmd('network security-partner-provider show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('securityProviderName', 'Checkpoint')
        ])
        self.cmd('network security-partner-provider update -n {name} -g {rg} --tag a=b', checks=[
            self.check('tags.a', 'b')
        ])
        self.cmd('network security-partner-provider list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network security-partner-provider list', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network security-partner-provider delete -n {name} -g {rg}')


class NetworkVirtualApplianceScenarioTest(ScenarioTest):
    def setUp(self):
        super(NetworkVirtualApplianceScenarioTest, self).setUp()
        self.cmd('extension add -n virtual-wan')

    def tearDown(self):
        # avoid influence other test when parallel run
        # self.cmd('extension remove -n virtual-wan')
        super(NetworkVirtualApplianceScenarioTest, self).tearDown()

    @ResourceGroupPreparer(location='westcentralus', name_prefix='test_network_virtual_appliance')
    def test_network_virtual_appliance(self, resource_group):
        self.kwargs.update({
            'vwan': 'clitestvwan',
            'vhub': 'clitestvhub',
            'name': 'cli-virtual-appliance',
            'site': 'cli-site',
            'blob': 'https://azurecliprod.blob.core.windows.net/cli-extensions/account-0.1.0-py2.py3-none-any.whl',
            'rg': resource_group
        })

        self.cmd('network vwan create -n {vwan} -g {rg} --type Standard')
        self.cmd('network vhub create -g {rg} -n {vhub} --vwan {vwan}  --address-prefix 10.5.0.0/16 --sku Standard')

        self.cmd('network virtual-appliance create -n {name} -g {rg} --vhub {vhub} --vendor "barracudasdwanrelease" '
                 '--scale-unit 2 -v latest --asn 10000 --init-config "echo $abc" '
                 '--boot-blobs {blob} {blob} --cloud-blobs {blob} {blob}',
                 checks=[
                     self.check('name', '{name}'),
                     self.check('length(bootStrapConfigurationBlobs)', 2),
                     self.check('length(cloudInitConfigurationBlobs)', 2),
                     self.check('virtualApplianceAsn', 10000),
                     self.check('cloudInitConfiguration', "echo $abc")
                 ])
        self.cmd('network virtual-appliance update -n {name} -g {rg} --asn 20000 --init-config "echo $abcd"', checks=[
            self.check('virtualApplianceAsn', 20000),
            self.check('cloudInitConfiguration', "echo $abcd")
        ])
        self.cmd('network virtual-appliance show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('length(bootStrapConfigurationBlobs)', 2),
            self.check('length(cloudInitConfigurationBlobs)', 2),
            self.check('virtualApplianceAsn', 20000),
            self.check('cloudInitConfiguration', "echo $abcd")
        ])
        self.cmd('network virtual-appliance list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('network virtual-appliance list', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('network virtual-appliance sku list', checks=[
            self.check('length(@)', 3)
        ])
        self.cmd('network virtual-appliance sku show --name "barracudasdwanrelease"', checks=[
            self.check('name', 'barracudasdwanrelease')
        ])

        self.cmd('network virtual-appliance site create -n {site} -g {rg} --appliance-name {name} --address-prefix 10.0.0.0/24 --allow --default --optimize', checks=[
            self.check('name', '{site}'),
            self.check('o365Policy.breakOutCategories.allow', True),
            self.check('o365Policy.breakOutCategories.default', True),
            self.check('o365Policy.breakOutCategories.optimize', True),
            self.check('addressPrefix', '10.0.0.0/24')
        ])
        self.cmd('network virtual-appliance site update -n {site} -g {rg} --appliance-name {name} --address-prefix 10.0.0.1/24 --allow false --default false --optimize false', checks=[
            self.check('name', '{site}'),
            self.check('o365Policy.breakOutCategories.allow', False),
            self.check('o365Policy.breakOutCategories.default', False),
            self.check('o365Policy.breakOutCategories.optimize', False),
            self.check('addressPrefix', '10.0.0.1/24')
        ])
        self.cmd('network virtual-appliance site show -n {site} -g {rg} --appliance-name {name}', checks=[
            self.check('name', '{site}'),
            self.check('o365Policy.breakOutCategories.allow', False),
            self.check('o365Policy.breakOutCategories.default', False),
            self.check('o365Policy.breakOutCategories.optimize', False),
            self.check('addressPrefix', '10.0.0.1/24')
        ])
        self.cmd('network virtual-appliance site list -g {rg} --appliance-name {name}', checks=[
            # self.check('length(@)', 1)
        ])
        self.cmd('network virtual-appliance site delete -n {site} -g {rg} --appliance-name {name} -y')
        self.cmd('network virtual-appliance delete -n {name} -g {rg} -y')


class NetworkExtendedLocation(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_network_lb_edge_zone', location='eastus2euap')
    def test_network_lb_edge_zone(self, resource_group):

        self.kwargs.update({
            'lb': 'lb',
            'lb1': 'lb1',
            'sku': 'standard',
            'ip': 'pubip1',
            'edge_name': 'microsoftrrdclab1'
        })

        self.cmd('network lb create -g {rg} -n {lb} --sku {sku} --public-ip-address {ip} --edge-zone {edge_name}')
        self.cmd('network lb show -g {rg} -n {lb}', checks=self.check('extendedLocation.name', '{edge_name}'))

        self.cmd('network lb create -g {rg} -n {lb1} --vnet-name vnet1 --subnet subnet1 --edge-zone {edge_name}')

    @ResourceGroupPreparer(name_prefix='test_network_nic_edge_zone', location='eastus2euap')
    def test_network_nic_edge_zone(self, resource_group):

        self.kwargs.update({
            'vnet': 'clitestvnet',
            'nic': 'clitestnic',
            'rg': resource_group,
            'edge_name': 'microsoftrrdclab1'
        })
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name subnet1 --edge-zone {edge_name}',
                 checks=self.check('newVNet.extendedLocation.name', '{edge_name}'))
        self.cmd('network nic create -g {rg} -n {nic} --subnet subnet1 --vnet-name {vnet} --edge-zone {edge_name}',
                 checks=self.check('NewNIC.extendedLocation.name', '{edge_name}'))

    @ResourceGroupPreparer(name_prefix='test_network_public_ip_edge_zone', location='eastus2euap')
    def test_network_public_ip_edge_zone(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'ip1': 'pubip1',
            'edge_name': 'microsoftrrdclab1'
        })

        self.cmd('network public-ip create -g {rg} -n {ip1} --edge-zone {edge_name}',
                 checks=self.check('publicIp.extendedLocation.name', '{edge_name}'))

    @ResourceGroupPreparer(name_prefix='test_network_public_ip_prefix_edge_zone', location='eastus2euap')
    def test_network_public_ip_prefix_edge_zone(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'ip1': 'pubip1-prefix',
            'edge_name': 'microsoftrrdclab1'
        })

        self.cmd('network public-ip prefix create -g {rg} -n {ip1} --length 30 --edge-zone {edge_name}',
                 checks=self.check('extendedLocation.name', '{edge_name}'))

    # @unittest.skip('wait for service ready')
    @ResourceGroupPreparer(name_prefix='test_network_vnet_gateway_edge_zone', location='eastus2euap')
    def test_network_vnet_gateway_edge_zone(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'ip1': 'pubip1',
            'vnet': 'vnet',
            'edge_name': 'microsoftrrdclab1'
        })
        self.cmd('network public-ip create -g {rg} -n {ip1}')
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name GatewaySubnet')
        self.cmd('network vnet-gateway create -g {rg} -n vnet-gateway --vnet {vnet} --public-ip-address {ip1} '
                 '--edge-zone {edge_name}',
                 checks=self.check('vnetGateway.extendedLocation.name', '{edge_name}'))

    @ResourceGroupPreparer(name_prefix='test_network_private_endpoint_edge_zone', location='eastus2euap')
    def test_network_private_endpoint_edge_zone(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'lb': 'lb',
            'vnet': 'vnet',
            'edge_name': 'microsoftrrdclab1',
            'subnet1': 'subnet1',
            'subnet2': 'subnet2',
        })
        self.cmd('network lb create -g {rg} -n {lb} --public-ip-address ip --sku Standard')
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet1} --edge-zone {edge_name}')
        self.cmd('network vnet subnet update -g {rg} -n {subnet1} --vnet-name {vnet} '
                 '--disable-private-link-service-network-policies')
        self.cmd('network vnet subnet create -g {rg} -n {subnet2} --vnet-name {vnet} '
                 '--address-prefixes 10.0.2.0/24')
        self.cmd('network vnet subnet update -g {rg} -n {subnet2} --vnet-name {vnet} '
                 '--disable-private-endpoint-network-policies')

        pls = self.cmd('network private-link-service create -g {rg} -n pls --vnet-name {vnet} --subnet {subnet1} '
                       '--lb-name {lb} --lb-frontend-ip-configs LoadBalancerFrontEnd --edge-zone {edge_name}',
                       checks=self.check('extendedLocation.name', '{edge_name}')).get_output_in_json()
        self.kwargs['pls_id'] = pls['id']
        self.cmd('network private-endpoint create -g {rg} -n pe --vnet-name {vnet} --subnet {subnet2} '
                 '--private-connection-resource-id {pls_id} --connection-name cn --edge-zone {edge_name}',
                 checks=self.check('extendedLocation.name', '{edge_name}'))


class NetworkLoadBalancerWithSkuGateway(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_network_lb_tunnel_interface', location='eastus')
    def test_network_lb_tunnel_interface(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'lb': 'lb',
            'sku': 'Gateway',
            'vnet': 'vnet',
            'subnet': 'subnet',
            'bap': 'backend-address-pool-name',
            'type': 'External',
            'type1': 'Internal',
            'protocol': 'vxlan',
            'identifier': '950',
            'identifier1': '960',
        })

        self.cmd('network lb create -g {rg} -n {lb} --sku {sku} --vnet-name {vnet} --subnet {subnet}')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n {bap} --vnet {vnet}')

        # default
        self.cmd('network lb address-pool tunnel-interface add -g {rg} --lb-name {lb} --address-pool {bap} '
                 '--type {type} --protocol {protocol} --identifier {identifier} --port 15000',
                 checks=self.check('length(tunnelInterfaces)', 2))
        self.cmd('network lb address-pool tunnel-interface list -g {rg} --lb-name {lb} --address-pool {bap}',
                 checks=self.check('length(@)', 2))
        self.cmd('network lb address-pool tunnel-interface remove -g {rg} --lb-name {lb} --address-pool {bap} '
                 '--index 0',
                 checks=self.check('length(tunnelInterfaces)', 1))
        self.cmd('network lb address-pool tunnel-interface update -g {rg} --lb-name {lb} --address-pool {bap} '
                 '--type {type1} --protocol {protocol} --identifier {identifier1} --port 10000 --index 0',
                 checks=self.check('tunnelInterfaces[0].type', '{type1}'))

    @ResourceGroupPreparer(name_prefix='test_network_lb_front_ip', location='eastus')
    def test_network_lb_front_ip(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'lb': 'lb',
            'lb1': 'lb1',
            'vnet': 'vnet',
            'subnet': 'subnet',
            'ip': 'public-ip',
            'ip1': 'public-ip1',
            'fip': 'load-balancer-frontend-end',
            'subnet': 'subnet',
        })

        self.cmd('network lb create -g {rg} -n {lb} --sku Standard --public-ip-address {ip}')
        self.cmd('network lb create -g {rg} -n {lb1} --sku Gateway --vnet-name {vnet} --subnet {subnet} ')
        self.cmd('network public-ip create -g {rg} -n {ip1} --sku standard')
        self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb} -n {fip} --public-ip-address {ip1}',
                 checks=self.not_exists('gatewayLoadBalancer'))
        result = self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb1} -n {fip} '
                          '--vnet-name {vnet} --subnet {subnet}').get_output_in_json()
        # test --gateway-lb
        self.kwargs['id'] = result['id']
        self.cmd('network lb frontend-ip update -g {rg} --lb-name {lb} -n {fip} --gateway-lb {id}',
                 checks=self.exists('gatewayLoadBalancer'))

        self.cmd("network lb frontend-ip update -g {rg} --lb-name {lb} -n {fip} --gateway-lb ''",
                 checks=self.check('gatewayLoadBalancer', None))

    @ResourceGroupPreparer(name_prefix='test_network_nic_front_ip', location='eastus2euap')
    def test_network_nic_front_ip(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'lb': 'lb',
            'vnet': 'vnet',
            'vnet1': 'vnet1',
            'subnet': 'subnet',
            'subnet1': 'subnet1',
            'ip': 'public-ip',
            'ip1': 'public-ip1',
            'fip': 'load-balancer-frontend-end',
            'nic': 'nic-name',
            'nip': 'nic-ip-config-name',
        })

        self.cmd('network public-ip create -g {rg} -n {ip} --sku standard')
        self.cmd('network public-ip create -g {rg} -n {ip1} --sku standard')
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.cmd('network nic create -g {rg} -n {nic} --public-ip-address {ip} --vnet-name {vnet} --subnet {subnet}')
        self.cmd('network lb create -g {rg} -n {lb} --sku Gateway --vnet-name {vnet1} --subnet {subnet1} ')
        result = self.cmd('network lb frontend-ip create -g {rg} --lb-name {lb} -n {fip} '
                          '--vnet-name {vnet1} --subnet {subnet1}').get_output_in_json()
        self.kwargs['id'] = result['id']
        self.cmd('network nic ip-config create -g {rg} --nic-name {nic} -n {nip} --make-primary '
                 '--public-ip-address {ip1}',
                 checks=self.not_exists('gatewayLoadBalancer'))

        # test --gateway-lb
        self.cmd('network nic ip-config update -g {rg} --nic-name {nic} -n {nip} --gateway-lb {id}',
                 checks=self.exists('gatewayLoadBalancer'))

    @ResourceGroupPreparer(name_prefix='test_network_lb_rule_backend_address_pools', location='eastus2euap')
    def test_network_lb_rule_backend_address_pools(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'lb': 'lb',
            'fip': 'LoadBalancerFrontEnd',
            'bap1': 'address-pool-name1',
            'bap2': 'address-pool-name2',
            'bap3': 'address-pool-name3',
            'type': 'External',
            'protocol': 'vxlan',
            'identifier': '901',
            'identifier1': '902',
            'port': '10700',
            'fport': '40',
            'fport1': '60',
            'bport': '60',
            'bport1': '80',
        })

        self.cmd('network lb create -g {rg} -n {lb} --sku Gateway --vnet-name vnet --subnet subnet')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n {bap1}')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n {bap2}')
        self.cmd('network lb address-pool create -g {rg} --lb-name {lb} -n {bap3}')
        self.cmd('network lb address-pool tunnel-interface add -g {rg} --lb-name {lb} --address-pool {bap1} --type {type}  --protocol {protocol} --identifier {identifier}')
        self.cmd('network lb address-pool tunnel-interface update -g {rg} --lb-name {lb} --address-pool {bap2} --type {type} --index 0')
        self.cmd('network lb address-pool tunnel-interface update -g {rg} --lb-name {lb} --address-pool {bap3} --port {port} --identifier {identifier1} --index 0')

        # test --backend-pool-name
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n rule1 --frontend-ip-name {fip} '
                 '--frontend-port {fport}  --protocol tcp --backend-port {bport} --backend-pool-name {bap1} ',
                 checks=[self.exists('backendAddressPool'),
                         self.check('length(backendAddressPools)', 1)])
        # test --backend-pools-name
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n rule2 --frontend-ip-name {fip} '
                 '--frontend-port {fport1} --backend-pools-name {bap3} {bap2} --protocol tcp  --backend-port {bport1}',
                 checks=[self.not_exists('backendAddressPool'),
                         self.check('length(backendAddressPools)', 2)])
        self.cmd('network lb rule update -g {rg} --lb-name {lb} -n rule2 --frontend-ip-name {fip} '
                 '--backend-pools-name {bap1} ',
                 checks=[self.check('length(backendAddressPools)', 1)])


if __name__ == '__main__':
    unittest.main()
