from __future__ import print_function
import inspect
import sys
from msrest.paging import Paged
from msrest.exceptions import ClientException
from azure.cli.parser import IncorrectUsageError
from ..commands import COMMON_PARAMETERS
from ..commands import command, description, option
from .._logging import logger

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config'])

class AutoCommandDefinition(object): #pylint: disable=too-few-public-methods

    def __init__(self, operation, return_type, command_alias=None):
        self.operation = operation
        self.return_type = return_type
        self.opname = command_alias if command_alias else operation.__name__.replace('_', '-')

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
    if not path:
        return obj
    for segment in path.split('.'):
        obj = getattr(obj, segment)
    return obj

def _make_func(client_factory, member_path, return_type_or_func, unbound_func):
    def call_client(args):
        client = client_factory(args)
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

#pylint: disable=too-many-arguments
def build_operation(command_name,
                    member_path,
                    client_type,
                    operations,
                    command_table,
                    common_parameters=None):

    common_parameters = common_parameters or COMMON_PARAMETERS
    for op in operations:
        func = _make_func(client_type, member_path, op.return_type_name, op.operation)
        func = _decorate_command(' '.join([command_name, op.opname]), func)

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
            #spec = paramaliases.get(arg, '--%s <%s>' % (arg, arg))
            #func = _decorate_option(spec, _option_description(op.operation, arg),
            #                        target=arg, func=func)
            common_param = common_parameters.get(arg, {
                'name': '--' + arg.replace('_', '-'),
                'required': True,
                'help': _option_description(operation, arg)
            }).copy() # We need to make a copy to allow consumers to mutate the value
                      # retrieved from the common parameters without polluting future
                      # use...
            common_param['dest'] = common_param.get('dest', arg)
            options.append(common_param)

        command_table[func] = {
            'name': ' '.join([command_name, opname]),
            'handler': func,
            'arguments': options
            }

        if common_parameters:
            for arg in common_parameters:
                if len(arg) != 2:
                    logger.warning('%s is in invalid format. Should be: (spec, description)',
                                   (str(arg)))
                    continue
                func = _decorate_option(arg[0], arg[1], target=None, func=func)
