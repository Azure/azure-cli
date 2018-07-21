# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import mock

from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.interactive.azclishell.configuration import Configuration
from azure.cli.command_modules.interactive.azclishell.app import AzInteractiveShell

from prompt_toolkit.document import Document


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class CompletionTest(unittest.TestCase):
    def __init__(self, methodName):
        super(CompletionTest, self).__init__(methodName)
        with mock.patch.object(Configuration, 'get_help_files', lambda _: 'help_dump_test.json'):
            with mock.patch.object(Configuration, 'get_config_dir', lambda _: TEST_DIR):
                shell_ctx = AzInteractiveShell(DummyCli(), None)
                self.completer = shell_ctx.completer
                self.shell_ctx = shell_ctx

    # tests the completion generator
    def verify_completions(self, generated_completions, expected_completions, start_position,
                           all_completions_expected=True, unexpected_completions=None):
        for completion in generated_completions:
            if all_completions_expected:
                self.assertIn(completion.text, expected_completions)
                expected_completions.remove(completion.text)
            else:
                expected_completions.discard(completion.text)
            if unexpected_completions:
                self.assertNotIn(completion.text, unexpected_completions)

            self.assertEqual(completion.start_position, start_position)
        self.assertFalse(expected_completions)

    def test_command_completion(self):
        # initial completions
        doc = Document(u' ')
        gen = self.completer.get_completions(doc, None)
        completions = set(['exit', 'quit', 'storage', 'vm', 'vmss'])
        self.verify_completions(gen, completions, 0)

        # start command
        doc = Document(u's')
        gen = self.completer.get_completions(doc, None)
        completions = set(['storage'])
        self.verify_completions(gen, completions, -1)

        # test spaces
        doc = Document(u'  storage    a')
        gen = self.completer.get_completions(doc, None)
        completions = set(['account'])
        self.verify_completions(gen, completions, -1)

        # completer traverses command-tree
        doc = Document(u'storage account ')
        gen = self.completer.get_completions(doc, None)
        completions = set(['create', 'check-name'])
        self.verify_completions(gen, completions, 0)

        # test completed command still shows completion
        doc = Document(u'vm')
        gen = self.completer.get_completions(doc, None)
        completions = set(['vm', 'vmss'])
        self.verify_completions(gen, completions, -2)

        # test unrecognized command does not complete
        doc = Document(u'vm group ')
        gen = self.completer.get_completions(doc, None)
        completions = set()
        self.verify_completions(gen, completions, 0)

    def test_param_completion(self):
        # 'az -h'
        doc = Document(u'-')
        gen = self.completer.get_completions(doc, None)
        completions = set(['-h'])
        self.verify_completions(gen, completions, -1)

        # 'az --help'
        doc = Document(u'--')
        gen = self.completer.get_completions(doc, None)
        completions = set(['--help'])
        self.verify_completions(gen, completions, -2)

        # 'az storage account -h'
        doc = Document(u'storage account -')
        gen = self.completer.get_completions(doc, None)
        completions = set(['-h'])
        self.verify_completions(gen, completions, -1)

        # test just completed command, first param completions
        doc = Document(u'storage account create ')
        gen = self.completer.get_completions(doc, None)
        expected = set(['--name', '--resource-group', '--access-tier', '--sku', '--tags'])
        not_expected = set(['-n', '-h', '-g'])
        self.verify_completions(gen, expected, 0, all_completions_expected=False, unexpected_completions=not_expected)

        # test single dash aliased params
        doc = Document(u'storage account create -')
        gen = self.completer.get_completions(doc, None)
        completions = set(['-h', '-o', '-g', '-l', '-n'])
        self.verify_completions(gen, completions, -1)

        # test params that are substrings of one another
        doc = Document(u'vmss create --subnet')
        gen = self.completer.get_completions(doc, None)
        completions = set(['--subnet', '--subnet-address-prefix'])
        self.verify_completions(gen, completions, -8)

        # test params with no help
        doc = Document(u'vmss create --upgrade-policy-mo')
        gen = self.completer.get_completions(doc, None)
        completions = set(['--upgrade-policy-mode'])
        self.verify_completions(gen, completions, -19)

        # test duplicated parameters
        expected = set()
        doc = Document(u'vmss create --name Bob --n')
        gen = self.completer.get_completions(doc, None)
        not_expected = set(['--name'])
        self.verify_completions(gen, expected, -3, all_completions_expected=False, unexpected_completions=not_expected)

        # test duplicated parameter alias
        doc = Document(u'vmss create --name Bob -')
        gen = self.completer.get_completions(doc, None)
        not_expected = set(['-n'])
        self.verify_completions(gen, expected, -1, all_completions_expected=False, unexpected_completions=not_expected)

        # test displayed help
        doc = Document(u'vm create -g')
        gen = self.completer.get_completions(doc, None)
        completion = next(gen)
        self.assertEqual(completion.text, '-g')
        self.assertIn('Name of resource group', completion._display_meta)


if __name__ == '__main__':
    unittest.main()
