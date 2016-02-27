import inspect
import sys
from msrest import Serializer
from ..main import CONFIG, SESSION
from ..commands import command, description, option
from .._logging import logger
from azure.cli._argparse import IncorrectUsageError

def _decorate_command(name, func):
    return command(name)(func)

def _decorate_description(desc, func):
    return description(desc)(func)

def _decorate_option(spec, description, func):
    return option(spec, description)(func)
    
def _make_func(client_factory, member_name, return_type_name, unbound_func):
    def call_client(args, unexpected):
        client = client_factory()
        ops_instance = getattr(client, member_name)
        try:
            result = unbound_func(ops_instance, **args)
            if not return_type_name:
                return {}
            return Serializer().serialize_data(result, return_type_name)
        except TypeError as e:
            # TODO: Evaluate required/missing parameters and provide specific
            # usage for missing params...
            raise IncorrectUsageError(e)

    return call_client
    
def _option_description(op, arg):
    """Pull out parameter help from doccomments of the command
    """
    # TODO: We are currently doing this for every option/argument. We should do it (at most) once for a given command...    
    return ' '.join([l.split(':')[-1] for l in inspect.getdoc(op).splitlines() if l.startswith(':param') and l.find(arg + ':') != -1])

def _operation_builder(package_name, resource_type, member_name, client_type, operations):
    excluded_params = ['self', 'raw', 'custom_headers', 'operation_config']
    for operation, return_type_name in operations:
        opname = operation.__name__
        func = _make_func(client_type, member_name, return_type_name, operation)
        func = _decorate_command(' '.join([package_name, resource_type, opname]), func)
        func = _decorate_description('This is the description of the command...', func)

        args = []
        try:
            sig = inspect.signature(operation) # only supported in python3 - falling back to argspec if not available
            args = sig.parameters
        except AttributeError:
            sig = inspect.getargspec(operation)
            args = sig.args

        for arg in [a for a in args if not a in excluded_params]:
            func = _decorate_option('--%s <%s>' % (arg, arg), _option_description(operation, arg), func=func) 
