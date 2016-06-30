#pylint: skip-file
import unittest
from six import StringIO
from azure.cli.commands.azure_resource_id import AzureResourceId

class TestApplication(unittest.TestCase):

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

    def test_resource_id_simple(self):
        rg = 'lbrg'
        lb = 'mylb'
        type = 'Microsoft.Network/loadBalancers'
        sub = '00000000-0000-0000-0000-000000000000'
        result = str(AzureResourceId(lb, rg, type, sub))
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb'
        self.assertEqual(result, expected)

    def test_resource_id_complex(self):
        rg = 'lbrg'
        lb = 'mylb'
        type = 'Microsoft.Network/loadBalancers'
        bep = 'mybep'
        bep_type = 'backendAddressPools'
        sub = '00000000-0000-0000-0000-000000000000'
        result = str(AzureResourceId(lb, rg, type, sub, bep_type, bep))
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep'
        self.assertEqual(result, expected)

    def test_resource_id_with_id(self):
        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep'
        result = str(AzureResourceId(id))
        expected = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/lbrg/providers/Microsoft.Network/loadBalancers/mylb/backendAddressPools/mybep'
        self.assertEqual(result, expected)
        
if __name__ == '__main__':
    unittest.main()
