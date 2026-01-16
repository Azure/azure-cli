# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from time import sleep
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
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
        cluster_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        cluster_size = 2

        # create elastic cluster
        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} \
                   --version {} --cluster-option ElasticCluster --public-access Enabled'
                  .format(resource_group, cluster_name, sku_name, version))
        
        basic_info = self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, cluster_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], cluster_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['cluster']['clusterSize'], cluster_size)

        # test failures
        self.cmd('postgres flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(resource_group, cluster_name), expect_failure=True)
        self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                 .format(resource_group, cluster_name, cluster_size - 1), expect_failure=True)
        self.cmd('postgres flexible-server replica list -g {} -n {}'
                 .format(resource_group, cluster_name), expect_failure=True)
        self.cmd('postgres flexible-server db create -g {} -s {} -d dbclusterfail'
                 .format(resource_group, cluster_name), expect_failure=True)

        # update cluster
        update_cluster_size = 4
        update_info = self.cmd('postgres flexible-server update -g {} -n {} --node-count {}'
                               .format(resource_group, cluster_name, update_cluster_size)).get_output_in_json()
        self.assertEqual(update_info['cluster']['clusterSize'], update_cluster_size)

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # Restore
        cluster_restore_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restore_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {}'
                                  .format(resource_group, cluster_restore_name, basic_info['id'])).get_output_in_json()
        self.assertEqual(restore_result['name'], cluster_restore_name)
        self.assertEqual(restore_result['cluster']['clusterSize'], update_cluster_size)

        # delete everything
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, cluster_name))
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, cluster_restore_name))