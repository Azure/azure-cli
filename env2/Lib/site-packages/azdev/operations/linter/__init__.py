# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import sys
import time
import yaml

from knack.arguments import ignore_type, ArgumentsContext
from knack import events
from knack.help_files import helps
from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    heading, subheading, display, get_path_table, require_azure_cli, filter_by_git_diff)

from .linter import LinterManager, LinterScope, RuleError
from .util import filter_modules


logger = get_logger(__name__)


# pylint:disable=too-many-locals
def run_linter(modules=None, rule_types=None, rules=None, ci_exclusions=None,
               git_source=None, git_target=None, git_repo=None, include_whl_extensions=False):

    require_azure_cli()

    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import (  # pylint: disable=import-error
        get_all_help, create_invoker_and_load_cmds_and_args)

    heading('CLI Linter')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    # needed to remove helps from azdev
    azdev_helps = helps.copy()
    exclusions = {}
    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any((selected_modules[x] for x in selected_modules)):
        raise CLIError('No modules selected.')

    selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
        list(selected_modules['ext'].keys())
    selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
        list(selected_modules['ext'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    # collect all rule exclusions
    for path in selected_mod_paths:
        exclusion_path = os.path.join(path, 'linter_exclusions.yml')
        if os.path.isfile(exclusion_path):
            mod_exclusions = yaml.safe_load(open(exclusion_path))
            exclusions.update(mod_exclusions)

    start = time.time()
    display('Initializing linter with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)

    stop = time.time()
    logger.info('Commands and help loaded in %i sec', stop - start)
    command_loader = az_cli.invocation.commands_loader

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    # load yaml help
    help_file_entries = {}
    for entry_name, help_yaml in helps.items():
        # ignore help entries from azdev itself, unless it also coincides
        # with a CLI or extension command name.
        if entry_name in azdev_helps and entry_name not in command_loader.command_table:
            continue
        help_entry = yaml.safe_load(help_yaml)
        help_file_entries[entry_name] = help_entry

    # trim command table and help to just selected_modules
    command_loader, help_file_entries = filter_modules(
        command_loader, help_file_entries, modules=selected_mod_names, include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        raise CLIError('No commands selected to check.')

    # Instantiate and run Linter
    linter_manager = LinterManager(command_loader=command_loader,
                                   help_file_entries=help_file_entries,
                                   loaded_help=loaded_help,
                                   exclusions=exclusions,
                                   rule_inclusions=rules,
                                   use_ci_exclusions=ci_exclusions)

    subheading('Results')
    logger.info('Running linter: %i commands, %i help entries',
                len(command_loader.command_table), len(help_file_entries))
    exit_code = linter_manager.run(
        run_params=not rule_types or 'params' in rule_types,
        run_commands=not rule_types or 'commands' in rule_types,
        run_command_groups=not rule_types or 'command_groups'in rule_types,
        run_help_files_entries=not rule_types or 'help_entries' in rule_types)
    sys.exit(exit_code)
