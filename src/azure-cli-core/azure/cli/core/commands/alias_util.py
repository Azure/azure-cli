# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def find_alias_and_transform_args(args, alias_table):
    args_transformed = args
    for section in alias_table.sections():
        if not alias_table.has_option(section, 'command'):
            continue
        transformed, new_args = _compare_and_transform(args, section, alias_table.get(section, 'command'))
        if transformed:
            args_transformed = find_alias_and_transform_args(new_args, alias_table)
            break
    return args_transformed


def _compare_and_transform(args, alias_section, command):
    def _parse_section(section):
        section_command = []
        section_argument = []
        command_flag = True
        for item in section.split():
            if not item:
                continue
            if not command_flag:
                section_argument.append(item)
            if item.startswith('-'):
                command_flag = False
                section_argument.append(item)
            else:
                section_command.append(item)
        return section_command, section_argument

    if not alias_section or command is None:
        return False, args
    alias_command, alias_argument = _parse_section(alias_section)
    arg_index = 1
    new_args = ['az']
    for command_item in alias_command:
        if not command_item:
            continue
        if command_item != args[arg_index]:
            return False, args
        arg_index += 1
    new_args.extend(command.split())
    new_args.extend(args[arg_index:])
    return True, new_args
