# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

""" Utility file for introspection.
"""

import inspect
import re

from .arguments import CLICommandArgument


def extract_full_summary_from_signature(operation):
    """ Extract the summary from the docstring of the command. """
    lines = inspect.getdoc(operation)
    regex = r'\s*(:param)\s+(.+?)\s*:(.*)'
    summary = ''
    if lines:
        match = re.search(regex, lines)
        summary = lines[:match.regs[0][0]] if match else lines

    summary = summary.replace('\n', ' ').replace('\r', '')
    return summary


def option_descriptions(operation):
    """ Extract parameter help from docstring of the command. """
    lines = inspect.getdoc(operation)

    if not lines:
        return {}

    param_breaks = ["'''", '"""', ':param', ':type', ':return', ':rtype']
    option_descs = {}

    lines = lines.splitlines()
    index = 0
    while index < len(lines):
        l = lines[index]
        regex = r'\s*(:param)\s+(.+?)\s*:(.*)'
        match = re.search(regex, l)
        if not match:
            index += 1
            continue

        # 'arg name' portion might have type info, we don't need it
        arg_name = str.split(match.group(2))[-1]
        arg_desc = match.group(3).strip()
        # look for more descriptions on subsequent lines
        index += 1
        while index < len(lines):
            temp = lines[index].strip()
            if any(temp.startswith(x) for x in param_breaks):
                break
            if temp:
                arg_desc += (' ' + temp)
            index += 1

        option_descs[arg_name] = arg_desc

    return option_descs


def extract_args_from_signature(operation, excluded_params=None):
    """ Extracts basic argument data from an operation's signature and docstring
        excluded_params: List of params to ignore and not extract. By default we ignore ['self', 'kwargs'].
    """
    sig = inspect.signature(operation)
    args = sig.parameters

    arg_docstring_help = option_descriptions(operation)
    excluded_params = excluded_params or ['self', 'kwargs']

    for arg_name in [a for a in args if a not in excluded_params]:
        default = args[arg_name].default
        required = default == inspect.Parameter.empty
        action = 'store_' + str(not default).lower() if isinstance(default, bool) else None
        command_argument_default = default if default != inspect.Parameter.empty else None
        options_list = ['--' + arg_name.replace('_', '-')]
        help_str = arg_docstring_help.get(arg_name)

        yield (arg_name, CLICommandArgument(arg_name,
                                            options_list=options_list,
                                            required=required,
                                            default=command_argument_default,
                                            help=help_str,
                                            action=action))
