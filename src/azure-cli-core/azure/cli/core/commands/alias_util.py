# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import shlex


def find_alias_and_transform_args(args, root_alias_nodes):
    if not root_alias_nodes:
        root_alias_nodes = _build_alias_tree()

    matched_node = None
    find_in_nodes = root_alias_nodes
    for item in args:
        if not find_in_nodes.get(item):
            break
        matched_node = find_in_nodes.get(item)
        find_in_nodes = matched_node.next_nodes

    if not matched_node or (not matched_node.command and not matched_node.argument_sections):
        return args

    new_args = _compare_and_transform(args, matched_node)
    return find_alias_and_transform_args(new_args, root_alias_nodes)


def _build_alias_tree():
    def _is_section(config):
        try:
            config.keys()
        except AttributeError:
            return False
        return True

    import os
    import configobj
    alias_fp = os.path.join(os.path.dirname(__file__), 'built_in_alias')
    alias_config = configobj.ConfigObj(alias_fp, interpolation=None)
    root_nodes = {}
    # read config section by section
    # each section key is full cmd, eg. storage account bsp
    for full_cmd_name in alias_config.keys():
        if not full_cmd_name:
            continue
        node = None
        # parse full cmd, build alias node for each cmd
        for cmd_name in shlex.split(full_cmd_name):
            # for the first cmd name, get node from root_nodes or create a new node and insert into root_nodes
            if not node:
                if root_nodes.get(cmd_name):
                    node = root_nodes.get(cmd_name)
                else:
                    node = AliasNode(cmd_name)
                    root_nodes[cmd_name] = node
                continue
            # for other cmd names, create a new node as the child of previous node or get previous node's existing child
            if not node.next_nodes.get(cmd_name):
                new_node = AliasNode(cmd_name, level=node.level+1)
                node.add_next(new_node)
                node = new_node
            else:
                node = node.next_nodes.get(cmd_name)
        # parse section command and argument sub sections
        node.command = alias_config[full_cmd_name].get('command')
        for key in alias_config[full_cmd_name].keys():
            if not key or not _is_section(alias_config[full_cmd_name][key]):
                continue
            if alias_config[full_cmd_name][key].get('command'):
                node.argument_sections[key] = alias_config[full_cmd_name][key].get('command')
    return root_nodes


def _compare_and_transform(args, alias_node):
    derived_command = shlex.split(alias_node.command) if alias_node.command else []
    if derived_command and alias_node.level + 1 < len(args):
        derived_command.extend(args[alias_node.level + 1:])
    # We will only continue parse arguments section only if the left parts of the input args are all arguments
    if alias_node.level + 1 == len(args) or (not args[alias_node.level + 1].startswith('-')):
        return derived_command if derived_command else args

    derived_command_with_arguments = []
    for (argument_alias, argument_command) in alias_node.argument_sections.items():
        command_with_arguments = _compare_arguments_and_transform(args[alias_node.level + 1:],
                                                                  argument_alias, argument_command)
        if command_with_arguments:
            derived_command_with_arguments = command_with_arguments

    if derived_command_with_arguments:
        return derived_command_with_arguments
    if derived_command:
        return derived_command
    return args


def _compare_arguments_and_transform(args, argument_alias, argument_command):
    if not argument_command:
        return []
    # parse argument_alias
    # input: argument_alias = "--list-defaults {{defaults_flag}} --scope {{scope}} --only-show-errors"
    # output: section_arguments = {'--list-defaults': 'defaults_flag', '--scope': 'scope', '--only-show-errors': None}
    section_arguments = {}
    argument_name = None
    argument_value_name = None
    import shlex
    for item in shlex.split(argument_alias):
        if item.startswith('-'):
            if argument_name:
                section_arguments[argument_name] = argument_value_name
            argument_name = item
        else:
            argument_value_name = item.lstrip('{').rstrip('}').strip()
    if argument_name:
        section_arguments[argument_name] = argument_value_name

    # parse args
    # input:
    #   args = ['--list-defaults', '--scope', 'local', '--query', '[].name']
    #   section_arguments = {'--list-defaults': 'defaults_flag', '--scope': 'scope', '--only-show-errors': None}
    # output:
    #   argument_values = {'--list-defaults': None, '--scope': 'local'}
    #   args_left = ['--query', '[].name']
    args_left = []
    argument_values = {}
    argument_name = None
    argument_value = []
    for arg in args:
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
    # check if args cover all the arguments in argument_alias
    if len(argument_values) != len(section_arguments):
        return []
    # read argument value
    # input:
    #   section_arguments = {'--list-defaults': 'defaults_flag', '--scope': 'scope'}
    #   argument_values = {'--list-defaults': None, '--scope': 'local'}
    # output:
    #   argument_value_dict = {'defaults_flag': None, 'scope': 'local'}
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
    # parse argument_command use argument_value_dict
    # input:
    #   argument_value_dict = {'defaults_flag': None, 'scope': 'local'}
    #   argument_command = "config get {% if defaults_flag!="false" %} defaults{% endif %}{% if scope=='local'%} --local{% endif %}"
    # output:
    #   alias_command = "config get defaults --local"
    from jinja2 import Template
    template = Template(argument_command)
    alias_command = template.render(argument_value_dict)

    derived_command_with_arguments = shlex.split(alias_command)
    if args_left:
        derived_command_with_arguments.extend(args_left)
    return derived_command_with_arguments


class AliasNode:
    def __init__(self, name, command=None, argument_sections=None, next_nodes=None, level=None):
        self.name = name
        self.command = command
        self.argument_sections = argument_sections if argument_sections else {}
        self.next_nodes = next_nodes if next_nodes else {}
        self.level = level if level else 0

    def add_next(self, node):
        self.next_nodes[node.name] = node
