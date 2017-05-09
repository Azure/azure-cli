# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import mock

from prompt_toolkit.interface import CommandLineInterface, Application
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.input import PipeInput
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import DEFAULT_BUFFER

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


PIPE = PipeInput()


def _mock_create_app():
    buffers = {
        DEFAULT_BUFFER: Buffer(is_multiline=True),
        'description': Buffer(is_multiline=True, read_only=True),
        'parameter': Buffer(is_multiline=True, read_only=True),
        'examples': Buffer(is_multiline=True, read_only=True),
        'bottom_toolbar': Buffer(is_multiline=True),
        'example_line': Buffer(is_multiline=True),
        'default_values': Buffer(),
        'symbols': Buffer()
    }
    return Application(
        mouse_support=False,
        buffers=buffers
    )


def _mock_create_interface(_):
    return CommandLineInterface(
        application=_mock_create_app(),
        eventloop=create_eventloop(),
        input=PIPE)


class ShellRun(ScenarioTest):

    @mock.patch('azclishell.app.Shell.create_interface', _mock_create_interface)
    def test_shell_run(self):
        """ tests whether the shell runs """
        PIPE.send('quit')
        self.cmd(str('interactive'))


# class DynamicShellCompletionsTest(ScenarioTest):

#     @mock.patch('azclishell.Shell.create_interface', _mock_create_interface)
#     @ResourceGroupPreparer()
#     def test_list_dynamic_completions(self, resource_group):
#         """ tests dynamic completions """
#         PIPE.send('vm show -g')
#         PIPE.
#         self.cmd('az interactive')
