# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import json
import logging
import os
import time
from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

logger = logging.getLogger(__name__)


def _create_keyvault(test, kwargs):
    kwargs.update({'policy_path': os.path.join(TEST_DIR, 'policy.json')})

    test.cmd('keyvault create --resource-group {rg} -n {kv_name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true')
    test.cmd('keyvault certificate create --vault-name {kv_name} -n {cert_name} -p @"{policy_path}"')


def _create_cluster(test, kwargs):
    _create_keyvault(test, kwargs)

    while True:
        cert = test.cmd('keyvault certificate show --vault-name {kv_name} -n {cert_name}').get_output_in_json()
        if cert:
            break
    assert cert['sid'] is not None
    cert_secret_id = cert['sid']
    logger.error(cert_secret_id)
    kwargs.update({'cert_secret_id': cert_secret_id})

    test.cmd('az sf cluster create -g {rg} -n {cluster_name} -l {loc} --secret-identifier {cert_secret_id} --vm-password "{vm_password}" --cluster-size 3')
    timeout = time.time() + 900
    while True:
        cluster = test.cmd('az sf cluster show -g {rg} -n {cluster_name}').get_output_in_json()

        if cluster['provisioningState']:
            if cluster['provisioningState'] == 'Succeeded':
                return
            if cluster['provisioningState'] == 'Failed':
                raise CLIError("Cluster deployment was not succesful")

        if time.time() > timeout:
            raise CLIError("Cluster deployment timed out")
        if not test.in_recording:
            time.sleep(20)


def _wait_for_cluster_state_ready(test, kwargs):
    timeout = time.time() + 900
    while True:
        cluster = test.cmd('az sf cluster show -g {rg} -n {cluster_name}').get_output_in_json()

        if cluster['clusterState']:
            if cluster['clusterState'] == 'Ready':
                return

        if time.time() > timeout:
            raise CLIError("Cluster deployment timed out. cluster state is not 'Ready'. State: {}".format(cluster['ClusterState']))
        if not test.in_recording:
            time.sleep(20)


class ServiceFabricApplicationTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_node_type(self):
        self.kwargs.update({
            # 'rg': 'alsantamclirg2',
            'kv_name': self.create_random_name('sfrp-cli-kv-', 24),
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            # 'cluster_name': 'alsantamcli2',
            'vm_password': self.create_random_name('Pass@', 9),
        })

        _create_cluster(self, self.kwargs)
        _wait_for_cluster_state_ready(self, self.kwargs)

        self.cmd('az sf cluster node-type add -g {rg} -n {cluster_name} --node-type nt2 --capacity 5 --vm-user-name admintest '
                 '--vm-password {vm_password} --durability-level Gold --vm-sku Standard_D15_v2',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('length(nodeTypes)', 2),
                         self.check('nodeTypes[1].name', 'nt2'),
                         self.check('nodeTypes[1].vmInstanceCount', 5),
                         self.check('nodeTypes[1].durabilityLevel', 'Gold')])


if __name__ == '__main__':
    unittest.main()
