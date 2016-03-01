import inspect
from msrest import Serializer
from ..commands import command, description, option
from azure.cli._argparse import IncorrectUsageError

def _decorate_command(name, func):
    return command(name)(func)

def _decorate_description(desc, func):
    return description(desc)(func)

def _decorate_option(spec, descr, func):
    return option(spec, descr)(func)

def _make_func(client_factory, member_name, return_type_name, unbound_func):
    def call_client(args, unexpected): #pylint: disable=unused-argument
        client = client_factory()
        ops_instance = getattr(client, member_name)
        try:
            result = unbound_func(ops_instance, **args)
            if not return_type_name:
                return {}
            return Serializer().serialize_data(result, return_type_name)
        except TypeError as exception:
            # TODO: Evaluate required/missing parameters and provide specific
            # usage for missing params...
            raise IncorrectUsageError(exception)

    return call_client

def _option_description(operation, arg):
    """Pull out parameter help from doccomments of the command
    """
    # TODO: We are currently doing this for every option/argument.
    # We should do it (at most) once for a given command...
    return ' '.join(l.split(':')[-1] for l in inspect.getdoc(operation).splitlines()
                    if l.startswith(':param') and arg + ':' in l)

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config'])

def operation_builder(package_name, resource_type, member_name, client_type, operations):
    for operation, return_type_name in operations:
        opname = operation.__name__
        func = _make_func(client_type, member_name, return_type_name, operation)
        func = _decorate_command(' '.join([package_name, resource_type, opname]), func)

        args = []
        try:
            # only supported in python3 - falling back to argspec if not available
            sig = inspect.signature(operation)
            args = sig.parameters
        except AttributeError:
            sig = inspect.getargspec(operation) #pylint: disable=deprecated-method
            args = sig.args

        for arg in [a for a in args if not a in EXCLUDED_PARAMS]:
            spec = '--%s <%s>' % (arg, arg)
            func = _decorate_option(spec, _option_description(operation, arg), func=func)
