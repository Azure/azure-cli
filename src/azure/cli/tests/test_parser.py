import unittest
from six import StringIO
from collections import namedtuple
from azure.cli.parser import AzCliCommandParser

#class TestParser(unittest.TestCase):

#    @classmethod
#    def setUpClass(cls):
#        pass
        
#    @classmethod
#    def tearDownClass(cls):
#        pass

#    def setUp(self):
#        self.io = StringIO()
        
#    def tearDown(self):
#        self.io.close()

#    def test_register_simple_commands(self):
#        def test_handler1(args):
#            pass

#        def test_handler2(args):
#            pass

#        command_table = {
#            'command the-name': {
#                'handler': test_handler1,
#                'arguments': []
#                },
#            'sub-command the-second-name': {
#                'handler': test_handler2,
#                'arguments': []
#                }
#            }
#        parser = AzCliCommandParser()
        
#        parser.load_command_table(command_table)
#        args = parser.parse_args('command the-name'.split())
#        self.assertIs(args.func, test_handler1)

#        args = parser.parse_args('sub-command the-second-name'.split())
#        self.assertIs(args.func, test_handler2)

#        AzCliCommandParser.error = VerifyError(self,)
#        parser.parse_args('sub-command'.split())
#        self.assertTrue(AzCliCommandParser.error.called)

#    def test_required_parameter(self):
#        def test_handler(args):
#            pass

#        command_table = {
#            'test command': {
#                'handler': test_handler,
#                'arguments': [
#                    {'name': '--req', 'required': True}
#                    ]
#                }
#            }
#        parser = AzCliCommandParser()
#        parser.load_command_table(command_table)

#        args = parser.parse_args('test command --req yep'.split())
#        self.assertIs(args.func, test_handler)

#        AzCliCommandParser.error = VerifyError(self)
#        parser.parse_args('test command'.split())
#        self.assertTrue(AzCliCommandParser.error.called)

#    def test_nargs_parameter(self):
#        def test_handler(args):
#            pass

#        command_table = {
#            'test command': {
#                'handler': test_handler,
#                'arguments': [
#                    {'name': '--req', 'required': True, 'nargs': 2}
#                    ]
#                }
#            }
#        parser = AzCliCommandParser()
#        parser.load_command_table(command_table)

#        args = parser.parse_args('test command --req yep nope'.split())
#        self.assertIs(args.func, test_handler)

#        AzCliCommandParser.error = VerifyError(self)
#        parser.parse_args('test command -req yep'.split())
#        self.assertTrue(AzCliCommandParser.error.called)

#class VerifyError(object):

#    def __init__(self, test, substr=None):
#        self.test = test
#        self.substr= substr
#        self.called = False

#    def __call__(self, message):
#        if self.substr:
#            self.test.assertTrue(message.find(self.substr) >= 0)
#        self.called = True

#if __name__ == '__main__':
#    unittest.main()
