# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import types
from collections import OrderedDict, defaultdict
from importlib import import_module

from .deprecation import Deprecated
from .preview import PreviewItem
from .experimental import ExperimentalItem
from .prompting import prompt_y_n, NoTTYException
from .util import CLIError, CtxTypeError
from .arguments import ArgumentRegistry, CLICommandArgument
from .introspection import extract_args_from_signature, extract_full_summary_from_signature
from .events import (EVENT_CMDLOADER_LOAD_COMMAND_TABLE, EVENT_CMDLOADER_LOAD_ARGUMENTS,
                     EVENT_COMMAND_CANCELLED)
from .log import get_logger
from .validators import DefaultInt, DefaultStr

logger = get_logger(__name__)


PREVIEW_EXPERIMENTAL_CONFLICT_ERROR = "Failed to register {} '{}', " \
                                      "is_preview and is_experimental can't be true at the same time"


class CLICommand(object):  # pylint:disable=too-many-instance-attributes

    # pylint: disable=unused-argument
    def __init__(self, cli_ctx, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None,
                 formatter_class=None, deprecate_info=None, validator=None, confirmation=None, preview_info=None,
                 experimental_info=None, **kwargs):
        """ The command object that goes into the command table.

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param name: The name of the command (e.g. 'mygroup mycommand')
        :type name: str
        :param handler: The function that will handle this command
        :type handler: function
        :param description: The description for the command
        :type description: str
        :param table_transformer: A function that transforms the command output for displaying in a table
        :type table_transformer: function
        :param arguments_loader: The function that defines how the arguments for the command should be loaded
        :type arguments_loader: function
        :param description_loader: The function that defines how the description for the command should be loaded
        :type description_loader: function
        :param formatter_class: The formatter for how help should be displayed
        :type formatter_class: class
        :param deprecate_info: Deprecation message to display when this command is invoked
        :type deprecate_info: str
        :param preview_info: Indicates a command is in preview
        :type preview_info: bool
        :param experimental_info: Indicates a command is experimental
        :type experimental_info: bool
        :param validator: The command validator
        :param confirmation: User confirmation required for command
        :type confirmation: bool, str, callable
        :param kwargs: Extra kwargs that are currently ignored
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.name = name
        self.handler = handler
        self.help = None
        self.description = description_loader if description_loader and self.should_load_description() else description
        self.arguments = {}
        self.arguments_loader = arguments_loader
        self.table_transformer = table_transformer
        self.formatter_class = formatter_class
        self.deprecate_info = deprecate_info
        self.preview_info = preview_info
        self.experimental_info = experimental_info
        self.confirmation = confirmation
        self.validator = validator

    def should_load_description(self):
        return not self.cli_ctx.data['completer_active']

    def _resolve_default_value_from_config_file(self, arg, overrides):
        default_key = overrides.settings.get('configured_default', None)
        if not default_key:
            return

        defaults_section = self.cli_ctx.config.defaults_section_name
        use_local_config_original = self.cli_ctx.config.use_local_config
        self.cli_ctx.config.set_to_use_local_config(True)
        config_value = self.cli_ctx.config.get(defaults_section, default_key, None)
        self.cli_ctx.config.set_to_use_local_config(use_local_config_original)
        if config_value:
            logger.info("Configured default '%s' for arg %s", config_value, arg.name)
            overrides.settings['default'] = DefaultStr(config_value)
            overrides.settings['required'] = False
            overrides.settings['default_value_source'] = 'Config'

    def load_arguments(self):
        if self.arguments_loader:
            cmd_args = self.arguments_loader()
            if self.confirmation:
                cmd_args.append(('yes',
                                 CLICommandArgument(dest='yes', options_list=['--yes', '-y'],
                                                    action='store_true', help='Do not prompt for confirmation.')))
            self.arguments.update(cmd_args)

    def add_argument(self, param_name, *option_strings, **kwargs):
        dest = kwargs.pop('dest', None)
        argument = CLICommandArgument(dest or param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        # resolve defaults from either environment variable or config file
        self._resolve_default_value_from_config_file(arg, argtype)
        arg.type.update(other=argtype)
        arg_default = arg.type.settings.get('default', None)
        # apply DefaultStr and DefaultInt to allow distinguishing between
        # when a default was applied or when the user specified a value
        # that coincides with the default
        if isinstance(arg_default, str):
            arg_default = DefaultStr(arg_default)
        elif isinstance(arg_default, int) and not isinstance(arg_default, bool):
            # bool's is_default is ignored for now, because
            # 1. bool is a subclass of int, so isinstance(True, int) cannot distinguish between int and bool
            # 2. bool is not extendable according to https://stackoverflow.com/a/2172204/2199657
            arg_default = DefaultInt(arg_default)
        # update the default
        if arg_default:
            arg.type.settings['default'] = arg_default

    def execute(self, **kwargs):
        return self(**kwargs)

    def __call__(self, *args, **kwargs):

        cmd_args = args[0]

        confirm = self.confirmation and not cmd_args.pop('yes', None) \
            and not self.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False)

        if confirm and not self._user_confirmed(self.confirmation, cmd_args):
            self.cli_ctx.raise_event(EVENT_COMMAND_CANCELLED, command=self.name, command_args=cmd_args)
            raise CLIError('Operation cancelled.')
        return self.handler(*args, **kwargs)

    @staticmethod
    def _user_confirmed(confirmation, command_args):
        if callable(confirmation):
            return confirmation(command_args)
        try:
            if isinstance(confirmation, str):
                return prompt_y_n(confirmation)
            return prompt_y_n('Are you sure you want to perform this operation?')
        except NoTTYException:
            logger.warning('Unable to prompt for confirmation as no tty available. Use --yes.')
            return False


# pylint: disable=too-many-instance-attributes
class CLICommandsLoader(object):

    def __init__(self, cli_ctx=None, command_cls=CLICommand, excluded_command_handler_args=None):
        """ The loader of commands. It contains the command table and argument registries.

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param command_cls: The command type that the command table will be populated with
        :type command_cls: knack.commands.CLICommand
        :param excluded_command_handler_args: List of params to ignore and not extract from a commands handler.
                                              By default we ignore ['self', 'kwargs'].
        :type excluded_command_handler_args: list of str
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.command_cls = command_cls
        self.skip_applicability = False
        self.excluded_command_handler_args = excluded_command_handler_args
        # A command table is a dictionary of name -> CLICommand instances
        self.command_table = {}
        # A command group table is a dictionary of names -> CommandGroup instances
        self.command_group_table = {}
        # An argument registry stores all arguments for commands
        self.argument_registry = ArgumentRegistry()
        self.extra_argument_registry = defaultdict(lambda: {})

    def _populate_command_group_table_with_subgroups(self, name):
        if not name:
            return

        # ensure all subgroups have some entry in the command group table
        name_components = name.split()
        for i, _ in enumerate(name_components):
            subgroup_name = ' '.join(name_components[:i + 1])
            if subgroup_name not in self.command_group_table:
                self.command_group_table[subgroup_name] = {}

    def load_command_table(self, args):  # pylint: disable=unused-argument
        """ Load commands into the command table

        :param args: List of the arguments from the command line
        :type args: list
        :return: The ordered command table
        :rtype: collections.OrderedDict
        """
        self.cli_ctx.raise_event(EVENT_CMDLOADER_LOAD_COMMAND_TABLE, cmd_tbl=self.command_table)
        return OrderedDict(self.command_table)

    def load_arguments(self, command):
        """ Load the arguments for the specified command

        :param command: The command to load arguments for
        :type command: str
        """
        from knack.arguments import ArgumentsContext

        self.cli_ctx.raise_event(EVENT_CMDLOADER_LOAD_ARGUMENTS, cmd_tbl=self.command_table, command=command)
        try:
            self.command_table[command].load_arguments()
        except KeyError:
            return

        # ensure global 'cmd' is ignored
        with ArgumentsContext(self, '') as c:
            c.ignore('cmd')

        self._apply_parameter_info(command, self.command_table[command])

    def _apply_parameter_info(self, command_name, command):
        for argument_name in command.arguments:
            overrides = self.argument_registry.get_cli_argument(command_name, argument_name)
            command.update_argument(argument_name, overrides)
        # Add any arguments explicitly registered for this command
        for argument_name, argument_definition in self.extra_argument_registry[command_name].items():
            command.arguments[argument_name] = argument_definition
            command.update_argument(argument_name, self.argument_registry.get_cli_argument(command_name, argument_name))

    def create_command(self, name, operation, **kwargs):
        """ Constructs the command object that can then be added to the command table """
        if not isinstance(operation, str):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        name = ' '.join(name.split())

        client_factory = kwargs.get('client_factory', None)

        def _command_handler(command_args):
            op = CLICommandsLoader._get_op_handler(operation)
            client = client_factory(command_args) if client_factory else None
            result = op(client, **command_args) if client else op(**command_args)
            return result

        def arguments_loader():
            return list(extract_args_from_signature(CLICommandsLoader._get_op_handler(operation),
                                                    excluded_params=self.excluded_command_handler_args))

        def description_loader():
            return extract_full_summary_from_signature(CLICommandsLoader._get_op_handler(operation))

        kwargs['arguments_loader'] = arguments_loader
        kwargs['description_loader'] = description_loader

        cmd = self.command_cls(self.cli_ctx, name, _command_handler, **kwargs)
        return cmd

    @staticmethod
    def _get_op_handler(operation):
        """ Import and load the operation handler """
        try:
            mod_to_import, attr_path = operation.split('#')
            op = import_module(mod_to_import)
            for part in attr_path.split('.'):
                op = getattr(op, part)
            if isinstance(op, types.FunctionType):
                return op
            # op as types.MethodType
            return op.__func__
        except (ValueError, AttributeError) as ex:
            raise ValueError("The operation '{}' is invalid.".format(operation)) from ex

    def deprecate(self, **kwargs):
        kwargs['object_type'] = 'command group'
        return Deprecated(self.cli_ctx, **kwargs)


class CommandGroup(object):

    def __init__(self, command_loader, group_name, operations_tmpl, **kwargs):
        """ Context manager for registering commands that share common properties.

        :param command_loader: The command loader that commands will be registered into
        :type command_loader: knack.commands.CLICommandsLoader
        :param group_name: The name of the group of commands in the command hierarchy
        :type group_name: str
        :param operations_tmpl: The template for handlers for this group of commands (e.g. '__main__#{}')
        :type operations_tmpl: str
        :param kwargs: Kwargs to apply to all commands in this group.
                       Possible values: `client_factory`, `arguments_loader`, `description_loader`, `description`,
                       `formatter_class`, `table_transformer`, `deprecate_info`, `validator`, `confirmation`.
        """
        self.command_loader = command_loader
        self.group_name = group_name
        self.operations_tmpl = operations_tmpl
        self.group_kwargs = kwargs
        Deprecated.ensure_new_style_deprecation(self.command_loader.cli_ctx, self.group_kwargs, 'command group')
        if kwargs['deprecate_info']:
            kwargs['deprecate_info'].target = group_name

        is_preview = kwargs.get('is_preview', False)
        is_experimental = kwargs.get('is_experimental', False)
        if is_preview and is_experimental:
            raise CLIError(PREVIEW_EXPERIMENTAL_CONFLICT_ERROR.format("command group", group_name))
        if is_preview:
            kwargs['preview_info'] = PreviewItem(
                cli_ctx=self.command_loader.cli_ctx,
                target=group_name,
                object_type='command group'
            )
        if is_experimental:
            kwargs['experimental_info'] = ExperimentalItem(
                cli_ctx=self.command_loader.cli_ctx,
                target=group_name,
                object_type='command group'
            )
        command_loader._populate_command_group_table_with_subgroups(group_name)  # pylint: disable=protected-access
        self.command_loader.command_group_table[group_name] = self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def command(self, name, handler_name, **kwargs):
        """ Register a command into the command table

        :param name: The name of the command
        :type name: str
        :param handler_name: The name of the handler that will be applied to the operations template
        :type handler_name: str
        :param kwargs: Kwargs to apply to the command.
                       Possible values: `client_factory`, `arguments_loader`, `description_loader`, `description`,
                       `formatter_class`, `table_transformer`, `deprecate_info`, `validator`, `confirmation`,
                       `is_preview`, `is_experimental`.
        """
        import copy

        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        command_kwargs = copy.deepcopy(self.group_kwargs)
        command_kwargs.update(kwargs)

        # don't inherit deprecation, preview and experimental info from command group
        # https://github.com/Azure/azure-cli/blob/683b9709b67c4c9e8df92f9fbd53cbf83b6973d3/src/azure-cli-core/azure/cli/core/commands/__init__.py#L1155
        command_kwargs['deprecate_info'] = kwargs.get('deprecate_info', None)

        is_preview = kwargs.get('is_preview', False)
        is_experimental = kwargs.get('is_experimental', False)
        if is_preview and is_experimental:
            raise CLIError(PREVIEW_EXPERIMENTAL_CONFLICT_ERROR.format("command", self.group_name + " " + name))

        command_kwargs['preview_info'] = None
        if is_preview:
            command_kwargs['preview_info'] = PreviewItem(self.command_loader.cli_ctx, object_type='command')
        command_kwargs['experimental_info'] = None
        if is_experimental:
            command_kwargs['experimental_info'] = ExperimentalItem(self.command_loader.cli_ctx, object_type='command')

        self.command_loader._populate_command_group_table_with_subgroups(' '.join(command_name.split()[:-1]))  # pylint: disable=protected-access
        self.command_loader.command_table[command_name] = self.command_loader.create_command(
            command_name,
            self.operations_tmpl.format(handler_name),
            **command_kwargs)

    def deprecate(self, **kwargs):
        kwargs['object_type'] = 'command'
        return Deprecated(self.command_loader.cli_ctx, **kwargs)
