from __future__ import print_function
import inspect
import sys
import time
from msrest.paging import Paged
from msrest.exceptions import ClientException
from azure.cli._argparse import IncorrectUsageError
from ..commands import command, description, option


EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config'])
GLOBALPARAMALIASES = {
    'resource_group_name': '--resourcegroup --rg <resourcegroupname>'
}



class LongRunningOperation(object): #pylint: disable=too-few-public-methods

    progress_file = sys.stderr

    def __init__(self, start_msg='', finish_msg='', poll_interval_ms=1000.0):
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poll_interval_ms = poll_interval_ms

    def __call__(self, poller):
        print(self.start_msg, file=self.progress_file)

        succeeded = False
        try:
            while not poller.done():
                if self.progress_file:
                    print('.', end='', file=self.progress_file)
                    self.progress_file.flush()
                time.sleep(self.poll_interval_ms / 1000.0)
            result = poller.result()
            succeeded = True
            return result
        finally:
            # Ensure that we get a newline after the dots...
            if self.progress_file:
                print(file=self.progress_file)
                print(self.finish_msg if succeeded else '', file=self.progress_file)

def _decorate_command(name, func):
    return command(name)(func)

def _decorate_description(desc, func):
    return description(desc)(func)

def _decorate_option(spec, descr, target, func):
    return option(spec, descr, target=target)(func)

def _get_member(obj, path):
    """Recursively walk down the dot-separated path
    to get child item.

    Ex. a.b.c would get the property 'c' of property 'b' of the
        object a
    """
    for segment in path.split('.'):
        obj = getattr(obj, segment)
    return obj

def _make_func(client_factory, member_path, return_type_or_func, unbound_func):
    def call_client(args, unexpected): #pylint: disable=unused-argument
        client = client_factory()
        ops_instance = _get_member(client, member_path)
        try:
            result = unbound_func(ops_instance, **args)
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

def build_operation(command_name, member_path, client_type, operations, #pylint: disable=dangerous-default-value
                    paramaliases=GLOBALPARAMALIASES):
    for operation, return_type_name in operations:
        opname = operation.__name__.replace('_', '-')
        func = _make_func(client_type, member_path, return_type_name, operation)
        func = _decorate_command(' '.join([command_name, opname]), func)

        args = []
        try:
            # only supported in python3 - falling back to argspec if not available
            sig = inspect.signature(operation)
            args = sig.parameters
        except AttributeError:
            sig = inspect.getargspec(operation) #pylint: disable=deprecated-method
            args = sig.args

        for arg in [a for a in args if not a in EXCLUDED_PARAMS]:
            spec = paramaliases.get(arg, '--%s <%s>' % (arg, arg))
            func = _decorate_option(spec, _option_description(operation, arg),
                                    target=arg, func=func)
