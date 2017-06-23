# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import six
import unittest

from azclishell.app import Shell, space_examples

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, Completion

from azclishell.util import get_window_dim


def mock_dimensions():
    return 25, 25


get_window_dim = mock_dimensions


class TestCompleter(Completer):
    def __init__(self, *args, **kwargs):
        super(TestCompleter, self).__init__(*args, **kwargs)
        self.completable = ['friendship', '--calls', 'ME']
        self.command_parameters = {'friendship': ['--calls']}
        self.command_description = {'friendship': 'the power within'}
        self.command_examples = {'friendship': 'use with care'}
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

        self.in_stream = six.StringIO()
        self.out_stream = six.StringIO()
        self.shell = Shell(history=None, input_custom=self.in_stream, output_custom=self.out_stream)

    def test_generate_help_text(self):
        """ tests building the help text """
        description, example = self.shell.generate_help_text('')
        self.assertEqual(description, '')
        self.assertEqual(example, '')

        self.shell.completer = TestCompleter()
        description, example = self.shell.generate_help_text('friendship --calls')
        self.assertEqual(description, '--calls:\n' + 'call the friends')
        self.assertEqual(example, space_examples('use with care', 25, 1))

    def test_on_input_timeout(self):
        """ tests everything """
        self.shell.cli.current_buffer.document = Document(u'az to be or not')
        self.shell.on_input_timeout(self.shell._cli)  # pylint: disable=protected-access
        cli = self.shell._cli  # pylint: disable=protected-access
        self.assertEqual(cli.current_buffer.document.text, u'az to be or not')
        self.assertEqual(cli.buffers['description'].document.text, '')
        self.assertEqual(cli.buffers['parameter'].document.text, '')
        self.assertEqual(cli.buffers['examples'].document.text, '')


if __name__ == '__main__':
    unittest.main()
