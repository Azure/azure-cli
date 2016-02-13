import logging

from ..main import RC
from .._argparse import IncorrectUsageError

# TODO: Alternatively, simply scan the directory for all modules
COMMAND_MODULES = [
    'login',
    'storage',
]

_COMMANDS = []

def command(args):
    def add_command(handler):
        _COMMANDS.append((args.split(), handler))
        logging.debug('Added %s as "%s"', handler, args)
        return handler
    return add_command

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

    for args, handler in _COMMANDS:
        parser.add_command(args, handler)
