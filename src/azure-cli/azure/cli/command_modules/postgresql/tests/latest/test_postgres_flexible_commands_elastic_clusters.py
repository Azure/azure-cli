# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from time import sleep
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, DEFAULT_LOCATION

class ElasticClustersMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_elastic_clusters_mgmt(self, resource_group):
        self._test_elastic_clusters_mgmt(resource_group)

    def _test_elastic_clusters_mgmt(self, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        version = '17'
        location = self.postgres_location
        sku_name = 'Standard_D2ds_v4'
        tier = 'GeneralPurpose'
        non_cluster = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        cluster = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        cluster_restore = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        node_count = 2
        database = 'dbcluster'

        # Try to create regular flexible server passing elastic cluster specific parameters to verify that they are not accepted for regular servers.
        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} \
                   --version {} --database-name {}'
                  .format(resource_group, cluster, sku_name, version, database),
                  expect_failure=True)
        
        # Create regular flexible server to verify that elastic cluster specific parameters are not accepted for update command as well.
        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} \
                   --version {} --public-access Enabled'
                  .format(resource_group, non_cluster, sku_name, version))
        
        # Try to update regular flexible server with elastic cluster specific parameters to verify that they are not accepted for regular servers.
        self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                 .format(resource_group, non_cluster, node_count),
                    expect_failure=True)

        # Create elastic cluster
        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} \
                   --version {} --node-count {} --public-access Enabled'
                  .format(resource_group, cluster, sku_name, version, node_count))
        
        basic_info = self.cmd('postgres flexible-server show -g {} -n {}'.
                              format(resource_group, cluster),
                              checks=[
                                  JMESPathCheck('name', cluster),
                                  JMESPathCheck('resourceGroup', resource_group),
                                  JMESPathCheck('sku.name', sku_name),
                                  JMESPathCheck('sku.tier', tier),
                                  JMESPathCheck('version', version),
                                  JMESPathCheck('cluster.clusterSize', node_count)
                              ]).get_output_in_json()
        self.assertEqual(basic_info['location'].replace(' ', '').lower(), location)

        # Test failures
        self.cmd('postgres flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(resource_group, cluster),
                 expect_failure=True)

        # Backend silently ignores if the cluster size is smaller than current size, and does not return error.
        # Also, the cluster size remains unchanged. Hence the check is added to verify that cluster size is not updated.
        # When control plane adds support for scaling down cluster size, this test should be updated accordingly.
        self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                 .format(resource_group, cluster, node_count - 1),
                 checks=[
                     JMESPathCheck('cluster.clusterSize', node_count)])

        # Same behavior with cluster size being set to 0, it doesn't return error, neither it changes the cluster size.
        self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                 .format(resource_group, cluster, 0),
                 checks=[
                     JMESPathCheck('cluster.clusterSize', node_count)])

        # If the cluster size is larger than current supported maximum (20), it will return error.
        self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                 .format(resource_group, cluster, 21),
                 expect_failure=True)

        self.cmd('postgres flexible-server replica list -g {} -n {}'
                 .format(resource_group, cluster),
                 expect_failure=True)

        self.cmd('postgres flexible-server db create -g {} -s {} -n dbclusterfail'
                 .format(resource_group, cluster),
                 expect_failure=True)

        # Grow cluster size and validate growth.
        update_node_count = 4
        self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                               .format(resource_group, cluster, update_node_count),
                               checks=[
                                   JMESPathCheck('cluster.clusterSize', update_node_count)
                               ])

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # Restore cluster and validate the restored cluster has the same cluster size as source cluster
        self.cmd('postgres flexible-server restore -g {} --name {} --source-server {}'
                                  .format(resource_group, cluster_restore, basic_info['id']),
                                  checks=[
                                      JMESPathCheck('name', cluster_restore),
                                      JMESPathCheck('cluster.clusterSize', update_node_count)
                                  ])

        # Clean up
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, cluster))
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, cluster_restore))