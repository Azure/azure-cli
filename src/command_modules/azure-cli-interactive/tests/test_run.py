# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

from prompt_toolkit.interface import CommandLineInterface, Application
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.input import PipeInput

from azure.cli.testsdk import ScenarioTest
from azclishell import Shell

PIPE = PipeInput()

def _mock_create_app():
    return Application(
        mouse_support=False,
    )

def _mock_create_interface(_):
    return CommandLineInterface(
        application=_mock_create_app(),
        eventloop=create_eventloop(),
        input=PIPE)


class ShellRun(ScenarioTest):

    def test_shell_run(self):
        """ tests whether the shell runs """
        Shell.create_interface = _mock_create_interface
        PIPE.send('quit')
        self.cmd('az interactive')
