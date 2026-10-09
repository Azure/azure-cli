# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI Relay - CLUSTER TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class RelayClusterCURDScenarioTest(ScenarioTest):
	from azure.cli.testsdk.scenario_tests import AllowLargeResponse

	@AllowLargeResponse()
	def test_relay_cluster(self):
		self.kwargs.update({
			'loc': 'eastus2euap',
			'rg': self.create_random_name(prefix='rg-cluster-', length=20),
			'clustername': self.create_random_name(prefix='relay-clus1-', length=20),
			'tags': '{tag1:value1}',
			'tags2': '{tag2:value2}',
			'capacity': 3,
			'sku': 'Dedicated',
			'tier': 'Dedicated'
		})

		# Get Cluster
		getresponse = self.cmd('relay cluster show --resource-group PPGTest --name RelayClusterTestE2E2026',
							   checks=[self.check('sku.capacity', self.kwargs['capacity'])]).get_output_in_json()

		self.assertEqual(getresponse['sku']['name'], self.kwargs['sku'])
		self.assertEqual(getresponse['location'], self.kwargs['loc'])

		self.kwargs.update({'clusterid': getresponse['id']})

		# Get namespaces created in the cluster
		listnsclusterresult = self.cmd('relay cluster namespace list --resource-group PPGTest --cluster-name RelayClusterTestE2E2026').output
		self.assertIsNotNone(listnsclusterresult)

		# Get cluster created in the resourcegroup
		listclusterresult = self.cmd('relay cluster list --resource-group PPGTest').output
		self.assertGreater(len(listclusterresult), 0)

		# Delete cluster
		# commented as the cluster can be deleted only after 4 hours
		# self.cmd('relay cluster delete --resource-group test-migration1 --name {clustername} --yes')
