# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: skip-file
import mock
import os
import tempfile
import unittest
import yaml

from azure.cli.command_modules.acs.custom import merge_kubernetes_configurations, _acs_browse_internal
from azure.mgmt.compute.models import ContainerServiceOchestratorTypes, ContainerService, ContainerServiceOrchestratorProfile

class AcsCustomCommandTest(unittest.TestCase):
    @mock.patch('azure.cli.command_modules.acs.custom._get_subscription_id')
    def test_browse_k8s(self, get_subscription_id):
        acs_info = ContainerService("location", {}, {}, {})
        acs_info.orchestrator_profile = ContainerServiceOrchestratorProfile(ContainerServiceOchestratorTypes.kubernetes)
        
        with mock.patch('azure.cli.command_modules.acs.custom._get_acs_info', return_value=acs_info) as get_acs_info:
            with mock.patch('azure.cli.command_modules.acs.custom._k8s_browse_internal') as k8s_browse:
                _acs_browse_internal(acs_info, 'resource-group', 'name', False)
                get_acs_info.assert_called_with('name', 'resource-group')
                k8s_browse.assert_called_with(acs_info, False)

    @mock.patch('azure.cli.command_modules.acs.custom._get_subscription_id')
    def test_browse_dcos(self, get_subscription_id):
        acs_info = ContainerService("location", {}, {}, {})
        acs_info.orchestrator_profile = ContainerServiceOrchestratorProfile(ContainerServiceOchestratorTypes.dcos)
        
        with mock.patch('azure.cli.command_modules.acs.custom._dcos_browse_internal') as dcos_browse:
            _acs_browse_internal(acs_info, 'resource-group', 'name', False)
            dcos_browse.assert_called_with(acs_info, False)

    def test_merge_credentials(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': [
                'cluster1'
            ],
            'contexts': [
                'context1'
            ],
            'users': [
                'user1'
            ],
            'current-context': 'cluster1',
        }
        with open(existing.name, 'w+') as stream:
            yaml.dump(obj1, stream)

        obj2 = {
            'clusters': [
                'cluster2'
            ],
            'contexts': [
                'context2'
            ],
            'users': [
                'user2'
            ],
            'current-context': 'cluster2',
        }

        with open(addition.name, 'w+') as stream:
            yaml.dump(obj2, stream)
        merge_kubernetes_configurations(existing.name, addition.name)

        with open(existing.name, 'r') as stream:
            merged = yaml.load(stream)
        self.assertEqual(len(merged['clusters']), 2)
        self.assertEqual(merged['clusters'], ['cluster1', 'cluster2'])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'], ['context1', 'context2'])
        self.assertEqual(len(merged['users']), 2)
        self.assertEqual(merged['users'], ['user1', 'user2'])
        self.assertEqual(merged['current-context'], obj2['current-context'])

        os.remove(existing.name)
        os.remove(addition.name)
