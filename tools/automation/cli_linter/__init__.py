# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import sys
import yaml
from knack.help_files import helps
from .linter import Linter


def define_arguments(parser):
    parser.add_argument('--ci', action='store_true', help='Run in CI mode')
    parser.add_argument('--params', dest='rule_types_to_run', action='append_const', const='params',
                        help='Run linter on parameters.')
    parser.add_argument('--commands', dest='rule_types_to_run', action='append_const', const='commands',
                        help='Run linter on commands.')
    parser.add_argument('--command-groups', dest='rule_types_to_run', action='append_const', const='command_groups',
                        help='Run linter on command groups.')
    parser.add_argument('--help-file-entries', dest='rule_types_to_run', action='append_const', const='help_entries',
                        help='Run linter on help-file-entries.')


def main(args):
    from azure.cli.testsdk import TestCli
    from azure.cli.core.util import get_all_help, create_invoker_and_load_cmds_and_args
    from azure.cli.core.commands.arm import add_id_parameters

    print('Initializing linter with command table and help files...')
    # setup CLI to enable command loader
    az_cli = TestCli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)
    command_table = az_cli.invocation.commands_loader.command_table
    add_id_parameters(None, cmd_tbl=command_table)

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    # load yaml help
    help_file_entries = {}
    for entry_name, help_yaml in helps.items():
        help_entry = yaml.load(help_yaml)
        help_file_entries[entry_name] = help_entry

    if not args.rule_types_to_run:
        args.rule_types_to_run = ['params', 'commands', 'command_groups', 'help_entries']

    # Instantiate and run Linter
    linter = Linter(command_table=command_table,
                    help_file_entries=help_file_entries,
                    loaded_help=loaded_help)
    exit_code = linter.run(run_params='params' in args.rule_types_to_run,
                           run_commands='commands' in args.rule_types_to_run,
                           run_command_groups='command_groups' in args.rule_types_to_run,
                           run_help_files_entries='help_entries' in args.rule_types_to_run)

    sys.exit(exit_code)


def init_args(root):
    parser = root.add_parser('cli-lint', help="Verify the contents of the command table and help.")
    define_arguments(parser)
    parser.set_defaults(func=main)
