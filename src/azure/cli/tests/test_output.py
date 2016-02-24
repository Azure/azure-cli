import unittest

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

from azure.cli._output import OutputProducer, OutputFormats, OutputFormatException

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
        
    def test_unknown_format(self):
        """
        Should through exception if format is unknown
        """
        with self.assertRaises(OutputFormatException):
            output_producer = OutputProducer(format='unknown')
        
        
    def test_default_format_json(self):
        """
        We expect the default format to be JSON
        """
        output_producer = OutputProducer()
        self.assertEqual(output_producer.format, OutputFormats.JSON)

    def test_set_format_table(self):
        """
        The format used can be set to table
        """
        output_producer = OutputProducer(format=OutputFormats.TABLE)
        self.assertEqual(output_producer.format, OutputFormats.TABLE)

    def test_set_format_text(self):
        """
        The format used can be set to text
        """
        output_producer = OutputProducer(format=OutputFormats.TEXT)
        self.assertEqual(output_producer.format, OutputFormats.TEXT)

    def test_out_json_none(self):
        """
        The JSON output when the input is None is 'null'
        """
        output_producer = OutputProducer(format=OutputFormats.JSON, file=self.io)
        output_producer.out(None)
        self.assertEqual(self.io.getvalue(), 'null\n')

    def test_out_json_valid(self):
        """
        The JSON output when the input is a dict should be the dict serialized to JSON
        """
        output_producer = OutputProducer(format=OutputFormats.JSON, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(self.io.getvalue(),
"""{
    "active": true,
    "id": "0b1f6472"
}
"""
        )

    def test_out__table_none(self):
        """
        The table format just returns a new line if object None is passed in.
        """
        output_producer = OutputProducer(format=OutputFormats.TABLE, file=self.io)
        output_producer.out(None)
        self.assertEqual(self.io.getvalue(), '\n')

    def test_out_table_valid(self):
        """
        """
        output_producer = OutputProducer(format=OutputFormats.TABLE, file=self.io)
        output_producer.out({'active': True, 'id': '0b1f6472'})
        self.assertEqual(self.io.getvalue(),
"""active |    id   
-------|---------
True   | 0b1f6472

"""
        )

    def test_out_text_none(self):
        """
        The text format just returns a new line if object None is passed in.
        """
        output_producer = OutputProducer(format=OutputFormats.TEXT, file=self.io)
        output_producer.out(None)
        self.assertEqual(self.io.getvalue(), '\n')



if __name__ == '__main__':
    unittest.main()
