# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.commands.arm import parse_resource_id

class TestARM(unittest.TestCase):
    def test_resource_parse(self):
        tests = [{
            'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                           '/Microsoft.Storage/storageAccounts/foo/providers'
                           '/Microsoft.Authorization/locks/bar',
            'expected': {
                'name': 'foo',
                'type': 'storageAccounts',
                'namespace': 'Microsoft.Storage',
                'child_name': 'bar',
                'child_namespace': 'Microsoft.Authorization',
                'child_type': 'locks',
                'resource_group': 'testgroup',
                'subscription': 'fakesub',
            }
        }, {
            'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                           '/Microsoft.Storage/storageAccounts/foo'
                           '/locks/bar',
            'expected': {
                'name': 'foo',
                'type': 'storageAccounts',
                'namespace': 'Microsoft.Storage',
                'child_name': 'bar',
                'child_type': 'locks',
                'resource_group': 'testgroup',
                'subscription': 'fakesub',
            }
        }, {
            'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                           '/Microsoft.Storage/storageAccounts/foo',
            'expected': {
                'name': 'foo',
                'type': 'storageAccounts',
                'namespace': 'Microsoft.Storage',
                'resource_group': 'testgroup',
                'subscription': 'fakesub',
            }
        }, {
            'resource_id': '/subscriptions/fakesub/providers/Microsoft.Authorization'
                           '/locks/foo',
            'expected': {
                'name': 'foo',
                'type': 'locks',
                'namespace': 'Microsoft.Authorization',
                'subscription': 'fakesub',
            }
        }, {
            'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                           '/Microsoft.Storage/storageAccounts/foo/providers'
                           '/Microsoft.Authorization/locks/bar/nets/gc',
            'expected': {
                'name': 'foo',
                'type': 'storageAccounts',
                'namespace': 'Microsoft.Storage',
                'child_name': 'bar',
                'child_namespace': 'Microsoft.Authorization',
                'child_type': 'locks',
                'grandchild_name': 'gc',
                'grandchild_type': 'nets',
                'resource_group': 'testgroup',
                'subscription': 'fakesub',
            }
        }, {
            'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                           '/Microsoft.Storage/storageAccounts/foo'
                           '/locks/bar/nets/gc',
            'expected': {
                'name': 'foo',
                'type': 'storageAccounts',
                'namespace': 'Microsoft.Storage',
                'child_name': 'bar',
                'child_type': 'locks',
                'grandchild_name': 'gc',
                'grandchild_type': 'nets',
                'resource_group': 'testgroup',
                'subscription': 'fakesub',
            }
        }]

        for test in tests:
            resource = parse_resource_id(test['resource_id'])
            self.assertDictEqual(resource, test['expected'])

if __name__ == "__main__":
    unittest.main()
