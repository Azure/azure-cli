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
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ServiceFabricClusterTests(ScenarioTest):
    @ResourceGroupPreparer()
    @KeyVaultPreparer(name_prefix='sfrp-cli-kv-', additional_params='--enabled-for-deployment --enabled-for-template-deployment')
    def test_create_cluster_with_separate_kv(self, key_vault, resource_group):
        self.kwargs.update({
            'kv_name': key_vault,
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': "Pass123!@#",
            'policy_path': os.path.join(TEST_DIR, 'policy.json')
        })
        _create_cluster_with_separate_kv(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

    @ResourceGroupPreparer()
    def test_update_settings_and_reliability(self):
        self.kwargs.update({
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': "Pass123!@#",
            'primary_node_type': 'nt1vm',
            'new_node_type': 'nt2',
            'cluster_size': '5'
        })
        _create_cluster(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

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

        # update reliability to Silver
        self.cmd('sf cluster reliability update --resource-group {rg} -c {cluster_name} --reliability-level Silver',
                 checks=[self.check('reliabilityLevel', 'Silver')])


    @ResourceGroupPreparer(location='southcentralus')
    def test_add_secondary_node_type_add_remove_node(self):
        self.kwargs.update({
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'southcentralus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': "Pass123!@#",
            'cluster_size': '3',
            'new_node_type': 'nt2'
        })
        _create_cluster(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

        # add node type nt2
        self.cmd('az sf cluster node-type add -g {rg} -c {cluster_name} --node-type {new_node_type} --capacity 5 --vm-user-name admintest '
                '--vm-password {vm_password} --durability-level Bronze --vm-sku Standard_D15_v2',
                checks=[self.check('provisioningState', 'Succeeded'),
                        self.check('length(nodeTypes)', 2),
                        self.check('nodeTypes[1].name', 'nt2'),
                        self.check('nodeTypes[1].vmInstanceCount', 5),
                        self.check('nodeTypes[1].durabilityLevel', 'Bronze')])

        # skipping add/remove node for now because begin_update method fails on test session only
        # with ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)

        # # add node to none primary node type nt2
        # self.cmd('sf cluster node add -g {rg} -c {cluster_name} --node-type {new_node_type} --number-of-nodes-to-add 2',
        #         checks=[self.check('nodeTypes[0].vmInstanceCount', 7)])

        # # remove node from none primary node type nt2
        # self.cmd('sf cluster node remove -g {rg} -c {cluster_name} --node-type {new_node_type} --number-of-nodes-to-remove 1',
        #          checks=[self.check('nodeTypes[1].vmInstanceCount', 6)])

        # update durability to Silver of node type nt2
        self.cmd('sf cluster durability update --resource-group {rg} -c {cluster_name} --durability-level Silver --node-type {new_node_type}',
                checks=[self.check('nodeTypes[1].durabilityLevel', 'Silver')])


    @unittest.skip('disable temporarily, begin_update method fails on test session only with ConnectionResetError')
    @ResourceGroupPreparer(location='southcentralus')
    def test_primary_nt_add_remove_node(self):
        self.kwargs.update({
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'southcentralus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': "Pass123!@#",
            'primary_node_type': 'nt1vm',
            'cluster_size': '5'
        })
        _create_cluster(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

        # add node primary node type nt1vm
        self.cmd('sf cluster node add -g {rg} -c {cluster_name} --node-type {primary_node_type} --number-of-nodes-to-add 2',
                checks=[self.check('nodeTypes[0].vmInstanceCount', 7)])

        # remvoe node from primary node type nt1vm
        self.cmd('sf cluster node remove -g {rg} -c {cluster_name} --node-type {primary_node_type} --number-of-nodes-to-remove 1',
                 checks=[self.check('nodeTypes[1].vmInstanceCount', 6)])


if __name__ == '__main__':
    unittest.main()
