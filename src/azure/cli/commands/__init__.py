from pip import get_installed_distributions

from .._argparse import IncorrectUsageError
from .._logging import logger

# Find our command modules, they start with 'azure-cli-'
INSTALLED_COMMAND_MODULES = [dist.key.replace('azure-cli-', '') for dist in get_installed_distributions(local_only=False) if dist.key.startswith('azure-cli-')]

_COMMANDS = {}

def command(name):
    def add_command(handler):
        _COMMANDS.setdefault(handler, {})['name'] = name
        logger.debug('Added %s as command "%s"', handler, name)
        return handler
    return add_command

def description(description_text):
    def add_description(handler):
        _COMMANDS.setdefault(handler, {})['description'] = description_text
        logger.debug('Added description "%s" to %s', description_text, handler)
        return handler
    return add_description

def option(spec, description_text=None, required=False, target=None):
    def add_option(handler):
        _COMMANDS.setdefault(handler, {}).setdefault('args', []) \
            .append((spec, description_text, required, target))
        logger.debug('Added option "%s" to %s', spec, handler)
        return handler
    return add_option

def add_to_parser(parser, command_name=None):
    '''Loads commands into the parser

    When `command` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''

    # Importing the modules is sufficient to invoke the decorators. Then we can
    # get all of the commands from the _COMMANDS variable.
    loaded = False
    if command_name:
        try:
            # Try and load the installed command module
            __import__('azure.cli.command_modules.'+command_name)
            loaded = True
        except ImportError:
            # Unknown command - we'll load all installed modules below
            pass

    if not loaded:
        for installed_mods in INSTALLED_COMMAND_MODULES:
            __import__('azure.cli.command_modules.'+installed_mods)
        loaded = True

    for handler, info in _COMMANDS.items():
        # args have probably been added in reverse order
        info.setdefault('args', []).reverse()
        parser.add_command(handler, **info)
