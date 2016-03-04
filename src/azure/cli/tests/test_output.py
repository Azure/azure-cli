from __future__ import print_function

import unittest

try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO

from azure.cli._output import OutputProducer, OutputFormatException, format_json, format_table, format_list, format_text
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
        """
        """
        output_producer = OutputProducer(formatter=format_table, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""active |    id   
-------|---------
True   | 0b1f6472

"""))

    def test_out_list_valid(self):
        """
        """
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active : True
Id     : 0b1f6472


"""))

    def test_out_list_valid_array_complex(self):
        """
        """
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
        """
        """
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out(['location', 'id', 'host', 'server'])
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""location

id

host

server


"""))

    def test_out_list_valid_complex_array(self):
        """
        """
        output_producer = OutputProducer(formatter=format_list, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472', 'myarray': ['1', '2', '3', '4']})
        self.assertEqual(util.normalize_newlines(self.io.getvalue()), util.normalize_newlines(
"""Active : True
Id     : 0b1f6472

  MYARRAY
  1
  2
  3
  4


"""))

if __name__ == '__main__':
    unittest.main()
