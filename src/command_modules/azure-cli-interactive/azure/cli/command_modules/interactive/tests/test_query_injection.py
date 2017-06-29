# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import six
from azclishell.util import parse_quotes
from azclishell.gather_commands import GatherCommands


def pass_gather(_):
    pass


GatherCommands.gather_from_files = pass_gather


# pylint: disable=too-few-public-methods
class MockValues(object):
    def __init__(self):
        self.result = None


class QueryInjection(unittest.TestCase):
    """ tests using the query gesture for the interactive mode """
    def __init__(self, *args, **kwargs):
        super(QueryInjection, self).__init__(*args, **kwargs)
        from azclishell.app import Shell, validate_contains_query

        self.stream = six.StringIO()
        self.shell = Shell(output_custom=self.stream)
        self.shell.cli_execute = self._mock_execute
        self.shell.last = MockValues()
        self.validation_func = validate_contains_query

    def _mock_execute(self, cmd):
        self.stream.write(cmd)
        self.stream.write('\n')

    def test_null(self):
        # tests empty case
        args = []
        self.shell.last.result = {}
        flag = self.shell.handle_jmespath_query(args, False)
        self.assertTrue(flag)
        self.assertEqual('\n', self.stream.getvalue())

    def test_just_query(self):
        # tests flushing just the query
        args = ['?x']
        self.shell.last.result = {'x': 'result'}
        flag = self.shell.handle_jmespath_query(args, False)
        self.assertTrue(flag)
        self.assertEqual('"result"\n', self.stream.getvalue())

    def test_string_replacement(self):
        # tests that the query replaces the values in the command
        args = 'vm show -g "?group" -n "?name"'
        args = parse_quotes(args)
        args_no_quotes = []
        for arg in args:
            args_no_quotes.append(arg.strip("/'").strip('/"'))
        self.shell.last.result = {
            'group': 'mygroup',
            'name': 'myname'
        }
        flag = self.shell.handle_jmespath_query(args, False)
        self.assertTrue(flag)
        self.assertEqual(u"vm show -g mygroup -n myname\n", self.stream.getvalue())

    def test_list_replacement(self):
        # tests that the query replaces the values in the command
        args = 'vm show -g "?[].group" -n "?[].name"'
        args = parse_quotes(args)
        args_no_quotes = []
        for arg in args:
            args_no_quotes.append(arg.strip("/'").strip('/"'))
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
        flag = self.shell.handle_jmespath_query(args, False)
        self.assertTrue(flag)
        results = self.stream.getvalue().strip().split('\n')
        self.assertTrue(len(results) == 3)
        self.assertEqual(results[0], 'vm show -g mygroup -n myname')
        self.assertEqual(results[1], 'vm show -g mygroup2 -n myname2')
        self.assertEqual(results[2], 'vm show -g mygroup3 -n myname3')

    def test_quotes(self):
        # tests that it parses correctly with quotes in the command
        self.shell.last.result = {'x': 'result'}
        # pylint: disable=protected-access
        b_flag, c_flag, out, cmd = self.shell._special_cases(
            "this is 'url?what' negative", "this is 'url?what' negative", False)
        self.assertFalse(b_flag)
        self.assertFalse(c_flag)
        self.assertFalse(out)
        self.assertEqual(cmd, "this is 'url?what' negative")

    def test_errors(self):
        # tests invalid query
        args = 'vm show -g "?[].group" -n "?[].name"'
        args = parse_quotes(args)
        args_no_quotes = []
        for arg in args:
            args_no_quotes.append(arg.strip("/'").strip('/"'))
        self.shell.last.result = [
            {
                'group': 'mygroup',
                'name': 'myname'
            },
            {
                'group': 'mygroup3',
            }
        ]
        flag = self.shell.handle_jmespath_query(args, False)
        results = self.stream.getvalue().split('\n')
        self.assertTrue(flag)
        self.assertEqual(results[0], 'vm show -g mygroup -n myname')
        self.assertEqual(len(results), 2)

    def test_singleton(self):
        # tests a singleton example
        args = 'vm show -g "?group" -n "?name"'
        args = parse_quotes(args)
        args_no_quotes = []
        for arg in args:
            args_no_quotes.append(arg.strip("/'").strip('/"'))
        self.shell.last.result = {
            'group': 'mygroup',
            'name': 'myname'
        }

        flag = self.shell.handle_jmespath_query(args, False)
        self.assertTrue(flag)
        results = self.stream.getvalue().split('\n')
        self.assertEqual(results[0], u'vm show -g mygroup -n myname')

    def test_spaces(self):
        # tests quotes with spaces
        args = 'vm show -g "?[?group == \'mygroup\'].name"'
        args = parse_quotes(args)
        args_no_quotes = []
        for arg in args:
            args_no_quotes.append(arg.strip("/'").strip('/"'))
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

        self.shell.handle_jmespath_query(args_no_quotes, False)
        results = self.stream.getvalue().split('\n')
        self.assertEqual(results[0], u'vm show -g fred')

    def test_spaces_with_equal(self):
        # tests quotes with spaces
        args = 'vm show -g="?[?group == \'myg roup\'].name"'
        args = parse_quotes(args)
        args_no_quotes = []
        for arg in args:
            args_no_quotes.append(arg.strip("/'").strip('/"'))
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

        self.shell.handle_jmespath_query(args_no_quotes, False)
        results = self.stream.getvalue().split('\n')
        self.assertEqual(results[0], u'vm show -g=fred')

    def test_validation(self):
        # tests line validation that the command is an injection
        args = 'foo bar --foo=?bar'
        self.assertTrue(self.validation_func(args.split(), '?'))

        args = 'foo bar --is fun -g ?bar '
        self.assertTrue(self.validation_func(args.split(), '?'))

        args = 'foo bar --is fun -g bar '
        self.assertFalse(self.validation_func(args.split(), '?'))

        args = 'foo bar --isfun=bar '
        self.assertFalse(self.validation_func(args.split(), '?'))

        args = 'foo bar --is ?[?group == \'word\'].name '
        self.assertTrue(self.validation_func(parse_quotes(args), '?'))

        args = 'foo bar --query [?group == \'word\'].name '
        self.assertFalse(self.validation_func(parse_quotes(args), '?'))

        args = 'foo bar --query=[?group == \'w or =?d\'].name '
        self.assertFalse(self.validation_func(parse_quotes(args), '?'))


if __name__ == '__main__':
    unittest.main()
