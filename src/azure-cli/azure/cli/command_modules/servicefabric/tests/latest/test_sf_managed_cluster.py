# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.command_modules.servicefabric.tests.latest.test_util import (
    _add_selfsigned_cert_to_keyvault
)
from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer
from azure.core.exceptions import HttpResponseError


class ServiceFabricManagedClustersTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_basic_cluster(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'tags': "key1=value1 key2=value2"
        })

        cluster = self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password} --tags {tags}',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('clusterState', 'WaitingForNodes')]).get_output_in_json()

        self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary',
                 checks=[self.check('provisioningState', 'Succeeded')])

        # 'InvalidParameter - Cluster must have at least one active primary node type'
        with self.assertRaisesRegex(HttpResponseError, 'Cluster must have at least one active primary node type'):
            self.cmd('az sf managed-node-type delete -g {rg} -c {cluster_name} -n pnt')

        self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}',
                 checks=[self.check('clusterState', 'Ready'),
                 self.check('tags', cluster["tags"])])

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')

    @ResourceGroupPreparer()
    def test_network_security_rule(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'vm_image_sku': '2022-datacenter-azure-edition',
            'vm_size': 'Standard_D2s_v3',
            'tags': "SFRP.DisableDefaultOutboundAccess=True SFRP.EnableDiagnosticMI=True",
            'name': self.create_random_name('NSR-', 10),
            'access': 'allow',
            'inv_access': 'deny',
            'description': self.create_random_name('NSR-description', 30),
            'direction': 'inbound',
            'inv_direction': 'outbound',
            'protocol': 'any',
            'priority': 1200,
            'update_priority': 1100,
            'source_port_ranges': '1-1000 1122-65535',
            'dest_port_ranges': '1-1900 2200-65535',
            'source_addr_prefixes': '167.220.242.0/27 167.220.0.0/23 131.107.132.16/28 167.220.81.128/26',
            'dest_addr_prefixes': '194.69.104.0/25 194.69.119.64/26 167.220.249.128/26 255.255.255.255/32',
            'deny_name': 'deny-nsr',
            'deny_access': 'deny',
            'deny_description': self.create_random_name('NSR-', 10),
            'deny_direction': 'inbound',
            'deny_protocol': 'any',
            'deny_priority': 1300,
            'deny_source_port_range': '*',
            'deny_dest_port_ranges': '19000 19080',
            'deny_source_addr_prefix': 'Internet',
            'deny_dest_addr_prefix': '*',
        })

        cluster = self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password} --tags {tags}',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('clusterState', 'WaitingForNodes')]).get_output_in_json()

        self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary --vm-image-sku {vm_image_sku} --vm-size {vm_size}',
                 checks=[self.check('provisioningState', 'Succeeded')])

        self.cmd('az sf managed-cluster network-security-rule add -g {rg} -c {cluster_name} '
                '--name {deny_name} --access {deny_access} --description {deny_description} --direction {deny_direction} --protocol {deny_protocol} --priority {deny_priority} --source-port-range {deny_source_port_range} --dest-port-ranges {deny_dest_port_ranges}'
                ' --source-addr-prefix {deny_source_addr_prefix} --dest-addr-prefix {deny_dest_addr_prefix}',
                checks=[self.check('provisioningState', 'Succeeded'),
                        self.check('networkSecurityRules[0].destinationAddressPrefix', '*'),
                        self.check('networkSecurityRules[0].sourceAddressPrefix', 'Internet'),
                        self.check('networkSecurityRules[0].protocol', '*'),
                        self.check('networkSecurityRules[0].direction', 'inbound'),
                        self.check('networkSecurityRules[0].access', 'deny'),
                        self.check('networkSecurityRules[0].priority', 1300),
                        self.check('networkSecurityRules[0].sourcePortRange', '*'),
                        self.check('networkSecurityRules[0].destinationPortRanges[0]', '19000'),
                        self.check('networkSecurityRules[0].destinationPortRanges[1]', '19080')])

        self.cmd('az sf managed-cluster network-security-rule add -g {rg} -c {cluster_name} '
                '--name {name} --access {access} --description {description} --direction {direction} --protocol {protocol} --priority {priority} --source-port-ranges {source_port_ranges} --dest-port-ranges {dest_port_ranges}'
                ' --source-addr-prefixes {source_addr_prefixes} --dest-addr-prefixes {dest_addr_prefixes}',
                checks=[self.check('provisioningState', 'Succeeded'),
                        self.check('networkSecurityRules[1].destinationAddressPrefixes[0]', '194.69.104.0/25'),
                        self.check('networkSecurityRules[1].sourceAddressPrefixes[1]', '167.220.0.0/23'),
                        self.check('networkSecurityRules[1].protocol', '*'),
                        self.check('networkSecurityRules[1].direction', 'inbound'),
                        self.check('networkSecurityRules[1].access', 'allow'),
                        self.check('networkSecurityRules[1].priority', 1200),
                        self.check('networkSecurityRules[1].sourcePortRanges[0]', '1-1000'),
                        self.check('networkSecurityRules[1].destinationPortRanges[1]', '2200-65535')])
        
        self.cmd('az sf managed-cluster network-security-rule update -g {rg} -c {cluster_name} '
                '--name {name} --access {inv_access} --direction {inv_direction} --priority {update_priority}',
                checks=[self.check('provisioningState', 'Succeeded'),])
        
        self.cmd('az sf managed-cluster network-security-rule get -g {rg} -c {cluster_name} --name {name}',
                 checks=[self.check('access', 'deny'),
                         self.check('direction', 'outbound'),
                         self.check('priority', 1100)])

        self.cmd('az sf managed-cluster network-security-rule list -g {rg} -c {cluster_name}',
                checks=[self.check('length(@)', 2)])
        
        self.cmd('az sf managed-cluster network-security-rule delete -g {rg} -c {cluster_name} --name {name}',
                checks=[self.check('provisioningState', 'Succeeded')])
        
        self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}',
                checks=[self.check('clusterState', 'Ready'),
                        self.check('length(networkSecurityRules)', 1)])

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')

    @ResourceGroupPreparer()
    def test_node_type_operation(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
        })

        self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password} --sku Standard --upgrade-mode Automatic --upgrade-cadence Wave1',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('clusterState', 'WaitingForNodes'),
                         self.check('clusterUpgradeMode', 'Automatic'),
                         self.check('clusterUpgradeCadence', 'Wave1')])

        self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary --disk-type Premium_LRS --vm-size Standard_DS2',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('dataDiskType', 'Premium_LRS'),
                         self.check('isStateless ', False)])

        self.cmd('az sf managed-node-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(@)', 1)])

        self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n snt --instance-count 6 --is-stateless --multiple-placement-groups',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('dataDiskType', 'StandardSSD_LRS'),
                         self.check('isStateless ', True),
                         self.check('multiplePlacementGroups ', True)])

        self.cmd('az sf managed-node-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(@)', 2)])


        # first operation with retry in case nodes take some time to be ready
        timeout = time.time() + 300
        while True:
            try:
                self.cmd('az sf managed-node-type node restart -g {rg} -c {cluster_name} -n snt --node-name snt_0 snt_1')
                break
            except HttpResponseError:
                if time.time() > timeout:
                    raise
                if self.in_recording or self.is_live:
                    time.sleep(60)

        self.cmd('az sf managed-node-type node delete -g {rg} -c {cluster_name} -n snt --node-name snt_1')

        self.cmd('az sf managed-node-type node reimage -g {rg} -c {cluster_name} -n snt --node-name snt_3')

        self.cmd('az sf managed-node-type delete -g {rg} -c {cluster_name} -n snt')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n snt')

        self.cmd('az sf managed-node-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(@)', 1)])

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')

    @ResourceGroupPreparer()
    @KeyVaultPreparer(name_prefix='sfrp-cli-kv-', location='eastasia', additional_params='--enabled-for-deployment --enabled-for-template-deployment --enable-rbac-authorization false')
    def test_cert_and_ext(self, key_vault, resource_group):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'cert_tp2': '123BDACDCDFB2C7B250192C6078E47D1E1DB7777',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'extName': 'csetest',
            'publisher': 'Microsoft.Compute',
            'extType': 'BGInfo',
            'extVer': '2.1',
            'kv_name': key_vault,
            'cert_name': self.create_random_name('sfrp-cli-', 24)
        })

        self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password}',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('clusterState', 'WaitingForNodes')])

        self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary',
                 checks=[self.check('provisioningState', 'Succeeded')])

        # add extension
        self.cmd('az sf managed-node-type vm-extension add -g {rg} -c {cluster_name} -n pnt '
                 ' --extension-name {extName} --publisher {publisher} --extension-type {extType} --type-handler-version {extVer} --auto-upgrade-minor-version',
                 checks=[self.check('provisioningState', 'Succeeded')])

        self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n pnt',
                 checks=[self.check('length(vmExtensions)', 1)])

        # add secret
        kv = self.cmd('keyvault show -n {kv_name} -g {rg}').get_output_in_json()
        self.kwargs.update({'kv_id': kv['id']})
        cert = _add_selfsigned_cert_to_keyvault(self, self.kwargs)
        cert_secret_id = cert['sid']
        self.kwargs.update({'cert_secret_id': cert_secret_id})

        self.cmd('az sf managed-node-type vm-secret add -g {rg} -c {cluster_name} -n pnt '
                 ' --source-vault-id {kv_id} --certificate-url {cert_secret_id} --certificate-store my',
                 checks=[self.check('provisioningState', 'Succeeded')])

        self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n pnt',
                 checks=[self.check('length(vmSecrets)', 1)])

        # add client cert
        self.cmd('az sf managed-cluster client-certificate add -g {rg} -c {cluster_name} --thumbprint {cert_tp2}',
                 checks=[self.check('provisioningState', 'Succeeded')])

        self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}',
                 checks=[self.check('length(clients)', 2)])

        # delete client cert
        self.cmd('az sf managed-cluster client-certificate delete -g {rg} -c {cluster_name} --thumbprint {cert_tp2}',
                 checks=[self.check('provisioningState', 'Succeeded')])

        self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}',
                 checks=[self.check('length(clients)', 1)])

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')


if __name__ == '__main__':
    unittest.main()
