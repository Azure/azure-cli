# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import yaml
from knack.help_files import helps
from azure.cli.testsdk import TestCli
from azure.cli.core.commands.arm import add_id_parameters
from azure.cli.command_modules.interactive.azclishell._dump_commands import AzInteractiveCommandsLoader
from azure.cli.command_modules.interactive.azclishell.command_tree import AzInteractiveCommandsLoader
from .cli_command_linter import Linter

import automation.utilities.path as automation_path


def define_arguments(parser):
    parser.add_argument('--ci', action='store_true', help='Run in CI mode')
    parser.add_argument('--module', dest='modules', action='append',
                        help='The modules on which the style check should run. Accept short names, '
                             'except azure-cli, azure-cli-core and azure-cli-nspkg')


def main(args):
    # setup CLI to enable command loader
    az_cli = TestCli()
    az_cli.invocation = az_cli.invocation_cls(cli_ctx=az_cli,
                                              parser_cls=az_cli.parser_cls,
                                              commands_loader_cls=az_cli.commands_loader_cls,
                                              help_cls=az_cli.help_cls)
    # Use interactive loader to load commands and arguments
    interactive_loader = AzInteractiveCommandsLoader(cli_ctx=az_cli)
    interactive_loader.load_command_table(None)
    interactive_loader.load_arguments(None)
    add_id_parameters(None, cmd_tbl=interactive_loader.command_table)

    # load descriptions from docstrings/param
    for _, command in interactive_loader.command_table.items():
        command.description = command.description()

    # load yaml help
    all_help = {}
    for command_name, help_yaml in helps.items():
        help_entry = yaml.load(help_yaml)
        all_help[command_name] = help_entry
        short_summary = help_entry.get('short-summary') or ''
        long_summary = help_entry.get('long-summary') or ''
        # param_info = help_entry.get('parameters') or []

        # load command/command-group help
        if command_name in interactive_loader.command_table:
            interactive_loader.command_table.get(command_name).description += short_summary + long_summary




    # Instantiate and run Linter
    Linter(command_table=interactive_loader.command_table, all_yaml_help=all_help).run()


def init_args(root):
    parser = root.add_parser('command-lint', help="Verify the contents of the command table and help.")
    define_arguments(parser)
    parser.set_defaults(func=main)
