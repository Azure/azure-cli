import unittest
from azure.cli.command_modules.resource import _list_resources_odata_filter_builder
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
        args = {
            'tag': 'foo'
            }
        filter = _list_resources_odata_filter_builder(args)
        self.assertEquals(filter, "tagname eq 'foo'")

    def test_tag_name_starts_with(self):
        args = {
            'tag': 'f*'
            }
        filter = _list_resources_odata_filter_builder(args)
        self.assertEquals(filter, "startswith(tagname, 'f')")

    def test_tag_name_value_equals(self):
        args = {
            'tag': 'foo=bar'
            }
        filter = _list_resources_odata_filter_builder(args)
        self.assertEquals(filter, "tagname eq 'foo' and tagvalue eq 'bar'")

    def test_name_location_equals(self):
        args = {
            'name': 'wonky',
            'location': 'dory',
            'resourcetype': 'resource/type'
            }
        filter = _list_resources_odata_filter_builder(args)
        self.assertEquals(filter, "name eq 'wonky' and location eq 'dory' and resourceType eq 'resource/type'")

    def test_name_location_equals(self):
        args = {
            'name': 'wonky',
            'location': 'dory'
            }
        filter = _list_resources_odata_filter_builder(args)
        self.assertEquals(filter, "name eq 'wonky' and location eq 'dory'")

    def test_tag_and_name_fails(self):
        args = {
            'tag': 'foo=bar',
            'name': 'will not work'
            }
        with self.assertRaises(IncorrectUsageError):
            filter = _list_resources_odata_filter_builder(args)

if __name__ == '__main__':
    unittest.main()
