# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import re
import os
import inspect


_LOADER_CLS_RE = re.compile('.*azure/cli/command_modules/(?P<module>[^/]*)/__init__.*')


def exclude_mods(command_table, help_file_entries, module_exclusions):
    return _filter_mods(command_table, help_file_entries, module_exclusions, True)


def include_mods(command_table, help_file_entries, module_inclusions):
    return _filter_mods(command_table, help_file_entries, module_inclusions, False)


def _filter_mods(command_table, help_file_entries, modules, exclude):
    from ..utilities.path import get_command_modules_paths

    command_modules_paths = get_command_modules_paths()
    filtered_module_names = {mod for mod, path in command_modules_paths if mod in modules}

    command_table = command_table.copy()
    help_file_entries = help_file_entries.copy()

    for command_name in list(command_table.keys()):
        try:
            mod_name = _get_command_module(command_name, command_table)
        except LinterError as ex:
            print(ex)
            continue
        if (mod_name in filtered_module_names) == exclude:
            # brute force method of clearing traces of a module
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


def _get_command_module(command_name, command_table):
    # hacky way to get a command's module
    command = command_table.get(command_name)
    loader_cls = command.loader.__class__
    loader_file_path = inspect.getfile(loader_cls)
    # normalize os path to '/' for regex
    loader_file_path = '/'.join(loader_file_path.split(os.path.sep))
    match = _LOADER_CLS_RE.match(loader_file_path)
    # loader class path is consistent due to convention, throw error if no match
    # this will likely throw error for extensions
    if not match:
        raise LinterError('`{}`\'s loader class path does not match regex pattern: {}' \
            .format(command_name, _LOADER_CLS_RE.pattern))
    return match.groupdict().get('module')


class LinterError(Exception):
    """
    Exception thrown by linter for non rule violation reasons
    """
    pass
