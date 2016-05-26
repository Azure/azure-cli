from collections import defaultdict

from azure.cli.application import APPLICATION

# pylint: disable=too-many-arguments,too-few-public-methods
class CliArgumentType(object):

    def __init__(self, options_list=None, base_type=str, overrides=None, completer=None,
                 validator=None, **kwargs):
        self.options_list = ()
        self.completer = completer
        self.validator = validator
        if overrides is not None:
            self.options_list = overrides.options_list
            self.options = overrides.options.copy()
            self.base_type = overrides.base_type
        else:
            self.options = {}

        self.base_type = base_type
        self.update(options_list=options_list, **kwargs)

    def update(self, options_list=None, completer=None, validator=None, **kwargs):
        self.options_list = options_list or self.options_list
        self.completer = completer or self.completer
        self.validator = validator or self.validator
        self.options.update(**kwargs)

class CliCommandArgument(CliArgumentType):
    def __init__(self, dest, options_list=None, completer=None, validator=None, **kwargs):
        if options_list is None:
            options_list = '--' + dest.replace('_', '-')

        super(CliCommandArgument, self).__init__(**kwargs)
        self.update(options_list=options_list, completer=completer, validator=validator, **kwargs)
        self.options['dest'] = dest

    def name(self):
        return self.options['dest']

class _ArgumentRegistry(object):

    def __init__(self):
        self.arguments = defaultdict(lambda: {})

    def register_cli_argument(self, scope, dest, argtype, options_list, **kwargs):
        argument = CliArgumentType(options_list=options_list, overrides=argtype,
                                   completer=argtype.completer, validator=argtype.validator,
                                   **kwargs)
        self.arguments[scope][dest] = argument

    def get_cli_argument(self, command, name):
        parts = command.split()
        result = CliArgumentType()
        for index in range(0, len(parts) + 1):
            probe = ' '.join(parts[0:index])
            override = self.arguments.get(probe, {}).get(name, None)
            if override:
                result.update(override.options_list, **override.options)
                result.completer = override.completer
                result.validator = override.validator
        return result

_cli_argument_registry = _ArgumentRegistry()
_cli_extra_argument_registry = defaultdict(lambda: {})

def register_cli_argument(scope, dest, argtype, options_list=None, **kwargs):
    '''Specify CLI specific metadata for a given argument for a given scope.
    '''
    _cli_argument_registry.register_cli_argument(scope, dest, argtype, options_list, **kwargs)

def get_cli_argument(command, argname):
    return _cli_argument_registry.get_cli_argument(command, argname)

def register_additional_cli_argument(command, dest, options_list=None, **kwargs):
    '''Register extra parameters for the given command. Typically used to augment auto-command built
    commands to add more parameters than the specific SDK method introspected.
    '''
    _cli_extra_argument_registry[command][dest] = CliCommandArgument(dest, options_list, **kwargs)

def _update_command_definitions(command_table):
    for command_name, command in command_table.items():
        for argument_name in command.arguments:
            command.update_argument(argument_name, get_cli_argument(command_name, argument_name))

        # Add any arguments explicitly registered for this command
        for argument_name, argument_definition in \
                _cli_extra_argument_registry[command_name].items():
            command.arguments[argument_name] = argument_definition
            command.update_argument(argument_name, get_cli_argument(command_name, argument_name))

def _validate_arguments(args, **_):
    for validator in getattr(args, '_validators', []):
        validator(args)
    try:
        delattr(args, '_validators')
    except AttributeError:
        pass

# Shared argument type definitions
resource_group_name_type = CliArgumentType(
    options_list=('--resource-group', '-g'), help='Name of resource group')
location_type = CliArgumentType(
    options_list=('--location', '-l'),
    help='Location. Use "az locations get" to get a list of valid locations', metavar='LOCATION')
name_type = CliArgumentType(options_list=('--name', '-n'))

# Register usage of said argument types
register_cli_argument('', 'resource_group_name', resource_group_name_type)
register_cli_argument('', 'location', location_type)

# Handlers to update command definitions before they are fed to the parser
APPLICATION.register(APPLICATION.COMMAND_TABLE_LOADED, _update_command_definitions)
APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSED, _validate_arguments)
