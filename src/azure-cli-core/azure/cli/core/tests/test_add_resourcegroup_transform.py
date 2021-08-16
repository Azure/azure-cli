# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from io import StringIO
from azure.cli.core.commands.transform import _parse_id, _add_resource_group


class TestResourceGroupTransform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    # CORRECT_ID should match 'resourceGroups' in the path in a case insensitive way
    CORRECT_ID = "/subscriptions/00000000-0000-0000-0000-0000000000000/resOurcegroUps/REsourceGROUPname/providers/Microsoft.Compute/virtualMachines/vMName"  # pylint: disable=line-too-long
    NON_RG_ID = "/subscriptions/00000000-0000-0000-0000-0000000000000/somethingElse/REsourceGROUPname/providers/Microsoft.Compute/virtualMachines/vMName"  # pylint: disable=line-too-long
    BOGUS_ID = "|completely-bogus-id|"
    DICT_ID = {'value': "/subscriptions/00000000-0000-0000-0000-0000000000000/resourceGroups/REsourceGROUPname/providers/Microsoft.Compute/virtualMachines/vMName"}  # pylint: disable=line-too-long

    def test_split_correct_id(self):
        result = _parse_id(TestResourceGroupTransform.CORRECT_ID)
        self.assertDictEqual(result, {
            'resource-group': 'REsourceGROUPname',
            'name': 'vMName'
        })

    def test_split_non_resourcegroup_id(self):
        with self.assertRaises(KeyError):
            _parse_id(TestResourceGroupTransform.NON_RG_ID)

    def test_split_bogus_resourcegroup_id(self):
        with self.assertRaises(IndexError):
            _parse_id(TestResourceGroupTransform.BOGUS_ID)

    def test_split_dict_id(self):
        with self.assertRaises(TypeError):
            _parse_id(TestResourceGroupTransform.DICT_ID)

    def test_add_valid_resourcegroup_id(self):
        instance = {
            'id': TestResourceGroupTransform.CORRECT_ID,
            'name': 'A name'
        }
        _add_resource_group(instance)
        self.assertDictEqual(instance, {
            'id': TestResourceGroupTransform.CORRECT_ID,
            'resourceGroup': 'REsourceGROUPname',
            'name': 'A name'
        })

    def test_dont_add_invalid_resourcegroup_id(self):
        instance = {
            'id': TestResourceGroupTransform.BOGUS_ID,
            'name': 'A name'
        }
        _add_resource_group(instance)
        self.assertDictEqual(instance, {
            'id': TestResourceGroupTransform.BOGUS_ID,
            'name': 'A name'
        })

    def test_dont_stomp_on_existing_resourcegroup_id(self):
        instance = {
            'id': TestResourceGroupTransform.CORRECT_ID,
            'resourceGroup': 'SomethingElse',
            'name': 'A name'
        }
        _add_resource_group(instance)
        self.assertDictEqual(instance, {
            'id': TestResourceGroupTransform.CORRECT_ID,
            'resourceGroup': 'SomethingElse',
            'name': 'A name'
        })


if __name__ == '__main__':
    unittest.main()
