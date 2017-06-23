# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import six
import unittest

from azclishell.app import Shell

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER


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
