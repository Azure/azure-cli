# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.commands.arm import parse_resource_id


class TestARM(unittest.TestCase):
    def test_resource_parse(self):

        tests = [
            {
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
            },
            {
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
            },
            {
                'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                               '/Microsoft.Storage/storageAccounts/foo',
                'expected': {
                    'name': 'foo',
                    'type': 'storageAccounts',
                    'namespace': 'Microsoft.Storage',
                    'resource_group': 'testgroup',
                    'subscription': 'fakesub',
                }
            },
            {
                'resource_id': '/subscriptions/fakesub/providers/Microsoft.Authorization'
                               '/locks/foo',
                'expected': {
                    'name': 'foo',
                    'type': 'locks',
                    'namespace': 'Microsoft.Authorization',
                    'subscription': 'fakesub',
                }
            },
            {
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
            },
            {
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
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/'
                               'Microsoft.Provider1/resourceType1/name1',
                'expected': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'resource_parent': '',
                    'resource_namespace': 'Microsoft.Provider1',
                    'resource_type': 'resourceType1',
                    'resource_name': 'name1'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/'
                               'Microsoft.Provider1/resourceType1/name1/resourceType2/name2',
                'expected': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'child_namespace': None,
                    'child_type': 'resourceType2',
                    'child_name': 'name2',
                    'resource_parent': 'resourceType1/name1/',
                    'resource_namespace': 'Microsoft.Provider1',
                    'resource_type': 'resourceType2',
                    'resource_name': 'name2'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/'
                               'Microsoft.Provider1/resourceType1/name1/providers/'
                               'Microsoft.Provider2/resourceType2/name2',
                'expected': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'child_namespace': 'Microsoft.Provider2',
                    'child_type': 'resourceType2',
                    'child_name': 'name2',
                    'resource_parent': 'resourceType1/name1/providers/Microsoft.Provider2/',
                    'resource_namespace': 'Microsoft.Provider1',
                    'resource_type': 'resourceType2',
                    'resource_name': 'name2'
                }
            }
        ]
        for test in tests:
            kwargs = parse_resource_id(test['resource_id'])
            for key in test['expected']:
                try:
                    self.assertEqual(kwargs[key], test['expected'][key])
                except KeyError:
                    self.assertTrue(key not in kwargs and test['expected'][key] is None)


if __name__ == "__main__":
    unittest.main()
