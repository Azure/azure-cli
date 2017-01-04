# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: skip-file
import unittest
import os
import tempfile
import yaml

from azure.cli.command_modules.acs.custom import merge_kubernetes_configurations

class AcsCustomCommandTest(unittest.TestCase):
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
