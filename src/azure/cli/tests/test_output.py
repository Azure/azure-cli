from __future__ import print_function

import unittest

try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO

from azure.cli._output import OutputProducer, OutputFormatException, format_json, format_table, format_text
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

if __name__ == '__main__':
    unittest.main()
