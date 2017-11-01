# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import unittest
import shlex
from six import StringIO
import sys

from azure.cli.core import AzCommandsLoader

from azure.cli.testsdk import TestCli

from knack.arguments import CLIArgumentType
from knack.util import CLIError


class ListTestObject(object):

    def __init__(self, val):
        self.list_value = list(val)


class DictTestObject(object):

    def __init__(self, val):
        self.dict_value = dict(val)


class ObjectTestObject(object):

    def __init__(self, str_val, int_val, bool_val):
        self.my_string = str(str_val)
        self.my_int = int(int_val)
        self.my_bool = bool(bool_val)


class TestObject(object):

    def __init__(self):
        self.my_prop = 'my_value'
        self.my_list = [
            'myValA',
            ['myValB', 'myValC'],
            {'myKey': 'valueA'},
            ObjectTestObject('myString', 0, True)
        ]
        self.my_dict = {}
        self.my_list_of_camel_dicts = [
            {'myKey': 'value_1'},
            {'myKey': 'value_2'}
        ]
        self.my_list_of_snake_dicts = [
            {'my_key': 'value1'},
            {'my_key': 'value2'}
        ]
        self.my_list_of_objects = [
            ObjectTestObject('myKeyA', 25, True),
            ObjectTestObject('1.2.3.4', 100, False),
        ]


class GenericUpdateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.getLogger().setLevel(logging.ERROR)

    def test_generic_update(self):  # pylint: disable=too-many-statements

        my_obj = TestObject()

        class GenericUpdateTestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(GenericUpdateTestCommandsLoader, self).load_command_table(args)

                def my_get():
                    return my_obj

                def my_set(**kwargs):  # pylint:disable=unused-argument
                    return my_obj

                setattr(sys.modules[__name__], my_get.__name__, my_get)
                setattr(sys.modules[__name__], my_set.__name__, my_set)
                with self.command_group('', operations_tmpl='{}#{{}}'.format(__name__)) as g:
                    g.generic_update_command('update-obj', 'my_get', 'my_set')

                return self.command_table

        cli = TestCli(commands_loader_cls=GenericUpdateTestCommandsLoader)

        # Test simplest ways of setting properties
        cli.invoke('update-obj --set myProp=newValue'.split())
        self.assertEqual(my_obj.my_prop, 'newValue', 'set simple property')

        cli.invoke('update-obj --set myProp=val3'.split())
        self.assertEqual(my_obj.my_prop, 'val3', 'set simple property again')

        cli.invoke('update-obj --set myProp="foo=bar"'.split())
        self.assertEqual(my_obj.my_prop, 'foo=bar', 'use equal in value')

        cli.invoke('update-obj --set myList[0]=newValA'.split())
        self.assertEqual(my_obj.my_list[0], 'newValA', 'set simple list element')

        cli.invoke('update-obj --set myList[-4]=newValB'.split())
        self.assertEqual(my_obj.my_list[0], 'newValB', 'set simple list element')

        cli.invoke('update-obj --set myDict.myCamelKey=success'.split())
        self.assertEqual(my_obj.my_dict['myCamelKey'], 'success',
                         'set simple dict element with camel case key')

        cli.invoke('update-obj --set myDict.my_snake_key=success'.split())
        self.assertEqual(my_obj.my_dict['my_snake_key'], 'success',
                         'set simple dict element with snake case key')

        # Test the different ways of indexing into a list of objects or dictionaries by filter
        cli.invoke('update-obj --set myListOfCamelDicts[myKey=value_2].myKey="foo=bar"'.split())
        self.assertEqual(my_obj.my_list_of_camel_dicts[1]['myKey'],
                         'foo=bar',
                         'index into list of dictionaries by camel-case key and set value with =')

        cli.invoke('update-obj --set myListOfCamelDicts[myKey="foo=bar"].myKey=new_value'.split())
        self.assertEqual(my_obj.my_list_of_camel_dicts[1]['myKey'],
                         'new_value',
                         'index into list of dictionaries by camel-case key')

        cli.invoke('update-obj --set myListOfSnakeDicts[my_key=value2].my_key=new_value'.split())
        self.assertEqual(my_obj.my_list_of_snake_dicts[1]['my_key'],
                         'new_value',
                         'index into list of dictionaries by snake-case key')

        cli.invoke('update-obj --set myListOfObjects[myString=1.2.3.4].myString=new_value'.split())
        self.assertEqual(my_obj.my_list_of_objects[1].my_string,
                         'new_value',
                         'index into list of objects by key')

        # Test setting on elements nested within lists
        cli.invoke('update-obj --set myList[1][1]=newValue'.split())
        self.assertEqual(my_obj.my_list[1][1], 'newValue', 'set nested list element')

        cli.invoke('update-obj --set myList[2].myKey=newValue'.split())
        self.assertEqual(my_obj.my_list[2]['myKey'], 'newValue', 'set nested dict element')

        cli.invoke('update-obj --set myList[3].myInt=50'.split())
        self.assertEqual(my_obj.my_list[3].my_int, 50, 'set nested object element')

        # Test overwriting and removing values
        cli.invoke('update-obj --set myProp={} myProp.foo=bar'.split())
        self.assertEqual(my_obj.my_prop['foo'], 'bar', 'replace scalar with dict')

        cli.invoke(
            'update-obj --set myProp=[] --add myProp key1=value1 --set myProp[0].key2=value2'.split())
        self.assertEqual(my_obj.my_prop[0]['key1'], 'value1',
                         'replace scalar with new list and add a dict entry')
        self.assertEqual(my_obj.my_prop[0]['key2'], 'value2',
                         'add a second value to the new dict entry')

        cli.invoke('update-obj --remove myProp --add myProp str1 str2 --remove myProp 0'.split())
        self.assertEqual(len(my_obj.my_prop), 1, 'nullify property, add two and remove one')
        self.assertEqual(my_obj.my_prop[0], 'str2', 'nullify property, add two and remove one')

        # Test various --add to lists
        cli.invoke('update-obj --set myList=[]'.split())
        cli.invoke(shlex.split(
            'update-obj --add myList key1=value1 key2=value2 foo "string in quotes" [] {} foo=bar'))
        self.assertEqual(my_obj.my_list[0]['key1'], 'value1', 'add a value to a dictionary')
        self.assertEqual(my_obj.my_list[0]['key2'], 'value2',
                         'add a second value to the dictionary')
        self.assertEqual(my_obj.my_list[1], 'foo', 'add scalar value to list')
        self.assertEqual(my_obj.my_list[2], 'string in quotes',
                         'add scalar value with quotes to list')
        self.assertEqual(my_obj.my_list[3], [], 'add list to a list')
        self.assertEqual(my_obj.my_list[4], {}, 'add dict to a list')
        self.assertEqual(my_obj.my_list[-1]['foo'], 'bar',
                         'add second dict and verify when dict is at the end')

        # Test --remove
        self.assertEqual(len(my_obj.my_list), 6, 'pre-verify length of list')
        cli.invoke('update-obj --remove myList -2'.split())
        self.assertEqual(len(my_obj.my_list), 5, 'verify one item removed')
        self.assertEqual(my_obj.my_list[4]['foo'], 'bar', 'verify correct item removed')

        self.assertEqual('key1' in my_obj.my_list[0], True, 'verify dict item exists')
        cli.invoke('update-obj --remove myList[0].key1'.split())
        self.assertEqual('key1' not in my_obj.my_list[0], True, 'verify dict entry can be removed')

    def test_generic_update_errors(self):  # pylint: disable=no-self-use

        my_obj = TestObject()

        class GenericUpdateTestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(GenericUpdateTestCommandsLoader, self).load_command_table(args)

                def my_get(a1, a2):
                    return my_obj

                def my_set(**kwargs):  # pylint:disable=unused-argument
                    return my_obj

                setattr(sys.modules[__name__], my_get.__name__, my_get)
                setattr(sys.modules[__name__], my_set.__name__, my_set)

                with self.command_group('', operations_tmpl='{}#{{}}'.format(__name__)) as g:
                    g.generic_update_command('gencommand', 'my_get', 'my_set')

                return self.command_table

        cli = TestCli(commands_loader_cls=GenericUpdateTestCommandsLoader)

        def _execute_with_error(command, error, message):
            try:
                cli.invocation = cli.invocation_cls(cli_ctx=cli, parser_cls=cli.parser_cls,
                                                    commands_loader_cls=cli.commands_loader_cls, help_cls=cli.help_cls)
                cli.invocation.execute(command.split())
            except CLIError as ex:
                if error not in str(ex):
                    raise AssertionError('{}\nExpected: {}\nActual: {}'.format(message, error, ex))
                return
            raise AssertionError("exception not raised for ''".format(message))

        missing_remove_message = "Couldn't find 'doesntExist' in ''. Available options: ['myDict', 'myList', 'myListOfCamelDicts', 'myListOfObjects', 'myListOfSnakeDicts', 'myProp']"
        _execute_with_error('gencommand --a1 1 --a2 2 --remove doesntExist',
                            missing_remove_message,
                            'remove non-existent property by name')
        _execute_with_error('gencommand --a1 1 --a2 2 --remove doesntExist 2',
                            missing_remove_message,
                            'remove non-existent property by index')

        remove_prop_message = "Couldn't find 'doesntExist' in 'myList.doesntExist'. Available options: index into the collection 'myList.doesntExist' with [<index>] or [<key=value>]"
        _execute_with_error('gencommand --a1 1 --a2 2 --remove myList.doesntExist.missing 2',
                            remove_prop_message,
                            'remove non-existent sub-property by index')

        _execute_with_error('gencommand --a1 1 --a2 2 --remove myList 20',
                            "index 20 doesn't exist on myList",
                            'remove out-of-range index')

        set_on_list_message = "Couldn't find 'doesnt_exist' in 'myList'. Available options: index into the collection 'myList' with [<index>] or [<key=value>]"
        _execute_with_error('gencommand --a1 1 --a2 2 --set myList.doesnt_exist=foo',
                            set_on_list_message,
                            'set shouldn\'t work on a list')
        _execute_with_error('gencommand --a1 1 --a2 2 --set myList.doesnt_exist.doesnt_exist2=foo',
                            set_on_list_message,
                            'set shouldn\'t work on a list')

        _execute_with_error('gencommand --a1 1 --a2 2 --set myList[5].doesnt_exist=foo',
                            "index 5 doesn't exist on myList",
                            'index out of range in path')

        _execute_with_error('gencommand --a1 1 --a2 2 --remove myList[0]',
                            'invalid syntax: --remove property.list <indexToRemove> OR --remove propertyToRemove',
                            'remove requires index to be space-separated')

        cli.invoke("gencommand --a1 1 --a2 2 --set myDict={'foo':'bar'}".split())
        _execute_with_error('gencommand --a1 1 --a2 2 --set myDict.foo.doo=boo',
                            "Couldn't find 'doo' in 'myDict.foo'. 'myDict.foo' does not support further indexing.",
                            'Cannot dot index from a scalar value')

        _execute_with_error('gencommand --a1 1 --a2 2 --set myDict.foo[0]=boo',
                            "Couldn't find '[0]' in 'myDict'. 'myDict' does not support further indexing.",
                            'Cannot list index from a scalar value')

        _execute_with_error('gencommand --a1 1 --a2 2 --add myDict la=da',
                            "invalid syntax: --add property.listProperty <key=value, string or JSON string>",
                            'Add only works with lists')

        # add an entry which makes 'myKey' no longer unique
        cli.invoke('gencommand --a1 1 --a2 2 --add myListOfCamelDicts myKey=value_2'.split())
        _execute_with_error(
            'gencommand --a1 1 --a2 2 --set myListOfCamelDicts[myKey=value_2].myKey=foo',
            "non-unique key 'myKey' found multiple matches on myListOfCamelDicts. "
            "Key must be unique.",
            'indexing by key must be unique')

        _execute_with_error(
            'gencommand --a1 1 --a2 2 --set myListOfCamelDicts[myKey=foo].myKey=foo',
            "item with value 'foo' doesn\'t exist for key 'myKey' on myListOfCamelDicts",
            'no match found when indexing by key and value')

    def test_generic_update_empty_nodes(self):
        my_obj = {
            'prop': None,
            'list': [],
            'dict': {
                'dict2': None
            },
            'dict3': {}
        }

        class GenericUpdateTestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(GenericUpdateTestCommandsLoader, self).load_command_table(args)

                def my_get():
                    return my_obj

                def my_set(**kwargs):  # pylint:disable=unused-argument
                    return my_obj

                setattr(sys.modules[__name__], my_get.__name__, my_get)
                setattr(sys.modules[__name__], my_set.__name__, my_set)

                with self.command_group('', operations_tmpl='{}#{{}}'.format(__name__)) as g:
                    g.generic_update_command('gencommand', 'my_get', 'my_set')

                return self.command_table

        cli = TestCli(commands_loader_cls=GenericUpdateTestCommandsLoader)

        # add to prop
        cli.invoke('gencommand --add prop a=b'.split())
        self.assertEqual(my_obj['prop'][0]['a'], 'b', 'verify object added to null list')
        self.assertEqual(len(my_obj['prop'][0]), 1, 'verify only one object added to null list')

        # add to list
        cli.invoke('gencommand --add list c=d'.split())
        self.assertEqual(my_obj['list'][0]['c'], 'd', 'verify object added to empty list')
        self.assertEqual(len(my_obj['list']), 1, 'verify only one object added to empty list')

        # set dict2
        cli.invoke('gencommand --set dict.dict2.e=f'.split())
        self.assertEqual(my_obj['dict']['dict2']['e'], 'f', 'verify object added to null dict')
        self.assertEqual(len(my_obj['dict']['dict2']), 1,
                         'verify only one object added to null dict')

        # set dict3
        cli.invoke('gencommand --set dict3.g=h'.split())
        self.assertEqual(my_obj['dict3']['g'], 'h', 'verify object added to empty dict')
        self.assertEqual(len(my_obj['dict3']), 1, 'verify only one object added to empty dict')


if __name__ == '__main__':
    unittest.main()
