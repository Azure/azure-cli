from __future__ import print_function

import unittest
from six import StringIO
from collections import namedtuple

from azure.cli._output import (OutputProducer, OutputFormatException, format_json, format_table, format_list, format_text,
                                format_tsv, ListOutput)
import azure.cli._util as util

class TestOutput(unittest.TestCase):

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
        
    def test_out_json_valid(self):
        """
        The JSON output when the input is a dict should be the dict serialized to JSON
        """
        output_producer = OutputProducer(formatter=format_json, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""{
  "active": true,
  "id": "0b1f6472"
}
"""))

    def test_out_table_valid(self):
        output_producer = OutputProducer(formatter=format_table, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""active |    id   
-------|---------
True   | 0b1f6472

"""))

    def test_out_list_valid(self):
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active : True
Id     : 0b1f6472


"""))

    def test_out_list_valid_none_val(self):
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out({'active': None, 'id': '0b1f6472'})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active : None
Id     : 0b1f6472


"""))

    def test_out_list_valid_empty_array(self):
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out({'active': None, 'id': '0b1f6472', 'hosts': []})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active : None
Id     : 0b1f6472
Hosts  :
   None


"""))

    def test_out_list_valid_array_complex(self):
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out([{'active': True, 'id': '783yesdf'}, {'active': False, 'id': '3hjnme32'}, {'active': False, 'id': '23hiujbs'}])
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active : True
Id     : 783yesdf

Active : False
Id     : 3hjnme32

Active : False
Id     : 23hiujbs


"""))

    def test_out_list_valid_str_array(self):
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out(['location', 'id', 'host', 'server'])
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""location

id

host

server


"""))

    def test_out_list_valid_complex_array(self):
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472', 'myarray': ['1', '2', '3', '4']})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active  : True
Id      : 0b1f6472
Myarray :
   1
   2
   3
   4


"""))

    def test_out_list_format_key_simple(self):
        lo = ListOutput()
        self.assertEqual(lo._formatted_keys_cache, {})
        lo._get_formatted_key('locationId')
        self.assertEqual(lo._formatted_keys_cache, {'locationId': 'Location Id'})

    def test_out_list_format_key_single(self):
        lo = ListOutput()
        self.assertEqual(lo._formatted_keys_cache, {})
        lo._get_formatted_key('location')
        self.assertEqual(lo._formatted_keys_cache, {'location': 'Location'})

    def test_out_list_format_key_multiple_caps(self):
        lo = ListOutput()
        self.assertEqual(lo._formatted_keys_cache, {})
        lo._get_formatted_key('fooIDS')
        self.assertEqual(lo._formatted_keys_cache, {'fooIDS': 'Foo I D S'})

    def test_out_list_format_key_multiple_words(self):
        lo = ListOutput()
        self.assertEqual(lo._formatted_keys_cache, {})
        lo._get_formatted_key('locationIdState')
        self.assertEqual(lo._formatted_keys_cache, {'locationIdState': 'Location Id State'})

    # TSV output tests
    def test_output_format_dict(self):
        obj = {}
        obj['A'] = 1
        obj['B'] = 2
        result = format_tsv(obj)
        self.assertEquals(result, '1\t2\n')

    def test_output_format_dict_sort(self):
        obj = {}
        obj['B'] = 1
        obj['A'] = 2
        result = format_tsv(obj)
        self.assertEquals(result, '2\t1\n')

    def test_output_format_ordereddict_not_sorted(self):
        from collections import OrderedDict
        obj = OrderedDict()
        obj['B'] = 1
        obj['A'] = 2
        result = format_tsv(obj)
        self.assertEquals(result, '1\t2\n')

    def test_output_format_ordereddict_list_not_sorted(self):
        from collections import OrderedDict
        obj1 = OrderedDict()
        obj1['B'] = 1
        obj1['A'] = 2

        obj2 = OrderedDict()
        obj2['A'] = 3
        obj2['B'] = 4
        result = format_tsv([obj1, obj2])
        self.assertEquals(result, '1\t2\n3\t4\n')

if __name__ == '__main__':
    unittest.main()
