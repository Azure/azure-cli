import logging

from ..main import RC
from .._util import import_module

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

def add_to_parser(parser):
    for mod in COMMAND_MODULES:
        import_module('azure.cli.commands.' + mod)

    for args, handler in _COMMANDS:
        parser.add_command(args, handler)
