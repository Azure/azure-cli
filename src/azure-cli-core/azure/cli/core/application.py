# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import defaultdict
import sys
import os
import uuid
import argparse
from azure.cli.core.parser import AzCliCommandParser, enable_autocomplete
from azure.cli.core._output import CommandResultItem
import azure.cli.core.extensions
import azure.cli.core._help as _help
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import todict, truncate_text, CLIError, read_file_content
from azure.cli.core._config import az_config
import azure.cli.core.commands.progress as progress

import azure.cli.core.telemetry as telemetry

logger = azlogging.get_az_logger(__name__)

ARGCOMPLETE_ENV_NAME = '_ARGCOMPLETE'


class Configuration(object):  # pylint: disable=too-few-public-methods
    """The configuration object tracks session specific data such
    as output formats, available commands etc.
    """

    def __init__(self):
        self.output_format = None

    def get_command_table(self, argv=None):  # pylint: disable=no-self-use
        import azure.cli.core.commands as commands
        # Find the first noun on the command line and only load commands from that
        # module to improve startup time.
        result = commands.get_command_table(argv[0].lower() if argv else None)

        if argv is None:
            return result

        command_tree = Configuration.build_command_tree(result)
        matches = Configuration.find_matches(argv, command_tree)
        return dict(matches)

    def load_params(self, command):  # pylint: disable=no-self-use
        import azure.cli.core.commands as commands
        commands.load_params(command)

    @staticmethod
    def build_command_tree(command_table):
        '''From the list of commands names, find the exact match or
           set of potential matches that we are looking for
        '''
        result = {}
        for command in command_table:
            index = result
            parts = command.split()
            for part in parts[:-1]:
                if part not in index:
                    index[part] = {}
                index = index[part]
            index[parts[-1]] = command_table[command]

        return result

    @staticmethod
    def find_matches(parts, commandtable):
        from .commands import CliCommand

        best_match = commandtable
        command_so_far = ""
        try:
            for part in parts:
                best_match = best_match[part.lower()]
                command_so_far = ' '.join((command_so_far, part))
                if isinstance(best_match, CliCommand):
                    break
        except KeyError:
            pass

        if isinstance(best_match, CliCommand):
            yield (best_match.name, best_match)
        else:
            for part in best_match:
                cmd = best_match[part]
                if isinstance(cmd, CliCommand):
                    yield (cmd.name, cmd)
                else:
                    dummy_cmdname = ' '.join((command_so_far, part))
                    yield (dummy_cmdname, CliCommand(dummy_cmdname, None))


class Application(object):

    TRANSFORM_RESULT = 'Application.TransformResults'
    FILTER_RESULT = 'Application.FilterResults'
    GLOBAL_PARSER_CREATED = 'GlobalParser.Created'
    COMMAND_PARSER_LOADED = 'CommandParser.Loaded'
    COMMAND_PARSER_PARSING = 'CommandParser.Parsing'
    COMMAND_PARSER_PARSED = 'CommandParser.Parsed'
    COMMAND_TABLE_LOADED = 'CommandTable.Loaded'
    COMMAND_TABLE_PARAMS_LOADED = 'CommandTableParams.Loaded'

    def __init__(self, configuration=None):
        self._event_handlers = defaultdict(lambda: [])
        self.session = {
            'headers': {},  # the x-ms-client-request-id is generated before a command is to execute
            'command': 'unknown',
            'completer_active': ARGCOMPLETE_ENV_NAME in os.environ,
            'query_active': False
        }

        # Register presence of and handlers for global parameters
        self.register(self.GLOBAL_PARSER_CREATED, Application._register_builtin_arguments)
        self.register(self.COMMAND_PARSER_PARSED, self._handle_builtin_arguments)

        # Let other extensions make their presence known
        azure.cli.core.extensions.register_extensions(self)

        self.global_parser = AzCliCommandParser(prog='az', add_help=False)
        global_group = self.global_parser.add_argument_group('global', 'Global Arguments')
        self.raise_event(self.GLOBAL_PARSER_CREATED, global_group=global_group)

        self.parser = AzCliCommandParser(prog='az', parents=[self.global_parser])
        self.configuration = configuration
        self.progress_controller = progress.ProgressHook()

    def get_progress_controller(self, det=False):
        self.progress_controller.init_progress(progress.get_progress_view(det))
        return self.progress_controller

    def initialize(self, configuration):
        self.configuration = configuration

    def execute(self, unexpanded_argv):  # pylint: disable=too-many-statements
        self.refresh_request_id()

        argv = Application._expand_file_prefixed_files(unexpanded_argv)
        command_table = self.configuration.get_command_table(argv)
        self.raise_event(self.COMMAND_TABLE_LOADED, command_table=command_table)
        self.parser.load_command_table(command_table)
        self.raise_event(self.COMMAND_PARSER_LOADED, parser=self.parser)

        if not argv:
            enable_autocomplete(self.parser)
            az_subparser = self.parser.subparsers[tuple()]
            _help.show_welcome(az_subparser)

            # TODO: Question, is this needed?
            telemetry.set_command_details('az')
            telemetry.set_success(summary='welcome')

            return None

        if argv[0].lower() == 'help':
            argv[0] = '--help'

        # Rudimentary parsing to get the command
        nouns = []
        for i, current in enumerate(argv):
            try:
                if current[0] == '-':
                    break
            except IndexError:
                pass
            argv[i] = current.lower()
            nouns.append(argv[i])

        command = ' '.join(nouns)

        if argv[-1] in ('--help', '-h') or command in command_table:
            self.configuration.load_params(command)
            self.raise_event(self.COMMAND_TABLE_PARAMS_LOADED, command_table=command_table)
            self.parser.load_command_table(command_table)

        if self.session['completer_active']:
            enable_autocomplete(self.parser)

        self.raise_event(self.COMMAND_PARSER_PARSING, argv=argv)
        args = self.parser.parse_args(argv)

        self.raise_event(self.COMMAND_PARSER_PARSED, command=args.command, args=args)
        results = []
        for expanded_arg in _explode_list_args(args):
            self.session['command'] = expanded_arg.command
            try:
                _validate_arguments(expanded_arg)
            except CLIError:
                raise
            except:  # pylint: disable=bare-except
                err = sys.exc_info()[1]
                getattr(expanded_arg, '_parser', self.parser).validation_error(str(err))

            # Consider - we are using any args that start with an underscore (_) as 'private'
            # arguments and remove them from the arguments that we pass to the actual function.
            # This does not feel quite right.
            params = dict([(key, value)
                           for key, value in expanded_arg.__dict__.items()
                           if not key.startswith('_')])
            params.pop('subcommand', None)
            params.pop('func', None)
            params.pop('command', None)

            telemetry.set_command_details(expanded_arg.command,
                                          self.configuration.output_format,
                                          [p for p in unexpanded_argv if p.startswith('-')])

            result = expanded_arg.func(params)
            result = todict(result)
            results.append(result)

        if len(results) == 1:
            results = results[0]

        event_data = {'result': results}
        self.raise_event(self.TRANSFORM_RESULT, event_data=event_data)
        self.raise_event(self.FILTER_RESULT, event_data=event_data)

        return CommandResultItem(event_data['result'],
                                 table_transformer=command_table[args.command].table_transformer,
                                 is_query_active=self.session['query_active'])

    def raise_event(self, name, **kwargs):
        '''Raise the event `name`.
        '''
        data = truncate_text(str(kwargs), width=500)
        logger.debug("Application event '%s' with event data %s", name, data)
        for func in list(self._event_handlers[name]):  # Make copy in case handler modifies the list
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
        logger.debug("Registered application event handler '%s' at %s", name, handler)

    def remove(self, name, handler):
        '''Remove a callable that is registered to be called when the
        event `name` is raised.

        param: name: The name of the event
        param: handler: Function that takes two parameters;
          name: name of the event raised
          event_data: `dict` with event specific data.
        '''
        self._event_handlers[name].remove(handler)
        logger.debug("Removed application event handler '%s' at %s", name, handler)

    def refresh_request_id(self):
        """Assign a new randome GUID as x-ms-client-request-id

        The method must be invoked before each command execution in order to ensure unique client side request ID is
        generated.
        """
        self.session['headers']['x-ms-client-request-id'] = str(uuid.uuid1())

    @staticmethod
    def _register_builtin_arguments(**kwargs):
        global_group = kwargs['global_group']
        global_group.add_argument('--output', '-o', dest='_output_format',
                                  choices=['json', 'tsv', 'table', 'jsonc'],
                                  default=az_config.get('core', 'output', fallback='json'),
                                  help='Output format',
                                  type=str.lower)
        # The arguments for verbosity don't get parsed by argparse but we add it here for help.
        global_group.add_argument('--verbose', dest='_log_verbosity_verbose', action='store_true',
                                  help='Increase logging verbosity. Use --debug for full debug logs.')
        global_group.add_argument('--debug', dest='_log_verbosity_debug', action='store_true',
                                  help='Increase logging verbosity to show all debug logs.')

    @staticmethod
    def _maybe_load_file(arg):
        ix = arg.find('@')
        if ix == -1:  # no @ found
            return arg

        poss_file = arg[ix + 1:]
        if not poss_file:  # if nothing after @ then it can't be a file
            return arg
        elif ix == 0:
            return Application._load_file(poss_file)

        # if @ not at the start it can't be a file
        return arg

    @staticmethod
    def _expand_file_prefix(arg):
        arg_split = arg.split('=', 1)
        try:
            return '='.join([arg_split[0], Application._maybe_load_file(arg_split[1])])
        except IndexError:
            return Application._maybe_load_file(arg_split[0])

    @staticmethod
    def _expand_file_prefixed_files(argv):
        return list([Application._expand_file_prefix(arg) for arg in argv])

    @staticmethod
    def _load_file(path):
        if path == '-':
            content = sys.stdin.read()
        else:
            content = read_file_content(os.path.expanduser(path),
                                        allow_binary=True)

        return content[0:-1] if content and content[-1] == '\n' else content

    def _handle_builtin_arguments(self, **kwargs):
        args = kwargs['args']
        self.configuration.output_format = args._output_format  # pylint: disable=protected-access
        del args._output_format


def _validate_arguments(args, **_):
    for validator in getattr(args, '_validators', []):
        validator(args)
    try:
        delattr(args, '_validators')
    except AttributeError:
        pass


def _explode_list_args(args):
    '''Iterate through each attribute member of args and create a copy with
    the IterateValues 'flattened' to only contain a single value

    Ex.
        { a1:'x', a2:IterateValue(['y', 'z']) } => [{ a1:'x', a2:'y'),{ a1:'x', a2:'z'}]
    '''
    list_args = {argname: argvalue for argname, argvalue in vars(args).items()
                 if isinstance(argvalue, IterateValue)}
    if not list_args:
        yield args
    else:
        values = list(zip(*list_args.values()))
        for key in list_args:
            delattr(args, key)

        for value in values:
            new_ns = argparse.Namespace(**vars(args))
            for key_index, key in enumerate(list_args.keys()):
                setattr(new_ns, key, value[key_index])
            yield new_ns


class IterateAction(argparse.Action):  # pylint: disable=too-few-public-methods
    '''Action used to collect argument values in an IterateValue list
    The application will loop through each value in the IterateValue
    and execeute the associated handler for each
    '''

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, IterateValue(values))


class IterateValue(list):
    '''Marker class to indicate that, when found as a value in the parsed namespace
    from argparse, the handler should be invoked once per value in the list with all
    other values in the parsed namespace frozen.

    Typical use is to allow multiple ID parameter to a show command etc.
    '''
    pass


APPLICATION = Application()

telemetry.set_application(APPLICATION, ARGCOMPLETE_ENV_NAME)
