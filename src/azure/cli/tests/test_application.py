#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import unittest
from collections import namedtuple

from six import StringIO

from azure.cli.application import Application, Configuration, IterateAction
from azure.cli.commands import CliCommand

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
        the_input = None
        actual = Application.todict(the_input)
        expected = None
        self.assertEqual(actual, expected)

    def test_application_todict_dict_empty(self):
        the_input = {}
        actual = Application.todict(the_input)
        expected = {}
        self.assertEqual(actual, expected)

    def test_application_todict_dict(self):
        the_input = {'a': 'b'}
        actual = Application.todict(the_input)
        expected = {'a': 'b'}
        self.assertEqual(actual, expected)

    def test_application_todict_list(self):
        the_input = [{'a': 'b'}]
        actual = Application.todict(the_input)
        expected = [{'a': 'b'}]
        self.assertEqual(actual, expected)

    def test_application_todict_obj(self):
        MyObject = namedtuple('MyObject', 'a b')
        the_input = MyObject('x', 'y')
        actual = Application.todict(the_input)
        expected = {'a': 'x', 'b': 'y'}
        self.assertEqual(actual, expected)

    def test_application_todict_dict_with_obj(self):
        MyObject = namedtuple('MyObject', 'a b')
        mo = MyObject('x', 'y')
        the_input = {'a': mo}
        actual = Application.todict(the_input)
        expected = {'a': {'a': 'x', 'b': 'y'}}
        self.assertEqual(actual, expected)

    def test_application_register_and_call_handlers(self):
        handler_called = [False]

        def handler(**kwargs):
            kwargs['args'][0] = True

        def other_handler(**kwargs): # pylint: disable=unused-variable
            self.assertEqual(kwargs['args'], 'secret sauce')

        config = Configuration([])
        app = Application(config)

        app.raise_event('was_handler_called', args=handler_called)
        self.assertFalse(handler_called[0],
                         "Raising event with no handlers registered somehow failed...")

        app.register('was_handler_called', handler)
        self.assertFalse(handler_called[0])

        # Registered handler won't get called if event with different name
        # is raised...
        app.raise_event('other_handler_called', args=handler_called)
        self.assertFalse(handler_called[0], 'Wrong handler called!')

        app.raise_event('was_handler_called', args=handler_called)
        self.assertTrue(handler_called[0], "Handler didn't get called")

        app.raise_event('other_handler_called', args='secret sauce')



    def test_list_value_parameter(self):
        hellos = []

        def handler(args):
            hellos.append(args)

        command = CliCommand('test command', handler)
        command.add_argument('hello', '--hello', nargs='+', action=IterateAction)
        command.add_argument('something', '--something')
        cmd_table = {'test command': command}

        argv = 'az test command --hello world sir --something else'.split()
        config = Configuration(argv)
        config.get_command_table = lambda: cmd_table
        application = Application(config)
        application.execute(argv[1:])

        self.assertEqual(2, len(hellos))
        self.assertEqual(hellos[0]['hello'], 'world')
        self.assertEqual(hellos[0]['something'], 'else')
        self.assertEqual(hellos[1]['hello'], 'sir')
        self.assertEqual(hellos[1]['something'], 'else')

if __name__ == '__main__':
    unittest.main()
