# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import json
import logging
import os
import time
from test_util import _create_cluster, _wait_for_cluster_state_ready
from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer


class ServiceFabricClusterTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_node_type(self):
        self.kwargs.update({
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
        })
        _create_cluster(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

        self.cmd('az sf cluster node-type add -g {rg} -c {cluster_name} --node-type nt2 --capacity 5 --vm-user-name admintest '
                 '--vm-password {vm_password} --durability-level Gold --vm-sku Standard_D15_v2',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('length(nodeTypes)', 2),
                         self.check('nodeTypes[1].name', 'nt2'),
                         self.check('nodeTypes[1].vmInstanceCount', 5),
                         self.check('nodeTypes[1].durabilityLevel', 'Gold')])


if __name__ == '__main__':
    unittest.main()
