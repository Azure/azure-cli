# TODO: Alternatively, simply scan the directory for all modules
COMMAND_MODULES = [
    'account',
    'login',
    'logout',
    'network',
#    'resourcegroup',
#    'storage',
    'vm',
]

class Command(object):

    def __init__(self, name, func, **kwargs):
        self.name = name
        self.func = func
        self.description = kwargs.pop('description', None)
        self.options = kwargs.pop('options', [])

class Option(dict):
    def __init__(self, name, **kwargs):
        super(Option, self).__init__()
        self.name = name
        self.update(kwargs)

class CommandTable(dict):

    def __init__(self):
        super(CommandTable, self).__init__(self)

    def command(self, name, **kwargs):
        def wrapper(func):
            self[func] = Command(name, func, **kwargs)
            return func
        return wrapper

    def option(self, name, **kwargs):
        def wrapper(func):
            self[func].options.append(Option(name, **kwargs))
            return func
        return wrapper

def get_command_table(command_name):
    module = __import__('azure.cli.commands.' + command_name)
    for part in ('cli.commands.' + command_name).split('.'):
        module = getattr(module, part)

    return module.get_command_table()

def add_to_parser(parser, session, command_name=None):
    '''Loads commands into the parser

    When `command` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    loaded = False
    if command_name:
        try:
            parser.load_command_table(session, get_command_table(command_name))
            loaded = True
        except ImportError:
            # Unknown command - we'll load all below
            pass

    if not loaded:
        for mod in COMMAND_MODULES:
            parser.load_command_table(session, get_command_table(mod))
        loaded = True
