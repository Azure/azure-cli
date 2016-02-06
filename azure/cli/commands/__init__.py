import logging

from ..main import RC
from .._util import import_module

COMMAND_MODULES = [
    'login',
    'storage',
]

MODULE_PREFIX = __package__ + '.'

def add_commands(top_level_parser):
    from .._util import import_module
    for module in COMMAND_MODULES:
        logging.debug("Adding commands from '%s'", module)
        mod = import_module(MODULE_PREFIX + module)
        logging.debug(" - source: '%s'", mod.__file__)
        
        parser = top_level_parser.add_parser(mod.COMMAND_NAME, help=mod.COMMAND_HELP)
        mod.add_commands(parser)

def process_command(args):
    # service will be the azure.cli.commands.<service> module to import
    service = (args.service or '').lower()
    
    if not service:
        raise RuntimeError(RC.UNKNOWN_SERVICE.format(''))
    
    logging.debug("Importing '%s%s' for command", MODULE_PREFIX, service)
    try:
        mod = import_module(MODULE_PREFIX + service)
    except ImportError:
        raise RuntimeError(RC.UNKNOWN_SERVICE.format(service))
    
    mod.execute(args)

class CommandDispatcher(object):
    def __init__(self, command_name):
        self.command_name = command_name
        self.commands = {}
    
    def __call__(self, func_or_name):
        if isinstance(func_or_name, str):
            def decorate(func):
                self.commands[func_or_name] = func
                return func
            return decorate
        
        self.commands[func_or_name.__name__] = func_or_name
        return func_or_name
        
    def execute(self, args):
        command = getattr(args, self.command_name)
        logging.debug("Dispatching to '%s'", command)
        return self.commands[command](args)
