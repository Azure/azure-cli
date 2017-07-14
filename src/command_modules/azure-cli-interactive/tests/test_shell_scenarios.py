# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import six
import sys
import unittest

from azclishell.app import Shell, space_examples

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, Completion

from azclishell.util import get_window_dim


def mock_dimensions():
    return 25, 25


def mock_pass(*args, **kwargs):
    pass


get_window_dim = mock_dimensions


class TestCompleter(Completer):
    def __init__(self, *args, **kwargs):
        super(TestCompleter, self).__init__(*args, **kwargs)
        self.completable = ['friendship', '--calls', 'ME']
        self.command_parameters = {'friendship': ['--calls']}
        self.command_description = {'friendship': 'the power within'}
        self.command_examples = {
            'friendship': [['used'], ['with care']],
            'guess': [['who', 'are'], ['you']]
        }
        self.param_description = {'friendship --calls': 'call the friends'}

    def has_description(self, command):
        return command in self.param_description

    def is_completable(self, command):
        return command in self.completable

    def get_completions(self, document, completion_event):  # pylint: disable=unused-argument
        for comp in self.completable:
            yield Completion(comp)


class ShellScenarioTest(unittest.TestCase):
    """ tests whether dump commands works """
    def __init__(self, *args, **kwargs):
        super(ShellScenarioTest, self).__init__(*args, **kwargs)

        self.out_stream = six.StringIO()
        self.shell = Shell(history=None, output_custom=self.out_stream)
        self.shell.completer = TestCompleter()

    def test_generate_help_text(self):
        """ tests building the help text """
        self.shell.completer = None
        description, example = self.shell.generate_help_text('')
        self.assertEqual(description, '')
        self.assertEqual(example, '')

        self.shell.completer = TestCompleter()
        description, example = self.shell.generate_help_text('friendship --calls')
        self.assertEqual(description, '--calls:\n' + 'call the friends')
        self.assertEqual(example, space_examples('use with care', 25, 1))

    def test_handle_examples(self):
        """ tests handling of example repl """
        temp_function = self.shell.example_repl
        self.shell.example_repl = mock_pass
        text = 'guess :: h'
        c_flag = False

        self.shell.handle_example(text, c_flag)
        self.assertEqual(self.out_stream.getvalue(), 'An Integer should follow the colon\n')
        self.out_stream.truncate(0)
        self.out_stream.seek(0)

        text = 'guess :: 2.8'
        c_flag = False
        self.shell.handle_example(text, c_flag)
        self.assertEqual(self.out_stream.getvalue(), 'An Integer should follow the colon\n')
        self.out_stream.truncate(0)
        self.out_stream.seek(0)

        text = 'guess :: -3'
        c_flag = False
        self.shell.handle_example(text, c_flag)
        self.assertEqual(self.out_stream.getvalue(), 'Invalid example number\n')
        self.out_stream.truncate(0)
        self.out_stream.seek(0)

        text = 'guess :: 3'
        c_flag = False
        self.shell.handle_example(text, c_flag)
        self.assertEqual(self.out_stream.getvalue(), 'Invalid example number\n')
        self.out_stream.truncate(0)
        self.out_stream.seek(0)

        text = 'guess :: 1'
        c_flag = False
        self.shell.handle_example(text, c_flag)

        self.shell.example_repl = temp_function


if __name__ == '__main__':
    unittest.main()
