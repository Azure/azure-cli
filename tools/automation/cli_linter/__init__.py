# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import sys
import os
import yaml
from knack.help_files import helps
from .linter import LinterManager


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
    parser.add_argument('--modules', dest='modules', nargs='+', help='The modules on which the linter should run.')
    parser.add_argument('--extensions', dest='extensions', nargs='+', help='The extensions on which the linter should run.')
    parser.add_argument('--rules', dest='rules', nargs='+', help='The rules which the linter should run.')


def main(args):
    from azure.cli.core import get_default_cli
    from azure.cli.core.file_util import get_all_help, create_invoker_and_load_cmds_and_args

    print('Initializing linter with command table and help files...')
    # setup CLI to enable command loader
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)
    command_loader = az_cli.invocation.commands_loader

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    # load yaml help
    help_file_entries = {}
    for entry_name, help_yaml in helps.items():
        help_entry = yaml.safe_load(help_yaml)
        help_file_entries[entry_name] = help_entry

    if not args.rule_types_to_run:
        args.rule_types_to_run = ['params', 'commands', 'command_groups', 'help_entries']

    # find rule exclusions and pass to linter manager
    from ..utilities.path import get_command_modules_paths, get_extensions_paths
    exclusions = {}
    command_modules_paths = get_command_modules_paths()
    extension_paths = get_extensions_paths()
    for gen in (command_modules_paths, extension_paths):
        for _, path in gen:
            exclusion_path = os.path.join(path, 'linter_exclusions.yml')
            if os.path.isfile(exclusion_path):
                mod_exclusions = yaml.safe_load(open(exclusion_path))
                exclusions.update(mod_exclusions)

    # only run linter on modules and extensions specified
    if args.modules or args.extensions:
        from .util import include_commands
        command_loader, help_file_entries = include_commands(
            command_loader, help_file_entries, module_inclusions=args.modules, extensions=args.extensions)

    # Instantiate and run Linter
    linter_manager = LinterManager(command_loader=command_loader,
                                   help_file_entries=help_file_entries,
                                   loaded_help=loaded_help,
                                   exclusions=exclusions,
                                   rule_inclusions=args.rules)
    exit_code = linter_manager.run(run_params='params' in args.rule_types_to_run,
                                   run_commands='commands' in args.rule_types_to_run,
                                   run_command_groups='command_groups' in args.rule_types_to_run,
                                   run_help_files_entries='help_entries' in args.rule_types_to_run,
                                   ci=args.ci)

    sys.exit(exit_code)


def init_args(root):
    parser = root.add_parser('cli-lint', help="Verify the contents of the command table and help.")
    define_arguments(parser)
    parser.set_defaults(func=main)
