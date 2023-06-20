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
    @KeyVaultPreparer(name_prefix='sfrp-cli-kv-', location='eastasia', additional_params='--enabled-for-deployment --enabled-for-template-deployment')
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
