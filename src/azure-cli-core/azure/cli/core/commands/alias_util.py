# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def find_alias_and_transform_args(args, alias_config):
    args_transformed = args
    for key in alias_config.keys():
        if not alias_config[key]:
            continue
        transformed, new_args = _compare_and_transform(args, key, alias_config[key])
        if transformed:
            args_transformed = find_alias_and_transform_args(new_args, alias_config)
            break
    return args_transformed


def _compare_and_transform(args, section_key, alias_section):
    args_index = 0
    import shlex
    for cmd in shlex.split(section_key):
        if cmd != args[args_index]:
            return False, args
        args_index += 1

    derived_command = []
    if alias_section.get('command'):
        derived_command = _transform_command(args, args_index, alias_section['command'])
    if args_index >= len(args) or (not args[args_index].startswith('-')):
        if derived_command:
            return True, derived_command
        else:
            return False, args
    derived_command_with_arguments = []
    for key in alias_section.keys():
        if not _is_section(alias_section[key]):
            continue
        command_with_arguments = _compare_arguments_and_transform(args, args_index, key, alias_section[key])
        if command_with_arguments:
            derived_command_with_arguments = command_with_arguments

    if derived_command_with_arguments:
        return True, derived_command_with_arguments
    if derived_command:
        return True, derived_command
    return False, args


def _compare_arguments_and_transform(args, index, section_key, alias_section):
    if not alias_section.get('command'):
        return []
    section_arguments = {}
    argument_name = None
    argument_value_name = None
    import shlex
    for item in shlex.split(section_key):
        if item.startswith('-'):
            if argument_name:
                section_arguments[argument_name] = argument_value_name
            argument_name = item
        else:
            argument_value_name = item.lstrip('{').rstrip('}').strip()
    if argument_name:
        section_arguments[argument_name] = argument_value_name
    args_left = []
    argument_values = {}
    argument_name = None
    argument_value = []
    for arg in args[index:]:
        if arg.startswith('-'):
            if argument_name:
                argument_values[argument_name] = argument_value
            if arg in section_arguments.keys():
                argument_name = arg
                argument_value = []
            else:
                argument_name = None
                argument_value = []
                args_left.append(arg)
        elif argument_name:
            argument_value.append(arg)
        else:
            args_left.append(arg)
    if argument_name:
        argument_values[argument_name] = argument_value
    if len(argument_values) != len(section_arguments):
        return []
    argument_value_dict = {}
    for (argument_name, argument_value_name) in section_arguments.items():
        if argument_value_name is None:
            continue
        argument_value = argument_values.get(argument_name)
        if not argument_value:
            argument_value = None
        if argument_value and len(argument_value) == 1:
            argument_value = argument_value[0]
        argument_value_dict[argument_value_name] = argument_value
    from jinja2 import Template
    template = Template(alias_section['command'])
    alias_command = template.render(argument_value_dict)
    return _transform_command_with_arguments(alias_command, args_left)


def _transform_command(args, index, alias_command):
    import shlex
    derived_command = shlex.split(alias_command)
    if index < len(args):
        derived_command.extend(args[index:])
    return derived_command


def _transform_command_with_arguments(alias_command, args_left):
    import shlex
    derived_command_with_arguments = shlex.split(alias_command)
    if args_left:
        derived_command_with_arguments.extend(args_left)
    return derived_command_with_arguments


def _is_section(alias_config):
    try:
        alias_config.keys()
    except AttributeError:
        return False
    return True
