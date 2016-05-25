from __future__ import print_function
import re
import inspect
from msrest.paging import Paged
from msrest.exceptions import ClientException
from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError
from ..commands import COMMON_PARAMETERS, CliCommand
from azure.cli.commands.argument_types import \
    get_cli_argument, CliArgumentType, _cli_extra_argument_registry as extra_argument_registry

# TODO THIS ENTIRE FILE ONCE CONVERSION IS COMPLETE. MAKE CHANGES IN commands.__init__ ############

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config',
                             'content_version', 'kwargs', 'client'])


class CommandDefinition(object): #pylint: disable=too-few-public-methods

    def __init__(self, operation, return_type, command_alias=None):
        self.operation = operation
        self.return_type = return_type
        self.opname = command_alias if command_alias else operation.__name__.replace('_', '-')

def _decorate_option(command_table, func, name, **kwargs):
    return command_table.option(name, kwargs=kwargs['kwargs'])(func)

def _get_member(obj, path):
    """Recursively walk down the dot-separated path
    to get child item.

    Ex. a.b.c would get the property 'c' of property 'b' of the
        object a
    """
    path = path or ''
    for segment in path.split('.'):
        try:
            obj = getattr(obj, segment)
        except AttributeError:
            pass
    return obj

def _make_func(client_factory, member_path, return_type_or_func, unbound_func, extra_parameters,
               command_name=None):
    def call_client(kwargs):
        client = client_factory(**kwargs) if client_factory else None

        for param in extra_parameters.keys() if extra_parameters else []:
            kwargs.pop(param)

        ops_instance = _get_member(client, member_path) if client else member_path

        try:
            result = unbound_func(ops_instance, **kwargs)
            if not return_type_or_func:
                return {}
            if callable(return_type_or_func):
                return return_type_or_func(result)
            if isinstance(return_type_or_func, str):
                return list(result) if isinstance(result, Paged) else result
        except TypeError as exception:
            raise IncorrectUsageError(exception)
        except ClientException as client_exception:
            message = getattr(client_exception, 'message', client_exception)
            raise CLIError(message)

    return call_client

def _option_descriptions(operation):
    """Pull out parameter help from doccomments of the command
    """
    option_descs = {}
    lines = inspect.getdoc(operation)
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
                    if temp.startswith(':'):
                        break
                    else:
                        if temp:
                            arg_desc += (' ' + temp)
                        index += 1

                option_descs[arg_name] = arg_desc
            else:
                index += 1
    return option_descs

def _extract_args_from_signature(command, operation):
    """ Extracts basic argument data from an operation's signature and docstring """
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
            required = arg not in arg_defaults

        action = 'store_' + str(not default).lower() if isinstance(default, bool) else None

        try:
            default = (default
                        if default != inspect._empty #pylint: disable=protected-access, no-member
                        else None)
        except AttributeError:
            pass

        command.add_argument(arg_name,
                            *['--' + arg_name.replace('_', '-')],
                            required=required,
                            default=default,
                            help=arg_docstring_help.get(arg_name),
                            action=action)


def build_operation(command_name,
                    member_path,
                    client_type,
                    operations,
                    command_table,
                    param_aliases=None,
                    extra_parameters=None,
                    argument_types={}):
    built_commands = []
    for op in operations:
        cmd = _build_operation(command_name,
                               member_path,
                               client_type,
                               op,
                               argument_types,
                               param_aliases,
                               extra_parameters)
        built_commands.append(cmd)
        command_table[cmd.name] = cmd
    return built_commands

#pylint: disable=too-many-arguments
def _build_operation(command_name,
                     member_path,
                     client_type,
                     op,
                     argument_types={},
                     param_aliases=None,
                     extra_parameters=None):

    full_command_name = ' '.join([command_name, op.opname])
    func = _make_func(client_type, member_path, op.return_type, op.operation, extra_parameters,
                      command_name=full_command_name)

    command = CliCommand(full_command_name, func)
    _extract_args_from_signature(command, op.operation)
        
    # append any 'extra' args needed (for example to obtain a client) that aren't required
    # by the SDK.
    if extra_parameters:
        for arg in extra_parameters.keys():
            options.append(extra_parameters[arg].copy())

    return command

def cli_command(name, client_factory, func, return_type, command_table):
    return build_operation(' '.join(name.split()[:-1]),
                           None,
                           client_factory,
                           [CommandDefinition(func, return_type, command_alias=name.split()[-1])],
                           command_table)[0]
