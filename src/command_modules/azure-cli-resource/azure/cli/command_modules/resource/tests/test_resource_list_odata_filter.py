import unittest
from azure.cli.command_modules.resource.custom import _list_resources_odata_filter_builder
from azure.cli.parser import IncorrectUsageError

class TestListResources(unittest.TestCase):   

    @classmethod
    def setUpClass(cls):
        pass
        
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    def test_tag_name(self):
        filter = _list_resources_odata_filter_builder(tag='foo')
        self.assertEqual(filter, "tagname eq 'foo'")

    def test_tag_name_starts_with(self):
        filter = _list_resources_odata_filter_builder(tag='f*')
        self.assertEqual(filter, "startswith(tagname, 'f')")

    def test_tag_name_value_equals(self):
        filter = _list_resources_odata_filter_builder(tag='foo=bar')
        self.assertEqual(filter, "tagname eq 'foo' and tagvalue eq 'bar'")

    def test_name_location_equals(self):
        filter = _list_resources_odata_filter_builder(
            name='wonky', location='dory', resource_type='resource/type'
        )
        self.assertEqual(filter, "name eq 'wonky' and location eq 'dory' and resourceType eq 'resource/type'")

    def test_name_location_equals(self):
        filter = _list_resources_odata_filter_builder(name='wonky', location='dory')
        self.assertEqual(filter, "name eq 'wonky' and location eq 'dory'")

    def test_tag_and_name_fails(self):
        with self.assertRaises(IncorrectUsageError):
            filter = _list_resources_odata_filter_builder(tag='foo=bar', name='should not work')

if __name__ == '__main__':
    unittest.main()
