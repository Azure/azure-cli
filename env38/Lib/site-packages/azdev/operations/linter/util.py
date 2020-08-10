# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import copy
import re

from knack.log import get_logger

from azdev.utilities import get_name_index


logger = get_logger(__name__)


_LOADER_CLS_RE = re.compile('.*azure/cli/command_modules/(?P<module>[^/]*)/__init__.*')


def filter_modules(command_loader, help_file_entries, modules=None, include_whl_extensions=False):
    """ Modify the command table and help entries to only include certain modules/extensions.

    : param command_loader: The CLICommandsLoader containing the command table to filter.
    : help_file_entries: The dict of HelpFile entries to filter.
    : modules: [str] list of module or extension names to retain.
    """
    return _filter_mods(command_loader, help_file_entries, modules=modules,
                        include_whl_extensions=include_whl_extensions)


def exclude_commands(command_loader, help_file_entries, module_exclusions, include_whl_extensions=False):
    """ Modify the command table and help entries to exclude certain modules/extensions.

    : param command_loader: The CLICommandsLoader containing the command table to filter.
    : help_file_entries: The dict of HelpFile entries to filter.
    : modules: [str] list of module or extension names to remove.
    """
    return _filter_mods(command_loader, help_file_entries, modules=module_exclusions, exclude=True,
                        include_whl_extensions=include_whl_extensions)


def _filter_mods(command_loader, help_file_entries, modules=None, exclude=False, include_whl_extensions=False):
    modules = modules or []

    # command tables and help entries must be copied to allow for seperate linter scope
    command_table = command_loader.command_table.copy()
    command_group_table = command_loader.command_group_table.copy()
    command_loader = copy.copy(command_loader)
    command_loader.command_table = command_table
    command_loader.command_group_table = command_group_table
    help_file_entries = help_file_entries.copy()
    name_index = get_name_index(include_whl_extensions=include_whl_extensions)

    for command_name in list(command_loader.command_table.keys()):
        try:
            source_name, _ = _get_command_source(command_name, command_loader.command_table)
        except LinterError as ex:
            # command is unrecognized
            logger.warning(ex)
            source_name = None

        try:
            long_name = name_index[source_name]
            is_specified = source_name in modules or long_name in modules
        except KeyError:
            is_specified = False
        if is_specified == exclude:
            # brute force method of ignoring commands from a module or extension
            command_loader.command_table.pop(command_name, None)
            help_file_entries.pop(command_name, None)

    # Remove unneeded command groups
    retained_command_groups = {' '.join(x.split(' ')[:-1]) for x in command_loader.command_table}
    excluded_command_groups = set(command_loader.command_group_table.keys()) - retained_command_groups

    for group_name in excluded_command_groups:
        command_loader.command_group_table.pop(group_name, None)
        help_file_entries.pop(group_name, None)

    return command_loader, help_file_entries


def share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)


def _get_command_source(command_name, command_table):
    from azure.cli.core.commands import ExtensionCommandSource  # pylint: disable=import-error
    command = command_table.get(command_name)
    # see if command is from an extension
    if isinstance(command.command_source, ExtensionCommandSource):
        return command.command_source.extension_name, True
    if command.command_source is None:
        raise LinterError('Command: `%s`, has no command source.' % command_name)
    # command is from module
    return command.command_source, False


# pylint: disable=line-too-long
def merge_exclusion(left_exclusion, right_exclusion):
    for command_name, value in right_exclusion.items():
        for rule_name in value.get('rule_exclusions', []):
            left_exclusion.setdefault(command_name, {}).setdefault('rule_exclusions', []).append(rule_name)
        for param_name in value.get('parameters', {}):
            for rule_name in value.get('parameters', {}).get(param_name, {}).get('rule_exclusions', []):
                left_exclusion.setdefault(command_name, {}).setdefault('parameters', {}).setdefault(param_name, {}).setdefault('rule_exclusions', []).append(rule_name)


class LinterError(Exception):
    """
    Exception thrown by linter for non rule violation reasons
    """
    pass  # pylint: disable=unnecessary-pass
