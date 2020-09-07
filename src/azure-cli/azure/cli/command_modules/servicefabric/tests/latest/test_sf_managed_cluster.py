# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.servicefabric.tests.latest.test_util import _create_cluster_with_separate_kv
from azure.cli.command_modules.servicefabric.tests.latest.test_util import (
    _create_keyvault,
    _add_selfsigned_cert_to_keyvault
)

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer


class ServiceFabricManagedClustersTests(ScenarioTest):
    @ResourceGroupPreparer()
    def basic_cluster_test(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'southcentralus',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9)
        })

        self.cmd('az sf managed-cluster list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 0)])

        cluster = self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password}',
                           checks=[self.check('provisioningState', 'Succeeded'),
                                   self.check('clusterState', 'WaitingForNodes')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        # SystemExit 1 'InvalidParameter - Cluster must have at least one active primary node type'
        with self.assertRaisesRegexp(SystemExit, '1'):
            self.cmd('az sf application-type delete -g {rg} -c {cluster_name} -n pnt')

        cluster = self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}',
                           checks=[self.check('clusterState', 'Deploying')]).get_output_in_json()

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')

    @ResourceGroupPreparer()
    def node_type_operation_test(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'southcentralus',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9)
        })
        self.cmd('az sf managed-cluster list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 0)])
        cluster = self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password} --sku Standard',
                           checks=[self.check('provisioningState', 'Succeeded'),
                                   self.check('clusterState', 'WaitingForNodes')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        self.cmd('az sf managed-node-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 1)])

        nodeType = self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n snt --instance-count 6',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        self.cmd('az sf managed-node-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 2)])

        self.cmd('az sf managed-node-type node restart -g {rg} -c {cluster_name} -n snt --node-name snt_0 snt_1')

        self.cmd('az sf managed-node-type node delete -g {rg} -c {cluster_name} -n snt --node-name snt_1')

        self.cmd('az sf managed-node-type node reimage -g {rg} -c {cluster_name} -n snt --node-name snt_3')

        self.cmd('az sf managed-node-type delete -g {rg} -c {cluster_name} -n snt')

        # SystemExit 3 'not found'
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n snt')

        self.cmd('az sf managed-node-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 1)])

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')

    @ResourceGroupPreparer()
    def cert_and_ext_test(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'cert_tp2': '123BDACDCDFB2C7B250192C6078E47D1E1DB7777',
            'loc': 'southcentralus',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'extName': 'csetest',
            'publisher': 'Microsoft.Compute',
            'extType': 'BGInfo',
            'extVer': '2.1',
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'cert_name': self.create_random_name('sfrp-cli-', 24)
        })

        self.cmd('az sf managed-cluster list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 0)])
        cluster = self.cmd('az sf managed-cluster create -g {rg} -c {cluster_name} -l {loc} --cert-thumbprint {cert_tp} --cert-is-admin --admin-password {vm_password}',
                           checks=[self.check('provisioningState', 'Succeeded'),
                                   self.check('clusterState', 'WaitingForNodes')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type create -g {rg} -c {cluster_name} -n pnt --instance-count 5 --primary',
                            checks=[self.check('vmExtensions', 'Succeeded')]).get_output_in_json()

        # add extension
        nodeType = self.cmd('az sf managed-node-type vm-extension add -g {rg} -c {cluster_name} -n pnt '
                            ' --extension-name {extName} --publisher {publisher} --extension-type {extType} --type-handler-version {extVer}',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n pnt',
                            checks=[self.check('length(vmExtensions)', 1)).get_output_in_json()

        #add secret
        kv = _create_keyvault(self, self.kwargs)
        kwargs.update({'kv_id': kv.id})
        cert = _add_selfsigned_cert_to_keyvault(self, self.kwargs)
        cert_secret_id = cert['sid']
        kwargs.update({'cert_secret_id': cert_secret_id})

        nodeType = self.cmd('az sf managed-node-type vm-secret add -g {rg} -c {cluster_name} -n pnt '
                            ' --thumbprint {extName} --publisher {publisher} --extension-type {extType} --type-handler-version {extVer}',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n pnt',
                            checks=[self.check('length(vmSecrets)', 1)).get_output_in_json()

        # add client cert
        nodeType = self.cmd('az sf managed-cluster client-certificate add -g {rg} -c {cluster_name} -n pnt '
                            ' --thumbprint {cert_tp2}',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n pnt',
                            checks=[self.check('length(clients)', 2)).get_output_in_json()

        # remove client cert
        nodeType = self.cmd('az sf managed-cluster client-certificate delete -g {rg} -c {cluster_name} -n pnt '
                            ' --thumbprint {cert_tp2}',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        nodeType = self.cmd('az sf managed-node-type show -g {rg} -c {cluster_name} -n pnt',
                            checks=[self.check('length(clients)', 1)).get_output_in_json()

        self.cmd('az sf managed-cluster delete -g {rg} -c {cluster_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('az sf managed-cluster show -g {rg} -c {cluster_name}')


if __name__ == '__main__':
    unittest.main()
