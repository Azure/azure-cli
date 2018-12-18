# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import re
import os
import copy
import inspect

option_pattern = r"(\-\-\S+|\-s)"
OPTION_RE = re.compile(option_pattern)



_LOADER_CLS_RE = re.compile('.*azure/cli/command_modules/(?P<module>[^/]*)/__init__.*')


def exclude_commands(command_loader, help_file_entries, module_exclusions=None, extensions=None):
    return _filter_mods(command_loader, help_file_entries, modules=module_exclusions, extensions=extensions,
                        exclude=True)


def include_commands(command_loader, help_file_entries, module_inclusions=None, extensions=None):
    return _filter_mods(command_loader, help_file_entries, modules=module_inclusions, extensions=extensions)


def _filter_mods(command_loader, help_file_entries, modules=None, extensions=None, exclude=False):
    from ..utilities.path import get_command_modules_paths
    modules = modules or []
    extensions = extensions or []

    command_modules_paths = get_command_modules_paths()
    filtered_module_names = {mod for mod, path in command_modules_paths if mod in modules}

    # command tables and help entries must be copied to allow for seperate linter scope
    command_table = command_loader.command_table.copy()
    command_group_table = command_loader.command_group_table.copy()
    command_loader = copy.copy(command_loader)
    command_loader.command_table = command_table
    command_loader.command_group_table = command_group_table
    help_file_entries = help_file_entries.copy()

    for command_name in list(command_loader.command_table.keys()):
        try:
            source_name, is_extension = _get_command_source(command_name, command_loader.command_table)
        except LinterError as ex:
            print(ex)
            # command is unrecognized
            source_name, is_extension = None, False

        is_specified = source_name in extensions if is_extension else source_name in filtered_module_names
        if is_specified == exclude:
            # brute force method of ignoring commands from a module or extension
            command_loader.command_table.pop(command_name, None)
            help_file_entries.pop(command_name, None)

    # Remove unneeded command groups
    retained_command_groups = set([' '.join(x.split(' ')[:-1]) for x in command_loader.command_table])
    excluded_command_groups = set(command_loader.command_group_table.keys()) - retained_command_groups
    for group_name in excluded_command_groups:
        command_loader.command_group_table.pop(group_name, None)
        help_file_entries.pop(group_name, None)

    return command_loader, help_file_entries


def share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)


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

# return list of (cmd, params) tuples from example text. e.g. (az foo bar, [--opt, -n, -g, --help])
def get_cmd_param_list_from_example(example_text):

    def process_short_option(option): # handle options like -otable
        if len(option) > 2 and option[0] == "-" and option[0] != option[1]:
            return option[0:2]
        else:
            return option

    CMD_PREFIX = "az "
    commands = []  # some examples have multistep commands. This is a simple way to extract them
    while(CMD_PREFIX in example_text):
        # find next az command start and end
        start = example_text.find(CMD_PREFIX)
        end = example_text.find(CMD_PREFIX, start + 1)
        end = end if end > -1 else len(example_text)
        # extract command
        cmd_text = example_text[start:end]
        # update example text
        example_text = example_text[end:]
        # remove piping from cmd_text
        end = cmd_text.find("|")
        end = end if end > -1 else len(cmd_text)
        cmd_text = cmd_text[:end]
        # add to commands list
        commands.append(cmd_text)


    cmd_param_list = []
    for command in commands:
        idx = command.find(" -")  # Todo: positionals?
        command_body = command[:idx].strip()
        parameters = [maybe_opt for maybe_opt in command[idx:].split() if maybe_opt.startswith("-")]
        parameters = list(map(process_short_option, parameters)) # process short options like -otable
        cmd_param_list.append((command_body, parameters))

    return cmd_param_list
