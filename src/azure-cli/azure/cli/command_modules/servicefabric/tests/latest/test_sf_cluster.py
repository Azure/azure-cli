# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import json
import logging
import os
import time
from azure.cli.command_modules.servicefabric.tests.latest.test_util import _create_cluster, _create_cluster_with_separate_kv, _wait_for_cluster_state_ready, _add_selfsigned_cert_to_keyvault
from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ServiceFabricClusterTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cluster_certs(self):
        self.kwargs.update({
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cert_name2': self.create_random_name('sfrp-cli-cert2', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': "Pass123!@#",
            'policy_path': os.path.join(TEST_DIR, 'policy.json')
        })
        _create_cluster_with_separate_kv(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

        primary_cert = self.cmd('keyvault certificate show --vault-name {kv_name} -n {cert_name}').get_output_in_json()
        primary_cert_tp = primary_cert['x509ThumbprintHex']
        self.kwargs.update({'primary_cert_tp': primary_cert_tp})

        # add secondary cert
        self.cmd('keyvault certificate create --vault-name {kv_name} -n {cert_name2} -p @"{policy_path}"')

        while True:
            cert = self.cmd('keyvault certificate show --vault-name {kv_name} -n {cert_name}').get_output_in_json()
            if cert:
                break
        assert cert['sid'] is not None
        secondary_cert = cert
        secondary_cert_secret_id = secondary_cert['sid']
        secondary_cert_tp = secondary_cert['x509ThumbprintHex']
        self.kwargs.update({'secondary_cert_secret_id': secondary_cert_secret_id})
        self.cmd('sf cluster certificate add --resource-group {rg} --cluster-name {cluster_name} --secret-identifier {secondary_cert_secret_id}',
                 checks=[self.check('certificate.thumbprintSecondary', secondary_cert_tp)])

        _wait_for_cluster_state_ready(self, self.kwargs)

        # remove primary cert
        self.cmd('sf cluster certificate remove --resource-group {rg} --cluster-name {cluster_name} --thumbprint {primary_cert_tp}',
                 checks=[self.check('certificate.thumbprint', secondary_cert_tp)])

        _wait_for_cluster_state_ready(self, self.kwargs)

    @unittest.skip('no quota, disable temporarily')
    @ResourceGroupPreparer()
    def test_cluster(self):
        self.kwargs.update({
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': "Pass123!@#",
            'priamry_node_type': 'nt1vm',
            'new_node_type': 'nt2'
        })
        _create_cluster(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

        # add node type nt2
        self.cmd('az sf cluster node-type add -g {rg} -c {cluster_name} --node-type {new_node_type} --capacity 6 --vm-user-name admintest '
                 '--vm-password {vm_password} --durability-level Bronze --vm-sku Standard_D15_v2',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('length(nodeTypes)', 2),
                         self.check('nodeTypes[1].name', 'nt2'),
                         self.check('nodeTypes[1].vmInstanceCount', 6),
                         self.check('nodeTypes[1].durabilityLevel', 'Bronze')])

        # remvoe node from node type nt2
        self.cmd('sf cluster node remove -g {rg} -c {cluster_name} --node-type {new_node_type} --number-of-nodes-to-remove 1',
                 checks=[self.check('nodeTypes[1].vmInstanceCount', 5)])

        # update to duribility to Silver of node type nt2
        self.cmd('sf cluster durability update --resource-group {rg} -c {cluster_name} --durability-level Silver --node-type {new_node_type}',
                 checks=[self.check('nodeTypes[1].durabilityLevel', 'Silver')])

        # add setting
        self.cmd('sf cluster setting set --resource-group {rg} -c {cluster_name} --section NamingService --parameter MaxOperationTimeout --value 10001',
                 checks=[self.check('length(fabricSettings)', 2),
                         self.check('fabricSettings[1].name', 'NamingService'),
                         self.check('fabricSettings[1].parameters[0].name', 'MaxOperationTimeout'),
                         self.check('fabricSettings[1].parameters[0].value', '10001')])

        # remove setting
        self.cmd('sf cluster setting remove --resource-group {rg} -c {cluster_name} --section NamingService --parameter MaxOperationTimeout',
                 checks=[self.check('length(fabricSettings)', 1),
                         self.check('fabricSettings[0].name', 'Security')])

        # add node primary node type nt1vm
        self.cmd('sf cluster node add -g {rg} -c {cluster_name} --node-type {priamry_node_type} --number-of-nodes-to-add 2',
                 checks=[self.check('nodeTypes[0].vmInstanceCount', 5)])

        # update reliability to Silver
        self.cmd('sf cluster reliability update --resource-group {rg} -c {cluster_name} --reliability-level Silver',
                 checks=[self.check('reliabilityLevel', 'Silver')])


if __name__ == '__main__':
    unittest.main()
