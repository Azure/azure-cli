from __future__ import print_function
import json
import time
import traceback
from importlib import import_module
from collections import OrderedDict, defaultdict
from pip import get_installed_distributions
from msrest.paging import Paged
from msrest.exceptions import ClientException
from msrestazure.azure_operation import AzureOperationPoller
from azure.cli._util import CLIError
import azure.cli._logging as _logging
from ._introspection import extract_args_from_signature

logger = _logging.get_az_logger(__name__)

# Find our command modules, they start with 'azure-cli-'
INSTALLED_COMMAND_MODULES = [dist.key.replace('azure-cli-', '')
                             for dist in get_installed_distributions(local_only=True)
                             if dist.key.startswith('azure-cli-')]

logger.info('Installed command modules %s', INSTALLED_COMMAND_MODULES)

# pylint: disable=too-many-arguments,too-few-public-methods
class CliArgumentType(object):

    def __init__(self, options_list=None, base_type=str, overrides=None, completer=None,
                 validator=None, **kwargs):
        self.options_list = ()
        self.completer = completer
        self.validator = validator
        if overrides:
            self.options_list = overrides.options_list
            self.options = overrides.options.copy()
            self.base_type = overrides.base_type
        else:
            self.options = {}

        self.base_type = base_type
        self.update(options_list=options_list, **kwargs)

    def update(self, options_list=None, completer=None, validator=None, **kwargs):
        self.options_list = options_list or self.options_list
        self.completer = completer or self.completer
        self.validator = validator or self.validator
        self.options.update(**kwargs)

class CliCommandArgument(CliArgumentType):
    def __init__(self, dest, options_list=None, completer=None, validator=None, **kwargs):
        if options_list is None:
            options_list = '--' + dest.replace('_', '-')

        super(CliCommandArgument, self).__init__(**kwargs)
        self.update(options_list=options_list, completer=completer, validator=validator, **kwargs)
        self.options['dest'] = dest

    def name(self):
        return self.options['dest']


class LongRunningOperation(object): #pylint: disable=too-few-public-methods

    def __init__(self, start_msg='', finish_msg='', poll_interval_ms=1000.0):
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poll_interval_ms = poll_interval_ms

    def _delay(self):
        time.sleep(self.poll_interval_ms / 1000.0)

    def __call__(self, poller):
        logger.warning(self.start_msg)
        logger.info("Starting long running operation '%s' with polling interval %s ms",
                    self.start_msg, self.poll_interval_ms)
        while not poller.done():
            self._delay()
            logger.info("Long running operation '%s' polling now", self.start_msg)
        try:
            result = poller.result()
        except ClientException as client_exception:
            message = getattr(client_exception, 'message', client_exception)

            try:
                message = str(message) + ' ' + json.loads(client_exception.response.text) \
                    ['error']['details'][0]['message']
            except: #pylint: disable=bare-except
                pass

            raise CLIError(message)

        logger.info("Long running operation '%s' completed with result %s",
                    self.start_msg, result)
        logger.warning(self.finish_msg)
        return result

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

    def __init__(self, name, handler, description=None):
        self.name = name
        self.handler = handler
        self.description = description
        self.help = None
        self.arguments = {}

    def add_argument(self, param_name, *option_strings, **kwargs):
        argument = CliCommandArgument(
            param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        arg.update(
            argtype.options_list,
            completer=argtype.completer,
            validator=argtype.validator,
            **argtype.options)

    def execute(self, **kwargs):
        return self.handler(**kwargs)

command_table = CommandTable()

def get_command_table(module_name=None):
    '''Loads command table(s)

    When `module_name` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    loaded = False
    if module_name:
        try:
            import_module('azure.cli.command_modules.' + module_name)
            logger.info("Successfully loaded command table from module '%s'.", module_name)
            loaded = True
        except ImportError:
            # Unknown command - we'll load all installed modules below
            logger.info("Loading all installed modules as module with name '%s' not found.", module_name) #pylint: disable=line-too-long
        except Exception: #pylint: disable=broad-except
            # Catch exception whilst loading the command module.
            # We don't log anything here as we will log below when we try and load all.
            pass

    if not loaded:
        logger.info('Loading command tables from all installed modules.')
        for mod in INSTALLED_COMMAND_MODULES:
            try:
                import_module('azure.cli.command_modules.' + mod)
            except Exception: #pylint: disable=broad-except
                logger.error("Error loading command module '%s'", mod)
                logger.debug(traceback.format_exc())

    _update_command_definitions(command_table)
    ordered_commands = OrderedDict(command_table)
    return ordered_commands

def register_cli_argument(scope, dest, argtype, options_list=None, **kwargs):
    '''Specify CLI specific metadata for a given argument for a given scope.
    '''
    _cli_argument_registry.register_cli_argument(scope, dest, argtype, options_list, **kwargs)

def register_extra_cli_argument(command, dest, options_list=None, **kwargs):
    '''Register extra parameters for the given command. Typically used to augment auto-command built
    commands to add more parameters than the specific SDK method introspected.
    '''
    _cli_extra_argument_registry[command][dest] = CliCommandArgument(dest, options_list, **kwargs)

def cli_command(name, operation, client_factory=None, transform=None):
    """ Registers a default Azure CLI command. These commands require no special parameters. """
    command_table[name] = create_command(name, operation, transform, client_factory)

def create_command(name, operation, transform_result, client_factory):
    def _execute_command(kwargs):
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
            message = getattr(client_exception, 'message', client_exception)
            raise CLIError(message)

    name = ' '.join(name.split())
    cmd = CliCommand(name, _execute_command)
    extract_args_from_signature(cmd, operation)
    return cmd


def _get_cli_argument(command, argname):
    return _cli_argument_registry.get_cli_argument(command, argname)

def _get_cli_extra_arguments(command):
    return _cli_extra_argument_registry[command].items()

class _ArgumentRegistry(object):

    def __init__(self):
        self.arguments = defaultdict(lambda: {})

    def register_cli_argument(self, scope, dest, argtype, options_list, **kwargs):
        argument = CliArgumentType(options_list=options_list, overrides=argtype,
                                   completer=kwargs.pop('completer', argtype.completer),
                                   validator=kwargs.pop('validator', argtype.validator),
                                   **kwargs)
        self.arguments[scope][dest] = argument

    def get_cli_argument(self, command, name):
        parts = command.split()
        result = CliArgumentType()
        for index in range(0, len(parts) + 1):
            probe = ' '.join(parts[0:index])
            override = self.arguments.get(probe, {}).get(name, None)
            if override:
                result.update(override.options_list,
                              completer=override.completer,
                              validator=override.validator,
                              **override.options)
        return result

_cli_argument_registry = _ArgumentRegistry()
_cli_extra_argument_registry = defaultdict(lambda: {})

def _update_command_definitions(command_table_to_update):
    for command_name, command in command_table_to_update.items():
        for argument_name in command.arguments:
            command.update_argument(argument_name, _get_cli_argument(command_name, argument_name))

        # Add any arguments explicitly registered for this command
        for argument_name, argument_definition in _get_cli_extra_arguments(command_name):
            command.arguments[argument_name] = argument_definition
            command.update_argument(argument_name, _get_cli_argument(command_name, argument_name))
