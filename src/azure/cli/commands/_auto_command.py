from __future__ import print_function
import inspect
import sys
from msrest.paging import Paged
from msrest.exceptions import ClientException
from azure.cli.parser import IncorrectUsageError
from ..commands import COMMON_PARAMETERS

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config'])

class AutoCommandDefinition(object): #pylint: disable=too-few-public-methods

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

def _make_func(client_factory, member_path, return_type_or_func, unbound_func):
    def call_client(args):
        client = client_factory(args)
        ops_instance = _get_member(client, member_path)

        # TODO: Remove this conversion code once internal key references are updated (#116797761)
        converted_params = {}
        for key in args.keys():
            converted_key = key.replace('-', '_')
            converted_params[converted_key] = args[key]

        try:
            result = unbound_func(ops_instance, **converted_params)
            if not return_type_or_func:
                return {}
            if callable(return_type_or_func):
                return return_type_or_func(result)
            if isinstance(return_type_or_func, str):
                return list(result) if isinstance(result, Paged) else result
        except TypeError as exception:
            # TODO: Evaluate required/missing parameters and provide specific
            # usage for missing params...
            raise IncorrectUsageError(exception)
        except ClientException as client_exception:
            # TODO: Better error handling for cloud exceptions...
            message = getattr(client_exception, 'message', client_exception)
            print(message, file=sys.stderr)

    return call_client

def _option_description(operation, arg):
    """Pull out parameter help from doccomments of the command
    """
    # TODO: We are currently doing this for every option/argument.
    # We should do it (at most) once for a given command...
    return ' '.join(l.split(':')[-1] for l in inspect.getdoc(operation).splitlines()
                    if l.startswith(':param') and arg + ':' in l)

#pylint: disable=too-many-arguments
def build_operation(command_name,
                    member_path,
                    client_type,
                    operations,
                    command_table,
                    common_parameters=None,
                    extra_parameters=None):

    merged_common_parameters = COMMON_PARAMETERS.copy()
    merged_common_parameters.update(common_parameters or {})
    extra_parameters = extra_parameters or {}

    for op in operations:

        func = _make_func(client_type, member_path, op.return_type, op.operation)

        args = []
        try:
            # only supported in python3 - falling back to argspec if not available
            sig = inspect.signature(op.operation)
            args = sig.parameters
        except AttributeError:
            sig = inspect.getargspec(op.operation) #pylint: disable=deprecated-method
            args = sig.args

        options = []
        for arg in [a for a in args if not a in EXCLUDED_PARAMS]:
            try:
                # this works in python3
                default = args[arg].default
                required = default == inspect.Parameter.empty # pylint: disable=no-member
            except TypeError:
                arg_defaults = dict(zip(sig.args[-len(sig.defaults):], sig.defaults))
                default = arg_defaults[arg] if arg in arg_defaults else None
                required = False if default else True

            # TODO: Add action here if a boolean default value exists to create a flag

            common_param = merged_common_parameters.get(arg, {
                'name': '--' + arg.replace('_', '-'),
                'required': required,
                'default': default,
                'help': _option_description(op.operation, arg)
            }).copy() # We need to make a copy to allow consumers to mutate the value
                      # retrieved from the common parameters without polluting future
                      # use...
            common_param['dest'] = common_param.get('dest', arg)
            options.append(common_param)

        # append any 'extra' args needed (for example to obtain a client) that aren't required
        # by the SDK.
        for arg in extra_parameters.values():
            options.append(arg.copy())

        command_table[func] = {
            'name': ' '.join([command_name, op.opname]),
            'handler': func,
            'arguments': options
            }
