from __future__ import print_function
import inspect
from msrest.paging import Paged
from msrest.exceptions import ClientException
from azure.cli.parser import IncorrectUsageError
from ..commands import COMMON_PARAMETERS

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config',
                             'content_version'])

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

def _make_func(client_factory, member_path, return_type_or_func, unbound_func, preamble=None):
    def call_client(args):
        client = client_factory(args)
        ops_instance = _get_member(client, member_path)

        try:
            if preamble:
                preamble(ops_instance, args)
            result = unbound_func(ops_instance, **args)
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
            raise RuntimeError(message)

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
                    param_aliases=None,
                    extra_parameters=None,
                    preamble=None):

    for op in operations:

        func = _make_func(client_type, member_path, op.return_type, op.operation, preamble)

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
                required = default == inspect.Parameter.empty #pylint: disable=no-member
            except TypeError:
                arg_defaults = dict(zip(sig.args[-len(sig.defaults):], sig.defaults))
                default = arg_defaults.get(arg)
                required = arg not in arg_defaults

            action = 'store_' + str(not default).lower() if isinstance(default, bool) else None

            try:
                default = (default
                           if default != inspect._empty #pylint: disable=protected-access, no-member
                           else None)
            except AttributeError:
                pass

            parameter = {
                'name': '--' + arg.replace('_', '-'),
                'required': required,
                'default': default,
                'dest': arg,
                'help': _option_description(op.operation, arg),
                'action': action
            }
            parameter.update(COMMON_PARAMETERS.get(arg, {}))
            if param_aliases:
                parameter.update(param_aliases.get(arg, {}))

            options.append(parameter)

        # append any 'extra' args needed (for example to obtain a client) that aren't required
        # by the SDK.
        if extra_parameters:
            for arg in extra_parameters:
                options.append(arg.copy())

        command_table[func] = {
            'name': ' '.join([command_name, op.opname]),
            'handler': func,
            'arguments': options
            }
