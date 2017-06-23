# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import re


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


def _option_descriptions(operation):
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
            else:
                if temp:
                    arg_desc += (' ' + temp)
                index += 1

        option_descs[arg_name] = arg_desc

    return option_descs


EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config',
                             'content_version', 'kwargs', 'client'])


def extract_args_from_signature(operation, no_wait_param=None):
    """ Extracts basic argument data from an operation's signature and docstring
        no_wait_param: SDK parameter which disables LRO polling. For now it is 'raw'
    """
    from azure.cli.core.commands import CliCommandArgument
    args = []
    try:
        # only supported in python3 - falling back to argspec if not available
        sig = inspect.signature(operation)
        args = sig.parameters
    except AttributeError:
        sig = inspect.getargspec(operation)  # pylint: disable=deprecated-method
        args = sig.args

    arg_docstring_help = _option_descriptions(operation)
    excluded_params = list(EXCLUDED_PARAMS)
    if no_wait_param in excluded_params:
        excluded_params.remove(no_wait_param)
    found_no_wait_param = False

    for arg_name in [a for a in args if a not in excluded_params]:
        try:
            # this works in python3
            default = args[arg_name].default
            required = default == inspect.Parameter.empty  # pylint: disable=no-member
        except TypeError:
            arg_defaults = (dict(zip(sig.args[-len(sig.defaults):], sig.defaults))
                            if sig.defaults
                            else {})
            default = arg_defaults.get(arg_name)
            required = arg_name not in arg_defaults

        action = 'store_' + str(not default).lower() if isinstance(default, bool) else None

        try:
            default = (default
                       if default != inspect._empty  # pylint: disable=protected-access, no-member
                       else None)
        except AttributeError:
            pass

        # improve the naming to 'no_wait'
        if arg_name == no_wait_param:
            if not isinstance(default, bool):
                raise ValueError("The type of '{}' must be boolean to enable no_wait".format(
                    no_wait_param))
            found_no_wait_param = True
            options_list = ['--no-wait']
            help_str = 'do not wait for the long running operation to finish'
        else:
            options_list = ['--' + arg_name.replace('_', '-')]
            help_str = arg_docstring_help.get(arg_name)

        yield (arg_name, CliCommandArgument(arg_name,
                                            options_list=options_list,
                                            required=required,
                                            default=default,
                                            help=help_str,
                                            action=action))
    if no_wait_param and not found_no_wait_param:
        raise ValueError("Command authoring error: unable to enable no-wait option. Operation '{}' "
                         "does not have a '{}' parameter.".format(operation, no_wait_param))
