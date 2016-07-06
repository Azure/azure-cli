# pylint: disable=line-too-long
import unittest
from six import StringIO
from azure.cli.commands.arm import parse_resource_id, resource_id, is_valid_resource_id

class TestApplication(unittest.TestCase):

    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_resource_id_simple(self):
        rg = 'lbrg'
        lb = 'mylb'
        namespace = 'Microsoft.Network'
        type = 'loadBalancers'
        sub = '00000000-0000-0000-0000-000000000000'
        result = resource_id(resource_group=rg, name=lb, namespace=namespace, type=type, subscription=sub)
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb'
        self.assertTrue(is_valid_resource_id(expected))
        self.assertTrue(is_valid_resource_id(result))
        self.assertEqual(result, expected)

    def test_resource_id_complex(self):
        rg = 'lbrg'
        lb = 'mylb'
        namespace = 'Microsoft.Network'
        type = 'loadBalancers'
        bep = 'mybep'
        bep_type = 'backendAddressPools'
        sub = '00000000-0000-0000-0000-000000000000'
        result = resource_id(name=lb, resource_group=rg, namespace=namespace, type=type, subscription=sub, child_type=bep_type, child_name=bep)
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep'
        self.assertTrue(is_valid_resource_id(expected))
        self.assertTrue(is_valid_resource_id(result))
        self.assertEqual(result, expected)

    def test_resource_id_with_id(self):
        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep'
        result = resource_id(**parse_resource_id(id))
        self.assertEqual(result, id)
        
if __name__ == '__main__':
    unittest.main()
