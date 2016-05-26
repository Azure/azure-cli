from __future__ import print_function
import copy
import inspect
import re
import time
import random
from importlib import import_module
from collections import defaultdict, OrderedDict
from pip import get_installed_distributions
from msrest.exceptions import ClientException
from msrest.paging import Paged

from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError
import azure.cli._logging as _logging
from azure.cli._locale import L
from azure.cli.commands._validators import validate_tags, validate_tag
import azure.cli.commands.argument_types

logger = _logging.get_az_logger(__name__)

# Find our command modules, they start with 'azure-cli-'
INSTALLED_COMMAND_MODULES = [dist.key.replace('azure-cli-', '')
                             for dist in get_installed_distributions(local_only=True)
                             if dist.key.startswith('azure-cli-')]

logger.info('Installed command modules %s', INSTALLED_COMMAND_MODULES)

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config',
                             'content_version', 'kwargs', 'client'])

COMMON_PARAMETERS = {
    'deployment_name': {
        'name': '--deployment-name',
        'metavar': 'DEPLOYMENTNAME',
        'help': 'Name of the resource deployment',
        'default': 'azurecli' + str(time.time()) + str(random.randint(0, 10000000)),
        'required': False
    },
    'location': {
        'name': '--location -l',
        'metavar': 'LOCATION',
        'help': 'Location',
    },
    'resource_group_name': {
        'name': '--resource-group -g',
        'metavar': 'RESOURCEGROUP',
        'help': 'The name of the resource group',
    },
    'tag' : {
        'name': '--tag',
        'metavar': 'TAG',
        'help': L('a single tag in \'key[=value]\' format'),
        'type': validate_tag
    },
    'tags' : {
        'name': '--tags',
        'metavar': 'TAGS',
        'help': L('multiple semicolon separated tags in \'key[=value]\' format'),
        'type': validate_tags
    },
}

def extend_parameter(parameter_metadata, **kwargs):
    extended_param = copy.deepcopy(parameter_metadata)
    extended_param.update(kwargs)
    return extended_param

def patch_aliases(aliases, patch):
    patched_aliases = copy.deepcopy(aliases)
    for key in patch:
        if key in patched_aliases:
            patched_aliases[key].update(patch[key])
        else:
            patched_aliases[key] = patch[key]
    return patched_aliases

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
            raise CLIError(message)
        logger.info("Long running operation '%s' completed with result %s",
                    self.start_msg, result)
        logger.warning(self.finish_msg)
        return result

class CommandTable(defaultdict):
    """A command table is a dictionary of func -> {name,
                                                   func,
                                                   **kwargs}
    objects.

    The `name` is the space separated name - i.e. 'az vm list'
    `func` represents the handler for the method, and will be called with the parsed
    args from argparse.ArgumentParser. The remaining keyword arguments will be passed to
    ArgumentParser.add_parser.
    """
    def __init__(self):
        super(CommandTable, self).__init__(lambda: {'arguments': []})

def _get_command_table(module_name):
    module = import_module('azure.cli.command_modules.' + module_name)
    return module.command_table

def get_command_table(module_name=None):
    '''Loads command table(s)

    When `module_name` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    loaded = False
    if module_name:
        try:
            command_table = _get_command_table(module_name)
            logger.info("Successfully loaded command table from module '%s'.", module_name)
            loaded = True
        except ImportError:
            # Unknown command - we'll load all installed modules below
            logger.info("Loading all installed modules as module with name '%s' not found.", module_name) #pylint: disable=line-too-long

    if not loaded:
        command_table = {}
        logger.info('Loading command tables from all installed modules.')
        for mod in INSTALLED_COMMAND_MODULES:
            command_table.update(_get_command_table(mod))

    ordered_commands = OrderedDict(command_table)
    return ordered_commands

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
            required = arg_name not in arg_defaults

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

class CliCommand(object):

    def __init__(self, name, handler, description=None):
        self.name = name
        self.handler = handler
        self.description = description
        self.help_file = None
        self.arguments = {}

    def add_argument(self, param_name, *option_strings, **kwargs):
        argument = azure.cli.commands.argument_types.CliCommandArgument(param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argument_type):
        arg = self.arguments[param_name]
        arg.update(argument_type.options_list, **argument_type.options)

    def execute(**kwargs):
        return self.handler(**kwargs)

def create_command(name, operation, return_type, client_factory):
    def _execute_command(kwargs):
        client = client_factory(kwargs) if client_factory else None
        try:
            result = operation(client, **kwargs)
            if not return_type:
                return {}
            if callable(return_type):
                return return_type(result)
            if isinstance(return_type, str):
                return list(result) if isinstance(result, Paged) else result
        except TypeError as exception:
            raise IncorrectUsageError(exception)
        except ClientException as client_exception:
            message = getattr(client_exception, 'message', client_exception)
            raise CLIError(message)

    name = ' '.join(name.split())
    command = CliCommand(name, _execute_command)
    _extract_args_from_signature(command, operation)

    return command

