#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import inspect
import re

def extract_full_summary_from_signature(operation):
    """ Extract the summary from the doccomments of the command. """
    lines = inspect.getdoc(operation)
    regex = r'\s*(:param)\s+(.+)\s*:(.*)'
    summary = ''
    if lines:
        match = re.search(regex, lines)
        if match:
            summary = lines[:match.regs[0][0]]
        else:
            summary = lines
    return summary

def _option_descriptions(operation):
    """ Extract parameter help from doccomments of the command. """
    option_descs = {}
    lines = inspect.getdoc(operation)
    param_breaks = ["'''", '"""', ':param', ':type', ':return', ':rtype']
    if lines:
        lines = lines.splitlines()
        index = 0
        while index < len(lines):
            l = lines[index]
            regex = r'\s*(:param)\s+(.+)\s*:(.*)'
            match = re.search(regex, l)
            if match:
                # 'arg name' portion might have type info, we don't need it
                arg_name = str.split(match.group(2))[-1]
                arg_desc = match.group(3).strip()
                #look for more descriptions on subsequent lines
                index += 1
                while index < len(lines):
                    temp = lines[index].strip()
                    if any(temp.startswith(x) for x in param_breaks):
                        break
                    else:
                        if temp:
                            arg_desc += (' ' + temp)
                        index += 1

                option_descs[arg_name] = arg_desc
            else:
                index += 1
    return option_descs

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config',
                             'content_version', 'kwargs', 'client'])

def extract_args_from_signature(operation):
    """ Extracts basic argument data from an operation's signature and docstring """
    from azure.cli.core.commands import CliCommandArgument
    args = []
    try:
        # only supported in python3 - falling back to argspec if not available
        sig = inspect.signature(operation)
        args = sig.parameters
    except AttributeError:
        sig = inspect.getargspec(operation) #pylint: disable=deprecated-method
        args = sig.args

    arg_docstring_help = _option_descriptions(operation)
    for arg_name in [a for a in args if not a in EXCLUDED_PARAMS]:
        try:
            # this works in python3
            default = args[arg_name].default
            required = default == inspect.Parameter.empty #pylint: disable=no-member
        except TypeError:
            arg_defaults = (dict(zip(sig.args[-len(sig.defaults):], sig.defaults))
                            if sig.defaults
                            else {})
            default = arg_defaults.get(arg_name)
            required = arg_name not in arg_defaults

        action = 'store_' + str(not default).lower() if isinstance(default, bool) else None

        try:
            default = (default
                       if default != inspect._empty #pylint: disable=protected-access, no-member
                       else None)
        except AttributeError:
            pass

        yield (arg_name, CliCommandArgument(arg_name,
                                            options_list=['--' + arg_name.replace('_', '-')],
                                            required=required,
                                            default=default,
                                            help=arg_docstring_help.get(arg_name),
                                            action=action))

