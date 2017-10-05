# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.commands.arm import parse_resource_id, is_valid_resource_id, resource_id


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
                    'child_name_1': 'bar',
                    'child_namespace_1': 'Microsoft.Authorization',
                    'child_type_1': 'locks',
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
                    'child_name_1': 'bar',
                    'child_type_1': 'locks',
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
                'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                               '/Microsoft.Storage/storageAccounts/foo/providers'
                               '/Microsoft.Authorization/locks/bar/providers/Microsoft.Network/nets/gc',
                'expected': {
                    'name': 'foo',
                    'type': 'storageAccounts',
                    'namespace': 'Microsoft.Storage',
                    'child_name_1': 'bar',
                    'child_namespace_1': 'Microsoft.Authorization',
                    'child_type_1': 'locks',
                    'child_name_2': 'gc',
                    'child_namespace_2': 'Microsoft.Network',
                    'child_type_2': 'nets',
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
                    'child_name_1': 'bar',
                    'child_type_1': 'locks',
                    'child_name_2': 'gc',
                    'child_type_2': 'nets',
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
                    'child_namespace_1': None,
                    'child_type_1': 'resourceType2',
                    'child_name_1': 'name2',
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
                    'child_namespace_1': 'Microsoft.Provider2',
                    'child_type_1': 'resourceType2',
                    'child_name_1': 'name2',
                    'resource_parent': 'resourceType1/name1/providers/Microsoft.Provider2/',
                    'resource_namespace': 'Microsoft.Provider1',
                    'resource_type': 'resourceType2',
                    'resource_name': 'name2'
                }
            },
            {
                'resource_id': '/subscriptions/00000/resourceGroups/myRg/providers/Microsoft.RecoveryServices/'
                               'vaults/vault_name/backupFabrics/fabric_name/protectionContainers/container_name/'
                               'protectedItems/item_name/recoveryPoint/recovery_point_guid',
                'expected': {
                    'subscription': '00000',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.RecoveryServices',
                    'type': 'vaults',
                    'name': 'vault_name',
                    'child_type_1': 'backupFabrics',
                    'child_name_1': 'fabric_name',
                    'child_type_2': 'protectionContainers',
                    'child_name_2': 'container_name',
                    'child_type_3': 'protectedItems',
                    'child_name_3': 'item_name',
                    'child_type_4': 'recoveryPoint',
                    'child_name_4': 'recovery_point_guid',
                    'resource_parent': 'vaults/vault_name/backupFabrics/fabric_name/'
                                       'protectionContainers/container_name/protectedItems/item_name/',
                    'resource_namespace': 'Microsoft.RecoveryServices',
                    'resource_type': 'recoveryPoint',
                    'resource_name': 'recovery_point_guid'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/'
                               'Microsoft.Provider1/resourceType1/name1/resourceType2/name2/providers/'
                               'Microsoft.Provider3/resourceType3/name3',
                'expected': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'child_namespace_1': None,
                    'child_type_1': 'resourceType2',
                    'child_name_1': 'name2',
                    'child_namespace_2': 'Microsoft.Provider3',
                    'child_type_2': 'resourceType3',
                    'child_name_2': 'name3',
                    'resource_parent': 'resourceType1/name1/resourceType2/name2/providers/Microsoft.Provider3/',
                    'resource_namespace': 'Microsoft.Provider1',
                    'resource_type': 'resourceType3',
                    'resource_name': 'name3'
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
            }
        ]
        for test in tests:
            self.assertTrue(is_valid_resource_id(test['resource_id']))
            kwargs = parse_resource_id(test['resource_id'])
            for key in test['expected']:
                try:
                    self.assertEqual(kwargs[key], test['expected'][key])
                except KeyError:
                    self.assertTrue(key not in kwargs and test['expected'][key] is None)

        invalid_ids = [
            '/subscriptions/fakesub/resourceGroups/myRg/type1/name1',
            '/subscriptions/fakesub/resourceGroups/myRg/providers/Microsoft.Provider/foo',
            '/subscriptions/fakesub/resourceGroups/myRg/providers/Microsoft.Provider/type/name/type1'
        ]
        for invalid_id in invalid_ids:
            self.assertFalse(is_valid_resource_id(invalid_id))

        tests = [
            {
                'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                               '/Microsoft.Storage/storageAccounts/foo/providers'
                               '/Microsoft.Authorization/locks/bar',
                'id_args': {
                    'name': 'foo',
                    'type': 'storageAccounts',
                    'namespace': 'Microsoft.Storage',
                    'child_name_1': 'bar',
                    'child_namespace_1': 'Microsoft.Authorization',
                    'child_type_1': 'locks',
                    'resource_group': 'testgroup',
                    'subscription': 'fakesub',
                }
            },
            {
                'resource_id': '/subscriptions/fakesub/resourcegroups/testgroup/providers'
                               '/Microsoft.Storage/storageAccounts/foo'
                               '/locks/bar',
                'id_args': {
                    'name': 'foo',
                    'type': 'storageAccounts',
                    'namespace': 'Microsoft.Storage',
                    'child_name_1': 'bar',
                    'child_type_1': 'locks',
                    'resource_group': 'testgroup',
                    'subscription': 'fakesub',
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/'
                               'Microsoft.Provider1/resourceType1/name1/resourceType2/name2/providers/'
                               'Microsoft.Provider3/resourceType3/name3',
                'id_args': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'child_type_1': 'resourceType2',
                    'child_name_1': 'name2',
                    'child_namespace_2': 'Microsoft.Provider3',
                    'child_type_2': 'resourceType3',
                    'child_name_2': 'name3'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/Microsoft.Provider1',
                'id_args': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg',
                'id_args': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/Microsoft.Provider1'
                               '/resourceType1/name1/resourceType2/name2/providers/Microsoft.Provider3',
                'id_args': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'child_type_1': 'resourceType2',
                    'child_name_1': 'name2',
                    'child_namespace_2': 'Microsoft.Provider3'
                }
            },
            {
                'resource_id': '/subscriptions/mySub/resourceGroups/myRg/providers/Microsoft.Provider1'
                               '/resourceType1/name1',
                'id_args': {
                    'subscription': 'mySub',
                    'resource_group': 'myRg',
                    'namespace': 'Microsoft.Provider1',
                    'type': 'resourceType1',
                    'name': 'name1',
                    'child_type_1': None,
                    'child_name_1': 'name2',
                    'child_namespace_2': 'Microsoft.Provider3'
                }
            }
        ]
        for test in tests:
            rsrc_id = resource_id(**test['id_args'])
            self.assertEqual(rsrc_id.lower(), test['resource_id'].lower())


if __name__ == "__main__":
    unittest.main()
