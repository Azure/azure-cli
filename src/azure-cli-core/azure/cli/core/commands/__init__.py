#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import json
import re
import time
import traceback
import pkgutil
from importlib import import_module
from collections import OrderedDict, defaultdict

from azure.cli.core._util import CLIError
import azure.cli.core._logging as _logging
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
        if not self.options_list and 'required' in self.options: # pylint: disable=access-member-before-definition
            raise ValueError(message="You can't specify both required and an options_list")
        if not self.options.get('dest', False):
            raise ValueError('Missing dest')
        if not self.options_list: # pylint: disable=access-member-before-definition
            self.options_list = ('--{}'.format(self.options['dest'].replace('_', '-')),)

    def __getattr__(self, name):
        if name in self._NAMED_ARGUMENTS:
            return self.type.settings.get(name, None)
        elif name == 'name':
            return self.type.settings.get('dest', None)
        elif name == 'options':
            return {key: value for key, value in self.type.settings.items()
                    if key != 'options' and not key in self._NAMED_ARGUMENTS
                    and not value == CliArgumentType.REMOVE}
        else:
            raise AttributeError(message=name)

    def __setattr__(self, name, value):
        if name == 'type':
            return super(CliCommandArgument, self).__setattr__(name, value)
        self.type.settings[name] = value

class LongRunningOperation(object): #pylint: disable=too-few-public-methods

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
                correlation_message = 'Correlation ID: {}' \
                    .format(json.loads(poller._response.__dict__['_content']) #pylint: disable=protected-access
                            ['properties']['correlationId'])
            except: #pylint: disable=bare-except
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
                message = str(message) + ' ' + json.loads(client_exception.response.text) \
                    ['error']['details'][0]['message']
            except: #pylint: disable=bare-except
                pass

            cli_error = CLIError('{}  {}'.format(message, correlation_message))
            #capture response for downstream commands (webapp) to dig out more details
            setattr(cli_error, 'response', getattr(client_exception, 'response', None))
            raise cli_error

        logger.info("Long running operation '%s' completed with result %s",
                    self.start_msg, result)
        return result

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
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

class CliCommand(object):

    def __init__(self, name, handler, description=None, table_transformer=None):
        self.name = name
        self.handler = handler
        self.description = description
        self.help = None
        self.arguments = {}
        self.table_transformer = table_transformer

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

def get_command_table(module_name=None):
    '''Loads command table(s)
    When `module_name` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    loaded = False
    # TODO Remove check for acs module. Issue #1110
    if module_name and module_name != 'acs':
        try:
            import_module('azure.cli.command_modules.' + module_name)
            logger.info("Successfully loaded command table from module '%s'.", module_name)
            loaded = True
        except ImportError:
            logger.info("Loading all installed modules as module with name '%s' not found.", module_name) #pylint: disable=line-too-long
        except Exception: #pylint: disable=broad-except
            pass
    if not loaded:
        installed_command_modules = []
        try:
            mods_ns_pkg = import_module('azure.cli.command_modules')
            installed_command_modules = [modname for _, modname, _ in \
                                        pkgutil.iter_modules(mods_ns_pkg.__path__)]
        except ImportError:
            pass
        logger.info('Installed command modules %s', installed_command_modules)
        logger.info('Loading command tables from all installed modules.')
        for mod in installed_command_modules:
            try:
                import_module('azure.cli.command_modules.' + mod)
            except Exception: #pylint: disable=broad-except
                # Changing this error message requires updating CI script that checks for failed
                # module loading.
                logger.error("Error loading command module '%s'", mod)
                log_telemetry('Error loading module', module=mod)
                logger.debug(traceback.format_exc())

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

def cli_command(name, operation, client_factory=None, transform=None, table_transformer=None):
    """ Registers a default Azure CLI command. These commands require no special parameters. """
    command_table[name] = create_command(name, operation, transform, table_transformer,
                                         client_factory)

def create_command(name, operation, transform_result, table_transformer, client_factory):

    def _execute_command(kwargs):
        from msrest.paging import Paged
        from msrest.exceptions import ClientException
        from msrestazure.azure_operation import AzureOperationPoller
        from azure.common import AzureException

        client = client_factory(kwargs) if client_factory else None
        try:
            result = operation(client, **kwargs) if client else operation(**kwargs)
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
            raise CLIError(message)
        except AzureException as azure_exception:
            log_telemetry('azure exception', log_type='trace')
            message = re.search(r"([A-Za-z\t .])+", str(azure_exception))
            raise CLIError('\n{}'.format(message.group(0) if message else str(azure_exception)))
        except ValueError as value_error:
            log_telemetry('value exception', log_type='trace')
            raise CLIError(value_error)

    name = ' '.join(name.split())
    cmd = CliCommand(name, _execute_command, table_transformer=table_transformer)
    cmd.description = extract_full_summary_from_signature(operation)
    cmd.arguments.update(extract_args_from_signature(operation))
    return cmd


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
