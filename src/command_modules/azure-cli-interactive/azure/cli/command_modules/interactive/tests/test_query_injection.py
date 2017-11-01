# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import six
import os
import json
from azclishell.util import parse_quotes
from azclishell.gather_commands import GatherCommands


def pass_gather(_):
    pass


GatherCommands._gather_from_files = pass_gather


# pylint: disable=too-few-public-methods
class MockValues(object):
    def __init__(self):
        self.result = None


class QueryInjection(unittest.TestCase):
    """ tests using the query gesture for the interactive mode """
    def __init__(self, *args, **kwargs):
        super(QueryInjection, self).__init__(*args, **kwargs)
        from azclishell.app import Shell

        self.stream = six.StringIO()
        self.shell = Shell(output_custom=self.stream)
        self.shell.cli_execute = self._mock_execute
        self.shell.last = MockValues()

    def _mock_execute(self, cmd):
        self.stream.write(cmd)
        self.stream.write(os.linesep)

    def test_print_last_command(self):
        # tests getting last command result
        args = ['??']
        self.shell.last.result = {'x': 'result'}
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        self.assertEqual(json.loads(self.stream.getvalue()), {'x': 'result'})

    def test_print_just_query(self):
        # tests flushing just the query
        args = ['??x']
        self.shell.last.result = {'x': 'result'}
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        self.assertEqual(json.loads(self.stream.getvalue()), 'result')

    def test_print_list_replacement(self):
        # tests that the query replaces the values in the command
        args = '??[].group'
        args = parse_quotes(args)
        self.shell.last.result = [
            {
                'group': 'mygroup',
                'name': 'myname'
            },
            {
                'group': 'mygroup2',
                'name': 'myname2'
            },
            {
                'group': 'mygroup3',
                'name': 'myname3'
            }
        ]
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        self.assertEqual(json.loads(self.stream.getvalue()), ['mygroup', 'mygroup2', 'mygroup3'])

    def test_usage_error(self):
        # tests case when multiple args but first arg starts with query
        args = '??[].group foo bar'
        args = parse_quotes(args)
        self.shell.last.result = {
            'group': 'mygroup',
            'name': 'myname'
        }
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        self.assertEqual(self.stream.getvalue().strip(),
                         "Usage Error: " + os.linesep +
                         "1. Use ?? stand-alone to display previous result with optional filtering "
                         "(Ex: ??[jmespath query])" +
                         os.linesep + "OR:" + os.linesep +
                         "2. Use ?? to query the previous result for argument values "
                         "(Ex: group show --name ??[jmespath query])")

    def test_string_replacement(self):
        # tests that the query replaces the values in the command
        args = 'vm show -g "??group" -n "??name"'
        args = parse_quotes(args)
        self.shell.last.result = {
            'group': 'mygroup',
            'name': 'myname'
        }
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        results = self.stream.getvalue().split(os.linesep)
        self.assertEqual(results[0], '"vm" "show" "-g" "mygroup" "-n" "myname"')

    def test_list_replacement(self):
        # tests that the query replaces the values in the command
        args = 'foo update --set blah=??[].group'
        args = parse_quotes(args)
        self.shell.last.result = [
            {
                'group': 'mygroup',
                'name': 'myname'
            },
            {
                'group': 'mygroup2',
                'name': 'myname2'
            },
            {
                'group': 'mygroup3',
                'name': 'myname3'
            }
        ]
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        results = self.stream.getvalue().strip().split(os.linesep)
        self.assertTrue(len(results) == 1)
        self.assertEqual(results[0], '"foo" "update" "--set" "blah=[\'mygroup\', \'mygroup2\', \'mygroup3\']"')

    def test_quotes(self):
        # tests that it parses correctly with quotes in the command
        self.shell.last.result = {'x': 'result'}
        # pylint: disable=protected-access
        b_flag, c_flag, out, cmd = self.shell._special_cases(
            "this is 'url?what' negative", False)
        self.assertFalse(b_flag)
        self.assertFalse(c_flag)
        self.assertFalse(out)
        self.assertEqual(cmd, "this is 'url?what' negative")

    def test_errors(self):
        # tests invalid query
        args = 'vm show -g "??[0].group" -n "??[1].name"'
        args = parse_quotes(args)
        self.shell.last.result = [
            {
                'group': 'mygroup',
                'name': 'myname'
            },
            {
                'group': 'mygroup3',
            }
        ]
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        results = self.stream.getvalue().split(os.linesep)
        self.assertEqual(results[0], '"vm" "show" "-g" "mygroup" "-n" "None"')

    def test_query_result_spaces(self):
        # tests a singleton example
        args = 'vm show -g "??group" -n "??name"'
        args = parse_quotes(args)
        self.shell.last.result = {
            'group': 'mygroup',
            'name': 'my name'
        }
        flag = self.shell.handle_jmespath_query(args)
        self.assertTrue(flag)
        results = self.stream.getvalue().split(os.linesep)
        self.assertEqual(results[0], '"vm" "show" "-g" "mygroup" "-n" "my name"')

    def test_spaces(self):
        # tests quotes with spaces
        args = 'foo update --set "bar=??[?group == \'mygroup\'].name"'
        args = parse_quotes(args)
        self.shell.last.result = [
            {
                'group': 'mygroup',
                'name': 'fred'
            },
            {
                'group': 'mygroup3',
                'name': 'myname3'
            }
        ]

        self.shell.handle_jmespath_query(args)
        results = self.stream.getvalue().split(os.linesep)
        self.assertEqual(results[0], '"foo" "update" "--set" "bar=[\'fred\']"')

    def test_spaces_with_equal(self):
        # tests quotes with spaces
        args = 'foo doo -bar="??[?group == \'myg roup\'].name"'
        args = parse_quotes(args)
        self.shell.last.result = [
            {
                'group': 'myg roup',
                'name': 'fred'
            },
            {
                'group': 'mygroup3',
                'name': 'myname3'
            }
        ]

        self.shell.handle_jmespath_query(args)
        results = self.stream.getvalue().split(os.linesep)
        self.assertEqual(results[0], '"foo" "doo" "-bar=[\'fred\']"')
