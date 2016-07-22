#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import logging
import unittest

from azure.cli.application import Application, Configuration
from azure.cli.commands.arm import register_generic_update
from azure.cli._util import CLIError

#pylint:disable=invalid-sequence-index

class GenericUpdateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger().setLevel(logging.ERROR)

    def test_generic_update(self):
        my_obj = {
            'prop': 'val',
            'list': [
                'a',
                'b',
                ['c', {'d': 'e'}]
                ]
            }

        def my_get():
            return my_obj

        def my_set(**kwargs): #pylint:disable=unused-argument
            return my_obj

        config = Configuration([])
        app = Application(config)

        register_generic_update('gencommand', my_get, my_set)

        app.execute('gencommand --set prop=val2'.split())
        self.assertEqual(my_obj['prop'], 'val2', 'set simple property')

        app.execute('gencommand --set prop=val3'.split())
        self.assertEqual(my_obj['prop'], 'val3', 'set simple property again')

        app.execute('gencommand --set list[0]=f'.split())
        self.assertEqual(my_obj['list'][0], 'f', 'set simple list element')

        app.execute('gencommand --set list[2][0]=g'.split())
        self.assertEqual(my_obj['list'][2][0], 'g', 'set nested list element')

        app.execute('gencommand --set list[2][1].d=h'.split())
        self.assertEqual(my_obj['list'][2][1]['d'], 'h', 'set nested dict element')

        app.execute('gencommand --set list[0]={} list[0].foo=bar'.split())
        self.assertEqual(my_obj['list'][0]['foo'], 'bar', 'replace nested scalar with new dict')

        app.execute('gencommand --set list[1]=[] --add list[1] key1=value1'
                    ' --set list[1][0].key2=value2'.split())
        self.assertEqual(my_obj['list'][1][0]['key1'], 'value1',
                         'replace nested scalar with new list with one value')
        self.assertEqual(my_obj['list'][1][0]['key2'], 'value2',
                         'add a second value to the new list')

        app.execute('gencommand --add list i=j k=l'.split())
        self.assertEqual(my_obj['list'][-1]['k'], 'l',
                         'add multiple values to a list at once (verify last element)')
        self.assertEqual(my_obj['list'][-1]['i'], 'j',
                         'add multiple values to a list at once (verify first element)')

        app.execute('gencommand --add list[-2] prop2=val2'.split())
        self.assertEqual(my_obj['list'][-2][-1]['prop2'], 'val2', 'add to list')
        app.execute('gencommand --add list[-2] prop3=val3'.split())
        self.assertEqual(my_obj['list'][-2][-1]['prop3'], 'val3',
                         'add to list again, should make seperate list elements')

        self.assertEqual(len(my_obj['list']), 4, 'pre-verify length of list')
        app.execute('gencommand --remove list -2'.split())
        self.assertEqual(len(my_obj['list']), 3, 'verify one item removed')
        app.execute('gencommand --remove list -1'.split())
        self.assertEqual(len(my_obj['list']), 2, 'verify another item removed')

        self.assertEqual('key1' in my_obj['list'][1][0], True, 'verify dict item')
        app.execute('gencommand --remove list[1][0].key1'.split())
        self.assertEqual('key1' not in my_obj['list'][1][0], True,
                         'verify dict item can be removed')

    def test_generic_update_errors(self):
        my_obj = {
            'prop': 'val',
            'list': [
                'a',
                'b',
                ['c', {'d': 'e'}]
                ]
            }

        def my_get(a1, a2): #pylint: disable=unused-argument
            return my_obj

        def my_set(**kwargs): #pylint:disable=unused-argument
            return my_obj

        config = Configuration([])
        app = Application(config)

        register_generic_update('gencommand', my_get, my_set)

        def _execute_with_error(command, error, message):
            try:
                app.execute(command.split())
            except CLIError as err:
                self.assertEqual(error in str(err), True, message)
            else:
                raise AssertionError('exception not thrown')

        missing_remove_message = """Couldn't find "doesntExist" in "".""" + \
                                 """  Available options: ['list', 'prop']"""
        _execute_with_error('gencommand --a1 1 --a2 2 --remove doesnt_exist',
                            missing_remove_message,
                            'remove non-existent property by name')
        _execute_with_error('gencommand --a1 1 --a2 2 --remove doesntExist 2',
                            missing_remove_message,
                            'remove non-existent property by index')

        remove_prop_message = """Couldn't find "doesntExist" in "list.doesntExist".""" + \
                              """  Available options: [['c', {'d': 'e'}], 'a', 'b']"""
        _execute_with_error('gencommand --a1 1 --a2 2 --remove list.doesnt_exist.missing 2',
                            remove_prop_message,
                            'remove non-existent sub-property by index')

        _execute_with_error('gencommand --a1 1 --a2 2 --remove list 20',
                            "index 20 doesn't exist on list",
                            'remove out-of-range index')

        set_on_list_message = """Couldn't find "doesntExist" in "list".""" + \
                              """  Available options: [['c', {'d': 'e'}], 'a', 'b']"""
        _execute_with_error('gencommand --a1 1 --a2 2 --set list.doesnt_exist=foo',
                            set_on_list_message,
                            'set shouldn\'t work on a list')
        _execute_with_error('gencommand --a1 1 --a2 2 --set list.doesnt_exist.doesnt_exist2=foo',
                            set_on_list_message,
                            'set shouldn\'t work on a list')

        _execute_with_error('gencommand --a1 1 --a2 2 --set list[2][3].doesnt_exist=foo',
                            "index 3 doesn't exist on [2]",
                            'index out of range in path')
