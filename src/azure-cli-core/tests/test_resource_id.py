# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
from six import StringIO
from azure.cli.core.commands.arm import parse_resource_id, resource_id, is_valid_resource_id


class TestApplication(unittest.TestCase):

    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_resource_id_simple(self):
        rg = 'lbrg'
        lb = 'mylb'
        namespace = 'Microsoft.Network'
        rtype = 'loadBalancers'
        sub = '00000000-0000-0000-0000-000000000000'
        result = resource_id(resource_group=rg, name=lb, namespace=namespace,
                             type=rtype, subscription=sub)
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb'
        self.assertTrue(is_valid_resource_id(expected))
        self.assertTrue(is_valid_resource_id(result))
        self.assertEqual(result, expected)

    def test_resource_id_with_child(self):
        rg = 'lbrg'
        lb = 'mylb'
        namespace = 'Microsoft.Network'
        rtype = 'loadBalancers'
        bep = 'mybep'
        bep_type = 'backendAddressPools'
        sub = '00000000-0000-0000-0000-000000000000'
        result = resource_id(name=lb, resource_group=rg, namespace=namespace,
                             type=rtype, subscription=sub, child_type=bep_type, child_name=bep)
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep'
        self.assertTrue(is_valid_resource_id(expected))
        self.assertTrue(is_valid_resource_id(result))
        self.assertEqual(result, expected)

    def test_resource_id_with_grandchild(self):
        rg = 'lbrg'
        lb = 'mylb'
        namespace = 'Microsoft.Network'
        rtype = 'loadBalancers'
        bep = 'mybep'
        bep_type = 'backendAddressPools'
        grandchild = 'grandchild'
        gc_type = 'grandchildType'
        sub = '00000000-0000-0000-0000-000000000000'
        result = resource_id(name=lb, resource_group=rg, namespace=namespace, type=rtype, subscription=sub,
                             child_type=bep_type, child_name=bep, grandchild_name=grandchild, grandchild_type=gc_type)
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep/grandchildType/grandchild'
        self.assertTrue(is_valid_resource_id(expected))
        self.assertTrue(is_valid_resource_id(result))
        self.assertEqual(result, expected)

    def test_resource_id_with_id(self):
        rid = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep/grandchildType/grandchild'
        result = resource_id(**parse_resource_id(rid))
        self.assertEqual(result, rid)


if __name__ == '__main__':
    unittest.main()
