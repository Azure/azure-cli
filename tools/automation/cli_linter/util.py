# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import re
import os
import inspect


_LOADER_CLS_RE = re.compile('.*azure/cli/command_modules/(?P<module>[^/]*)/__init__.*')


def exclude_commands(command_table, help_file_entries, module_exclusions=None, extensions=None):
    return _filter_mods(command_table, help_file_entries, modules=module_exclusions, extensions=extensions,
                        exclude=True)


def include_commands(command_table, help_file_entries, module_inclusions=None, extensions=None):
    return _filter_mods(command_table, help_file_entries, modules=module_inclusions, extensions=extensions)


def _filter_mods(command_table, help_file_entries, modules=None, extensions=None, exclude=False):
    from ..utilities.path import get_command_modules_paths
    modules = modules or []
    extensions = extensions or []

    command_modules_paths = get_command_modules_paths()
    filtered_module_names = {mod for mod, path in command_modules_paths if mod in modules}

    command_table = command_table.copy()
    help_file_entries = help_file_entries.copy()

    for command_name in list(command_table.keys()):
        try:
            source_name, is_extension = _get_command_source(command_name, command_table)
        except LinterError as ex:
            print(ex)
            # command is unrecognized
            source_name, is_extension = None, False

        is_specified = source_name in extensions if is_extension else source_name in filtered_module_names
        if is_specified == exclude:
            # brute force method of ignoring commands from a module or extension
            del command_table[command_name]
            help_file_entries.pop(command_name, None)
            for group_name in get_command_groups(command_name):
                help_file_entries.pop(group_name, None)

    return command_table, help_file_entries


def share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)


def get_command_groups(command_name):
    command_args = []
    for arg in command_name.split()[:-1]:
        command_args.append(arg)
        if command_args:
            yield ' '.join(command_args)


def _get_command_source(command_name, command_table):
    from azure.cli.core.commands import ExtensionCommandSource
    command = command_table.get(command_name)
    # see if command is from an extension
    if isinstance(command.command_source, ExtensionCommandSource):
        return command.command_source.extension_name, True
    if command.command_source is None:
        raise LinterError('Command: `%s`, has no command source.' % command_name)
    # command is from module
    return command.command_source, False


class LinterError(Exception):
    """
    Exception thrown by linter for non rule violation reasons
    """
    pass
