# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import json
import pkgutil
import re
import time
import timeit
import traceback
from collections import OrderedDict, defaultdict
from importlib import import_module
from six import string_types

import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from azure.cli.core.application import APPLICATION
from azure.cli.core.telemetry import log_telemetry

from ._introspection import (extract_args_from_signature,
                             extract_full_summary_from_signature)

logger = _logging.get_az_logger(__name__)


# pylint: disable=too-many-arguments,too-few-public-methods


class CliArgumentType(object):
    REMOVE = '---REMOVE---'

    def __init__(self, overrides=None, **kwargs):
        if isinstance(overrides, str):
            raise ValueError("Overrides has to be a CliArgumentType (cannot be a string)")
        self.settings = {}
        self.update(overrides, **kwargs)

    def update(self, other=None, **kwargs):
        if other:
            self.settings.update(**other.settings)
        self.settings.update(**kwargs)


class CliCommandArgument(object):
    _NAMED_ARGUMENTS = ('options_list', 'validator', 'completer', 'id_part', 'arg_group')

    def __init__(self, dest=None, argtype=None, **kwargs):
        self.type = CliArgumentType(overrides=argtype, **kwargs)
        if dest:
            self.type.update(dest=dest)

        # We'll do an early fault detection to find any instances where we have inconsistent
        # set of parameters for argparse
        if not self.options_list and 'required' in self.options:  # pylint: disable=access-member-before-definition
            raise ValueError(message="You can't specify both required and an options_list")
        if not self.options.get('dest', False):
            raise ValueError('Missing dest')
        if not self.options_list:  # pylint: disable=access-member-before-definition
            self.options_list = ('--{}'.format(self.options['dest'].replace('_', '-')),)

    def __getattr__(self, name):
        if name in self._NAMED_ARGUMENTS:
            return self.type.settings.get(name, None)
        elif name == 'name':
            return self.type.settings.get('dest', None)
        elif name == 'options':
            return {key: value for key, value in self.type.settings.items()
                    if key != 'options' and key not in self._NAMED_ARGUMENTS and
                    not value == CliArgumentType.REMOVE}
        else:
            raise AttributeError(message=name)

    def __setattr__(self, name, value):
        if name == 'type':
            return super(CliCommandArgument, self).__setattr__(name, value)
        self.type.settings[name] = value


class LongRunningOperation(object):  # pylint: disable=too-few-public-methods

    def __init__(self, start_msg='', finish_msg='', poller_done_interval_ms=1000.0):
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poller_done_interval_ms = poller_done_interval_ms

    def _delay(self):
        time.sleep(self.poller_done_interval_ms / 1000.0)

    def __call__(self, poller):
        from msrest.exceptions import ClientException
        logger.info("Starting long running operation '%s'", self.start_msg)
        correlation_message = ''
        while not poller.done():
            try:
                # pylint: disable=protected-access
                correlation_id = json.loads(
                    poller._response.__dict__['_content'])['properties']['correlationId']

                correlation_message = 'Correlation ID: {}'.format(correlation_id)
            except:  # pylint: disable=bare-except
                pass

            try:
                self._delay()
            except KeyboardInterrupt:
                logger.error('Long running operation wait cancelled.  %s', correlation_message)
                raise
        try:
            result = poller.result()
        except ClientException as client_exception:
            log_telemetry('client exception', log_type='trace')
            message = getattr(client_exception, 'message', client_exception)

            try:
                message = '{} {}'.format(
                    str(message),
                    json.loads(client_exception.response.text)['error']['details'][0]['message'])
            except:  # pylint: disable=bare-except
                pass

            cli_error = CLIError('{}  {}'.format(message, correlation_message))
            # capture response for downstream commands (webapp) to dig out more details
            setattr(cli_error, 'response', getattr(client_exception, 'response', None))
            raise cli_error

        logger.info("Long running operation '%s' completed with result %s",
                    self.start_msg, result)
        return result


# pylint: disable=too-few-public-methods
class DeploymentOutputLongRunningOperation(LongRunningOperation):
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        outputs = result.properties.outputs
        return {key: val['value'] for key, val in outputs.items()} if outputs else {}


class CommandTable(dict):
    """A command table is a dictionary of name -> CliCommand
    instances.

    The `name` is the space separated name - i.e. 'vm list'
    """

    def register(self, name):
        def wrapped(func):
            cli_command(self, name, func)
            return func

        return wrapped


class CliCommand(object):  # pylint:disable=too-many-instance-attributes

    def __init__(self, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None):
        self.name = name
        self.handler = handler
        self.help = None
        self.description = description_loader() \
            if description_loader and CliCommand._should_load_description() \
            else description
        self.arguments = {}
        self.arguments_loader = arguments_loader
        self.table_transformer = table_transformer

    @staticmethod
    def _should_load_description():
        return not APPLICATION.session['completer_active']

    def load_arguments(self):
        if self.arguments_loader:
            self.arguments.update(self.arguments_loader())

    def add_argument(self, param_name, *option_strings, **kwargs):
        dest = kwargs.pop('dest', None)
        argument = CliCommandArgument(
            dest or param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        arg.type.update(other=argtype)

    def execute(self, **kwargs):
        return self.handler(**kwargs)


command_table = CommandTable()

# Map to determine what module a command was registered in
command_module_map = {}


def load_params(command):
    try:
        command_table[command].load_arguments()
    except KeyError:
        return
    command_module = command_module_map.get(command, None)
    if not command_module:
        logger.debug("Unable to load commands for '%s'. No module in command module map found.",
                     command)  # pylint: disable=line-too-long
        return
    module_to_load = command_module[:command_module.rfind('.')]
    import_module(module_to_load).load_params(command)
    _update_command_definitions(command_table)


def get_command_table():
    '''Loads command table(s)
    '''
    installed_command_modules = []
    try:
        mods_ns_pkg = import_module('azure.cli.command_modules')
        installed_command_modules = [modname for _, modname, _ in
                                     pkgutil.iter_modules(mods_ns_pkg.__path__)]
    except ImportError:
        pass
    logger.info('Installed command modules %s', installed_command_modules)
    cumulative_elapsed_time = 0
    for mod in installed_command_modules:
        try:
            start_time = timeit.default_timer()
            import_module('azure.cli.command_modules.' + mod).load_commands()
            elapsed_time = timeit.default_timer() - start_time
            logger.debug("Loaded module '%s' in %.3f seconds.", mod, elapsed_time)
            cumulative_elapsed_time += elapsed_time
        except Exception:  # pylint: disable=broad-except
            # Changing this error message requires updating CI script that checks for failed
            # module loading.
            logger.error("Error loading command module '%s'", mod)
            log_telemetry('Error loading module', module=mod)
            logger.debug(traceback.format_exc())
    logger.debug("Loaded all modules in %.3f seconds. "
                 "(note: there's always an overhead with the first module loaded)",
                 cumulative_elapsed_time)
    _update_command_definitions(command_table)
    ordered_commands = OrderedDict(command_table)
    return ordered_commands


def register_cli_argument(scope, dest, arg_type=None, **kwargs):
    '''Specify CLI specific metadata for a given argument for a given scope.
    '''
    _cli_argument_registry.register_cli_argument(scope, dest, arg_type, **kwargs)


def register_extra_cli_argument(command, dest, **kwargs):
    '''Register extra parameters for the given command. Typically used to augment auto-command built
    commands to add more parameters than the specific SDK method introspected.
    '''
    _cli_extra_argument_registry[command][dest] = CliCommandArgument(dest, **kwargs)


def cli_command(module_name, name, operation,
                client_factory=None, transform=None, table_transformer=None,
                no_wait_param=None):
    """ Registers a default Azure CLI command. These commands require no special parameters. """
    command_table[name] = create_command(module_name, name, operation, transform, table_transformer,
                                         client_factory, no_wait_param)


def get_op_handler(operation):
    """ Import and load the operation handler """
    try:
        mod_to_import, attr_path = operation.split('#')
        op = import_module(mod_to_import)
        for part in attr_path.split('.'):
            op = getattr(op, part)
        return op
    except (ValueError, AttributeError):
        raise ValueError("The operation '{}' is invalid.".format(operation))


def create_command(module_name, name, operation,
                   transform_result, table_transformer, client_factory,
                   no_wait_param=None):
    if not isinstance(operation, string_types):
        raise ValueError("Operation must be a string. Got '{}'".format(operation))

    def _execute_command(kwargs):
        from msrest.paging import Paged
        from msrest.exceptions import ClientException
        from msrestazure.azure_operation import AzureOperationPoller
        from azure.common import AzureException

        client = client_factory(kwargs) if client_factory else None
        try:
            op = get_op_handler(operation)
            result = op(client, **kwargs) if client else op(**kwargs)

            if no_wait_param and kwargs.get(no_wait_param, None):
                return None  # return None for 'no-wait'

            # apply results transform if specified
            if transform_result:
                return transform_result(result)

            # otherwise handle based on return type of results
            if isinstance(result, AzureOperationPoller):
                return LongRunningOperation('Starting {}'.format(name))(result)
            elif isinstance(result, Paged):
                return list(result)
            else:
                return result
        except ClientException as client_exception:
            log_telemetry('client exception', log_type='trace')
            message = getattr(client_exception, 'message', client_exception)
            raise _polish_rp_not_registerd_error(CLIError(message))
        except AzureException as azure_exception:
            log_telemetry('azure exception', log_type='trace')
            message = re.search(r"([A-Za-z\t .])+", str(azure_exception))
            raise CLIError('\n{}'.format(message.group(0) if message else str(azure_exception)))
        except ValueError as value_error:
            log_telemetry('value exception', log_type='trace')
            raise CLIError(value_error)
        except CLIError as cli_error:
            raise _polish_rp_not_registerd_error(cli_error)

    command_module_map[name] = module_name
    name = ' '.join(name.split())

    def arguments_loader():
        return extract_args_from_signature(get_op_handler(operation), no_wait_param=no_wait_param)

    def description_loader():
        return extract_full_summary_from_signature(get_op_handler(operation))

    cmd = CliCommand(name, _execute_command, table_transformer=table_transformer,
                     arguments_loader=arguments_loader, description_loader=description_loader)
    return cmd


def _polish_rp_not_registerd_error(cli_error):
    msg = str(cli_error)
    pertinent_text_namespace = 'The subscription must be registered to use namespace'
    pertinent_text_feature = 'is not registered for feature'
    # pylint: disable=line-too-long
    if pertinent_text_namespace in msg:
        reg = r".*{} '(.*)'".format(pertinent_text_namespace)
        match = re.match(reg, msg)
        cli_error = CLIError(
            "Run 'az provider register -n {}' to register the namespace first".format(
                match.group(1)))
    elif pertinent_text_feature in msg:
        reg = r".*{}\s+([^\s]+)\s+".format(pertinent_text_feature)
        match = re.match(reg, msg)
        parts = match.group(1).split('/')
        if len(parts) == 2:
            cli_error = CLIError(
                "Run 'az feature register --namespace {} -n {}' to enable the feature first".format(
                    parts[0], parts[1]))
    return cli_error


def _get_cli_argument(command, argname):
    return _cli_argument_registry.get_cli_argument(command, argname)


def _get_cli_extra_arguments(command):
    return _cli_extra_argument_registry[command].items()


class _ArgumentRegistry(object):
    def __init__(self):
        self.arguments = defaultdict(lambda: {})

    def register_cli_argument(self, scope, dest, argtype, **kwargs):
        argument = CliArgumentType(overrides=argtype,
                                   **kwargs)
        self.arguments[scope][dest] = argument

    def get_cli_argument(self, command, name):
        parts = command.split()
        result = CliArgumentType()
        for index in range(0, len(parts) + 1):
            probe = ' '.join(parts[0:index])
            override = self.arguments.get(probe, {}).get(name, None)
            if override:
                result.update(override)
        return result


_cli_argument_registry = _ArgumentRegistry()
_cli_extra_argument_registry = defaultdict(lambda: {})


def _update_command_definitions(command_table_to_update):
    for command_name, command in command_table_to_update.items():
        for argument_name in command.arguments:
            overrides = _get_cli_argument(command_name, argument_name)
            command.update_argument(argument_name, overrides)

        # Add any arguments explicitly registered for this command
        for argument_name, argument_definition in _get_cli_extra_arguments(command_name):
            command.arguments[argument_name] = argument_definition
            command.update_argument(argument_name, _get_cli_argument(command_name, argument_name))
