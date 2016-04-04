import unittest
from six import StringIO
from collections import namedtuple
from azure.cli.application import Application, Configuration

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

    def test_application_todict_none(self):
        input = None
        actual = Application.todict(input)
        expected = None
        self.assertEqual(actual, expected)

    def test_application_todict_dict_empty(self):
        input = {}
        actual = Application.todict(input)
        expected = {}
        self.assertEqual(actual, expected)

    def test_application_todict_dict(self):
        input = {'a': 'b'}
        actual = Application.todict(input)
        expected = {'a': 'b'}
        self.assertEqual(actual, expected)

    def test_application_todict_list(self):
        input = [{'a': 'b'}]
        actual = Application.todict(input)
        expected = [{'a': 'b'}]
        self.assertEqual(actual, expected)

    def test_application_todict_list(self):
        input = [{'a': 'b'}]
        actual = Application.todict(input)
        expected = [{'a': 'b'}]
        self.assertEqual(actual, expected)

    def test_application_todict_obj(self):
        MyObject = namedtuple('MyObject', 'a b')
        input = MyObject('x', 'y')
        actual = Application.todict(input)
        expected = {'a': 'x', 'b': 'y'}
        self.assertEqual(actual, expected)

    def test_application_todict_dict_with_obj(self):
        MyObject = namedtuple('MyObject', 'a b')
        mo = MyObject('x', 'y')
        input = {'a': mo}
        actual = Application.todict(input)
        expected = {'a': {'a': 'x', 'b': 'y'}}
        self.assertEqual(actual, expected)

    def test_application_register_and_call_handlers(self):
        handler_called = [False]

        def handler(args):
            args[0] = True

        def other_handler(args):
            self.assertEqual(args, 'secret sauce')

        config = Configuration([])
        app = Application(config)

        app.raise_event('was_handler_called', handler_called)
        self.assertFalse(handler_called[0], "Raising event with no handlers registered somehow failed...")

        app.register('was_handler_called', handler)
        self.assertFalse(handler_called[0])

        # Registered handler won't get called if event with different name
        # is raised...
        app.raise_event('other_handler_called', handler_called)
        self.assertFalse(handler_called[0], 'Wrong handler called!')
        
        app.raise_event('was_handler_called', handler_called)
        self.assertTrue(handler_called[0], "Handler didn't get called")

        app.raise_event('other_handler_called', 'secret sauce')

if __name__ == '__main__':
    unittest.main()
