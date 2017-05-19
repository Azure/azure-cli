# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os

from prompt_toolkit.history import FileHistory

from azclishell import __version__
import azclishell._dump_help
import azclishell.configuration
from azclishell.gather_commands import GatherCommands
from azclishell.app import Shell
from azclishell.az_completer import AzCompleter
from azclishell.az_lexer import AzLexer
from azclishell.color_styles import style_factory
from azclishell.frequency_heuristic import frequent_user

from azure.cli.core.application import APPLICATION
from azure.cli.core._session import ACCOUNT, CONFIG, SESSION
from azure.cli.core._environment import get_config_dir as cli_config_dir
from azure.cli.core.commands.client_factory import ENV_ADDITIONAL_USER_AGENT

AZCOMPLETER = AzCompleter(GatherCommands())
SHELL_CONFIGURATION = azclishell.configuration.CONFIGURATION


def main(style=None):
    os.environ[ENV_ADDITIONAL_USER_AGENT] = 'AZURECLISHELL/' + __version__

    azure_folder = cli_config_dir()
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)

    ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
    CONFIG.load(os.path.join(azure_folder, 'az.json'))
    SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

    config = SHELL_CONFIGURATION
    shell_config_dir = azclishell.configuration.get_config_dir

    if style:
        given_style = style
        config.set_style(given_style)
    else:
        given_style = config.get_style()

    style_obj = style_factory(given_style)

    if config.BOOLEAN_STATES[config.config.get('DEFAULT', 'firsttime')]:
        print("When in doubt, ask for 'help'")
        config.firsttime()

    ask_feedback = False
    if not config.has_feedback() and frequent_user:
        print("\n\nAny comments or concerns? You can use the \'feedback\' command!" +
              " We would greatly appreciate it.\n")
        ask_feedback = True

    shell_app = Shell(
        completer=AZCOMPLETER,
        lexer=AzLexer,
        history=FileHistory(
            os.path.join(shell_config_dir(), config.get_history())),
        app=APPLICATION,
        styles=style_obj,
        user_feedback=ask_feedback
    )
    shell_app.run()
