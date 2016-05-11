from __future__ import print_function
import time
import random
from importlib import import_module
from collections import defaultdict, OrderedDict
from pip import get_installed_distributions
from msrest.exceptions import ClientException

from azure.cli._util import CLIError
import azure.cli._logging as _logging
from azure.cli._locale import L
from azure.cli.commands._validators import validate_tags, validate_tag

logger = _logging.get_az_logger(__name__)

# Find our command modules, they start with 'azure-cli-'
INSTALLED_COMMAND_MODULES = [dist.key.replace('azure-cli-', '')
                             for dist in get_installed_distributions(local_only=True)
                             if dist.key.startswith('azure-cli-')]

logger.info('Installed command modules %s', INSTALLED_COMMAND_MODULES)

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
    extended_param = parameter_metadata.copy()
    extended_param.update(kwargs)
    return extended_param

def patch_aliases(aliases, patch):
    patched_aliases = aliases.copy()
    patched_aliases.update(patch)
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

    def command(self, name, **kwargs):
        def wrapper(func):
            self[func]['name'] = name
            self[func].update(kwargs)
            return func
        return wrapper

    def description(self, description):
        def wrapper(func):
            self[func]['description'] = description
            return func
        return wrapper

    def help(self, help_file):
        def wrapper(func):
            self[func]['help_file'] = help_file
            return func
        return wrapper

    def option(self, name, **kwargs):
        def wrapper(func):
            opt = dict(kwargs)
            opt['name'] = name
            self[func]['arguments'].append(opt)
            return func
        return wrapper

    def option_set(self, options):
        def wrapper(func):
            for opt in options:
                self[func]['arguments'].append(opt)
            return func
        return wrapper

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

    ordered_commands = OrderedDict(sorted(command_table.items(), key=lambda item: item[1]['name']))
    return ordered_commands
