# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import six

import azclishell.command_tree as tree
from azclishell.az_completer import AzCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion


def _build_completer(commands, global_params):
    from azure.cli.testsdk import TestCli
    from azclishell.app import AzInteractiveShell
    shell_ctx = AzInteractiveShell(TestCli(), None)
    return AzCompleter(shell_ctx, commands, global_params)


class _Commands():
    """ mock model for testing completer """
    def __init__(self, descrip=None, completable=None, command_param=None,
                 completable_param=None, command_tree=None, param_descript=None,
                 command_example=None, same_param_doubles=None):
        self.descrip = descrip
        self.completable = completable
        com_par = {}
        for com in self.descrip.keys():
            com_par[com] = ''
        self.command_param = command_param or com_par
        self.completable_param = completable_param

        self.command_tree = command_tree
        self.param_descript = param_descript
        self.command_example = command_example
        self.same_param_doubles = same_param_doubles


class CompletionTest(unittest.TestCase):
    """ tests the completion generator """
    def init1(self):
        """ a variation of initializing """
        com_tree1 = tree.generate_tree("command can")
        com_tree2 = tree.generate_tree("create")
        com_tree3 = tree.CommandHead()
        com_tree3.add_child(com_tree2)
        com_tree3.add_child(com_tree1)
        command_description = {
            "create": '',
            "command can": ''
        }
        commands = _Commands(
            command_tree=com_tree3,
            descrip=command_description
        )
        self.completer = _build_completer(commands, global_params=False)

    def init2(self):
        """ a variation of initializing """
        com_tree1 = tree.generate_tree("command can")
        com_tree2 = tree.generate_tree("create")
        com_tree3 = tree.CommandHead()
        com_tree3.add_child(com_tree2)
        com_tree3.add_child(com_tree1)
        command_param = {
            "create": ["-funtime"],
        }
        completable_param = [
            "-helloworld",
            "-funtime"
        ]
        param_descript = {
            "create -funtime": "There is no work life balance, it's just your life"
        }
        command_description = {
            "create": '',
            "command can": ''
        }
        commands = _Commands(
            command_tree=com_tree3,
            command_param=command_param,
            completable_param=completable_param,
            param_descript=param_descript,
            descrip=command_description
        )
        self.completer = _build_completer(commands, global_params=False)

    def init3(self):
        """ a variation of initializing """
        com_tree1 = tree.generate_tree("command can")
        com_tree2 = tree.generate_tree("create")
        com_tree3 = tree.CommandHead()
        com_tree3.add_child(com_tree2)
        com_tree3.add_child(com_tree1)
        command_param = {
            "create": ["--funtimes", "-f", '--fun', "--helloworld"],
        }
        completable_param = [
            "--helloworld",
            "--funtimes",
            "-f",
            '--fun'
        ]
        param_descript = {
            "create -f": "There is no work life balance, it's just your life",
            "create --funtimes": "There is no work life balance, it's just your life",
            "create --fun": "There is no work life balance, it's just your life"
        }
        same_param_doubles = {
            "create": [set(["-f", "--funtimes", '--fun']), set(['--unhap', '-u'])]
        }
        command_description = {
            "create": '',
            "command can": ''
        }
        commands = _Commands(
            command_tree=com_tree3,
            command_param=command_param,
            completable_param=completable_param,
            param_descript=param_descript,
            same_param_doubles=same_param_doubles,
            descrip=command_description
        )
        self.completer = _build_completer(commands, global_params=False)

    def init4(self):
        """ a variation of initializing """
        com_tree1 = tree.generate_tree("createmore can")
        com_tree2 = tree.generate_tree("create")
        com_tree3 = tree.CommandHead()
        com_tree3.add_child(com_tree2)
        com_tree3.add_child(com_tree1)
        command_param = {
            "create": ["--funtimes", "-f", "--helloworld"],
        }
        completable_param = [
            "--helloworld",
            "--funtimes",
            "-f"
        ]
        param_descript = {
            "create -f": "There is no work life balance, it's just your life",
            "create --funtimes": "There is no work life balance, it's just your life"
        }
        same_param_doubles = {
            "create": [set(["-f", "--funtimes", '--fun'])]
        }
        command_description = {
            "create": '',
            "createmore can": ''
        }
        commands = _Commands(
            command_tree=com_tree3,
            command_param=command_param,
            completable_param=completable_param,
            param_descript=param_descript,
            same_param_doubles=same_param_doubles,
            descrip=command_description
        )
        self.completer = _build_completer(commands, global_params=False)

    def test_command_completion(self):
        # tests general command completion
        self.init1()

        doc = Document(u'')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion("command"))
        self.assertEqual(six.next(gen), Completion("create"))

        doc = Document(u'c')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion("command", -1))
        self.assertEqual(six.next(gen), Completion("create", -1))

        doc = Document(u'cr')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion("create", -2))

        doc = Document(u'command ')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion("can"))

        doc = Document(u'create ')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

    def test_param_completion(self):
        # tests param completion
        self.init2()
        doc = Document(u'create -')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion(
            "-funtime", -1, display_meta="There is no work life balance, it's just your life"))

        doc = Document(u'command can -')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

    def test_param_double(self):
        # tests not generating doubles for parameters
        self.init3()
        doc = Document(u'create -f --')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion(
            "--helloworld", -2))

        doc = Document(u'create -f -')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

        doc = Document(u'create --fun -')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

        doc = Document(u'create --funtimes -')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

    def test_second_completion(self):
        self.init3()
        doc = Document(u'crea ')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

        doc = Document(u'create --fun ')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

        doc = Document(u'command d ')
        gen = self.completer.get_completions(doc, None)
        with self.assertRaises(StopIteration):
            six.next(gen)

        doc = Document(u'create --funtimes "life" --hello')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion(
            "--helloworld", -7))

    def test_substring_completion(self):
        self.init4()
        doc = Document(u'create')
        gen = self.completer.get_completions(doc, None)
        self.assertEqual(six.next(gen), Completion(
            "createmore", -6))


if __name__ == '__main__':
    unittest.main()
