from .._argparse import IncorrectUsageError
from .._logging import logger

# TODO: Alternatively, simply scan the directory for all modules
COMMAND_MODULES = [
    'login',
    'logout',
    'account',
    'storage',
    'generated',
    'resourcegroup',
]

_COMMANDS = {}

def command(name):
    def add_command(handler):
        _COMMANDS.setdefault(handler, {})['name'] = name
        logger.debug('Added %s as command "%s"', handler, name)
        return handler
    return add_command

def description(description):
    def add_description(handler):
        _COMMANDS.setdefault(handler, {})['description'] = description
        logger.debug('Added description "%s" to %s', description, handler)
        return handler
    return add_description

def option(spec, description=None):
    def add_option(handler):
        _COMMANDS.setdefault(handler, {}).setdefault('args', []).append((spec, description))
        logger.debug('Added option "%s" to %s', spec, handler)
        return handler
    return add_option

def add_to_parser(parser, command=None):
    '''Loads commands into the parser

    When `command` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    
    # Importing the modules is sufficient to invoke the decorators. Then we can
    # get all of the commands from the _COMMANDS variable.
    loaded = False
    if command:
        try:
            __import__('azure.cli.commands.' + command)
            loaded = True
        except ImportError:
            # Unknown command - we'll load all below
            pass

    if not loaded:
        for mod in COMMAND_MODULES:
            __import__('azure.cli.commands.' + mod)
        loaded = True

    for handler, info in _COMMANDS.items():
        # args have probably been added in reverse order
        info.setdefault('args', []).reverse()
        parser.add_command(handler, **info)
