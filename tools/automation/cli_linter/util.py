# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import inspect


def _exclude_mods(command_table, help_file_entries, module_exclusions):
    return _filter_mods(command_table, help_file_entries, module_exclusions, True)


def _include_mods(command_table, help_file_entries, module_inclusions):
    return _filter_mods(command_table, help_file_entries, module_inclusions, False)


def _filter_mods(command_table, help_file_entries, modules, exclude):
    from ..utilities.path import get_command_modules_paths

    command_modules_paths = get_command_modules_paths()
    filtered_module_paths = tuple(path for mod, path in command_modules_paths if mod in modules)

    command_table = command_table.copy()
    help_file_entries = help_file_entries.copy()

    for command_name, command in list(command_table.items()):
        # brute force way to remove all traces from excluded modules
        loader_cls = command.loader.__class__
        loader_file_path = inspect.getfile(loader_cls)
        if loader_file_path.startswith(filtered_module_paths) == exclude:
            del command_table[command_name]
            help_file_entries.pop(command_name, None)
            for group_name in _get_command_groups(command_name):
                help_file_entries.pop(group_name, None)

    return command_table, help_file_entries


def _share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)


def _get_command_groups(command_name):
    command_args = []
    for arg in command_name.split()[:-1]:
        command_args.append(arg)
        if command_args:
            yield ' '.join(command_args)


def _get_command_module(command_name, command_table):
    from ..utilities.path import get_command_modules_paths

    command_modules_paths = get_command_modules_paths()

    command = command_table.get(command_name)
    loader_cls = command.loader.__class__
    loader_file_path = inspect.getfile(loader_cls)
    return [mod for mod, path in command_modules_paths if loader_file_path.startswith(path)]
