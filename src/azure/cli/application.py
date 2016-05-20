from collections import defaultdict
from datetime import datetime
import sys
import re
import argparse
from enum import Enum
from .parser import AzCliCommandParser
import azure.cli.extensions
import azure.cli._help as _help
import azure.cli._logging as _logging

logger = _logging.get_az_logger(__name__)

class Configuration(object): # pylint: disable=too-few-public-methods
    """The configuration object tracks session specific data such
    as output formats, available commands etc.
    """
    def __init__(self, argv):
        self.argv = argv or sys.argv[1:]
        self.output_format = 'list'

    def get_command_table(self):
        import azure.cli.commands as commands

        # Find the first noun on the command line and only load commands from that
        # module to improve startup time.
        for a in self.argv:
            if not a.startswith('-'):
                return commands.get_command_table(a)

        # No noun found, so load all commands.
        return  commands.get_command_table()

class Application(object):

    TRANSFORM_RESULT = 'Application.TransformResults'
    FILTER_RESULT = 'Application.FilterResults'
    GLOBAL_PARSER_CREATED = 'GlobalParser.Created'
    COMMAND_PARSER_LOADED = 'CommandParser.Loaded'
    COMMAND_PARSER_PARSED = 'CommandParser.Parsed'
    COMMAND_TABLE_LOADED = 'CommandTable.Loaded'

    def __init__(self, config=None):
        self._event_handlers = defaultdict(lambda: [])

        # Register presence of and handlers for global parameters
        self.register(self.GLOBAL_PARSER_CREATED, Application._register_builtin_arguments)
        self.register(self.COMMAND_PARSER_LOADED, Application._enable_autocomplete)
        self.register(self.COMMAND_PARSER_PARSED, self._handle_builtin_arguments)

        # Let other extensions make their presence known
        azure.cli.extensions.register_extensions(self)

        self.global_parser = AzCliCommandParser(prog='az', add_help=False)
        global_group = self.global_parser.add_argument_group('global', 'Global Arguments')
        self.raise_event(self.GLOBAL_PARSER_CREATED, global_group=global_group)

        self.parser = AzCliCommandParser(prog='az', parents=[self.global_parser])

        if config:
            self.initialize(config)

    def initialize(self, configuration):
        self.configuration = configuration

    def execute(self, argv):
        command_table = self.configuration.get_command_table()
        self.raise_event(self.COMMAND_TABLE_LOADED, command_table=command_table)
        self.parser.load_command_table(command_table)
        self.raise_event(self.COMMAND_PARSER_LOADED, parser=self.parser)

        if len(argv) == 0:
            az_subparser = self.parser.subparsers[tuple()]
            _help.show_welcome(az_subparser)
            return None

        if argv[0].lower() == 'help':
            argv[0] = '--help'

        args = self.parser.parse_args(argv)
        self.raise_event(self.COMMAND_PARSER_PARSED, command=args.command, args=args)

        # Consider - we are using any args that start with an underscore (_) as 'private'
        # arguments and remove them from the arguments that we pass to the actual function.
        # This does not feel quite right.
        params = dict([(key, value)
                       for key, value in args.__dict__.items() if not key.startswith('_')])
        params.pop('subcommand', None)
        params.pop('func', None)
        params.pop('command', None)

        result = args.func(params)

        result = self.todict(result)
        event_data = {'result': result}
        self.raise_event(self.TRANSFORM_RESULT, event_data=event_data)
        self.raise_event(self.FILTER_RESULT, event_data=event_data)
        return event_data['result']

    def raise_event(self, name, **kwargs):
        '''Raise the event `name`.
        '''
        logger.info("Application event '%s' with event data %s", name, kwargs)
        for func in self._event_handlers[name]:
            func(**kwargs)

    def register(self, name, handler):
        '''Register a callable that will be called when the
        event `name` is raised.

        param: name: The name of the event
        param: handler: Function that takes two parameters;
          name: name of the event raised
          event_data: `dict` with event specific data.
        '''
        self._event_handlers[name].append(handler)
        logger.info("Registered application event handler '%s' at %s", name, handler)

    KEYS_CAMELCASE_PATTERN = re.compile('(?!^)_([a-zA-Z])')
    @classmethod
    def todict(cls, obj): #pylint: disable=too-many-return-statements

        def to_camelcase(s):
            return re.sub(cls.KEYS_CAMELCASE_PATTERN, lambda x: x.group(1).upper(), s)

        if isinstance(obj, dict):
            return {k: cls.todict(v) for (k, v) in obj.items()}
        elif isinstance(obj, list):
            return [cls.todict(a) for a in obj]
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '_asdict'):
            return cls.todict(obj._asdict())
        elif hasattr(obj, '__dict__'):
            return dict([(to_camelcase(k), cls.todict(v))
                         for k, v in obj.__dict__.items()
                         if not callable(v) and not k.startswith('_')])
        else:
            return obj

    @staticmethod
    def _enable_autocomplete(**kwargs):
        import argcomplete
        argcomplete.autocomplete(kwargs['parser'])

    @staticmethod
    def _register_builtin_arguments(**kwargs):
        global_group = kwargs['global_group']
        global_group.add_argument('--subscription', dest='_subscription_id', help=argparse.SUPPRESS)
        global_group.add_argument('--output', '-o', dest='_output_format',
                                  choices=['list', 'json', 'tsv'],
                                  default='list',
                                  help='Output format')
        # The arguments for verbosity don't get parsed by argparse but we add it here for help.
        global_group.add_argument('--verbose', dest='_log_verbosity_verbose', action='store_true',
                                  help='Increase logging verbosity. Use --debug for full debug logs.') #pylint: disable=line-too-long
        global_group.add_argument('--debug', dest='_log_verbosity_debug', action='store_true',
                                  help='Increase logging verbosity to show all debug logs.')

    def _handle_builtin_arguments(self, **kwargs):
        args = kwargs['args']
        self.configuration.output_format = args._output_format #pylint: disable=protected-access
        del args._output_format

APPLICATION = Application()
