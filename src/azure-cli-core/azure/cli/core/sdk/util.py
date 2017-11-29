# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import EXCLUDED_PARAMS
from azure.cli.core.commands.arm import _cli_generic_update_command, _cli_generic_wait_command

from knack.arguments import ignore_type, ArgumentsContext
from knack.commands import CommandGroup as KnackCommandGroup
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

# COMMANDS UTILITIES

CLI_COMMAND_KWARGS = ['transform', 'table_transformer', 'confirmation', 'exception_handler', 'min_api', 'max_api',
                      'client_factory', 'operations_tmpl', 'no_wait_param', 'validator', 'resource_type']


# pylint: disable=too-few-public-methods
class CliCommandType(object):

    def __init__(self, overrides=None, **kwargs):
        if isinstance(overrides, str):
            raise ValueError("Overrides has to be a {} (cannot be a string)".format(CliCommandType.__name__))
        unrecognized_kwargs = [x for x in kwargs if x not in CLI_COMMAND_KWARGS]
        if unrecognized_kwargs:
            raise TypeError('unrecognized kwargs: {}'.format(unrecognized_kwargs))
        self.settings = {}
        self.update(overrides, **kwargs)

    def update(self, other=None, **kwargs):
        if other:
            self.settings.update(**other.settings)
        self.settings.update(**kwargs)


class _CommandGroup(KnackCommandGroup):

    def __init__(self, command_loader, group_name, **kwargs):
        operations_tmpl = kwargs.pop('operations_tmpl', None)
        super(_CommandGroup, self).__init__(command_loader, group_name,
                                            operations_tmpl, **kwargs)
        if operations_tmpl:
            self.group_kwargs['operations_tmpl'] = operations_tmpl
        self.is_stale = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_stale = True

    def _check_stale(self):
        if self.is_stale:
            message = "command authoring error: command group '{}' is stale! " \
                      "Check that the subsequent block for has a corresponding `as` statement.".format(self.group_name)
            logger.error(message)
            raise CLIError(message)

    # pylint: disable=arguments-differ
    def command(self, name, method_name=None, command_type=None, **kwargs):
        """
        Register a CLI command
        :param name: Name of the command as it will be called on the command line
        :type name: str
        :param method_name: Name of the method the command maps to
        :type method_name: str
        :param command_type: CliCommandType object containing settings to apply to the entire command group
        :type command_type: CliCommandType
        :param kwargs: Keyword arguments. Supported keyword arguments include:
            - client_factory: Callable which returns a client needed to access the underlying command method. (function)
            - confirmation: Prompt prior to the action being executed. This is useful if the action
                            would cause a loss of data. (bool)
            - exception_handler: Exception handler for handling non-standard exceptions (function)
            - no_wait_param: The name of a boolean parameter that will be exposed as `--no-wait` to skip long running
              operation polling. (string)
            - transform: Transform function for transforming the output of the command (function)
            - table_transformer: Transform function or JMESPath query to be applied to table output to create a
                                 better output format for tables. (function or string)
            - resource_type: The ResourceType enum value to use with min or max API. (ResourceType)
            - min_api: Minimum API version required for commands within the group (string)
            - max_api: Maximum API version required for commands within the group (string)
        :rtype: None
        """
        self._check_stale()
        merged_kwargs = self.group_kwargs.copy()
        group_command_type = merged_kwargs.get('command_type', None)
        if command_type:
            merged_kwargs.update(command_type.settings)
        elif group_command_type:
            merged_kwargs.update(group_command_type.settings)
        merged_kwargs.update(kwargs)

        operations_tmpl = merged_kwargs.get('operations_tmpl')
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        operation = operations_tmpl.format(method_name) if operations_tmpl else None
        self.command_loader._cli_command(command_name, operation, **merged_kwargs)  # pylint: disable=protected-access

    def custom_command(self, name, method_name, **kwargs):
        """
        Register a custom CLI command.
        :param name: Name of the command as it will be called on the command line
        :type name: str
        :param method_name: Name of the method the command maps to
        :type method_name: str
        :param kwargs: Keyword arguments. Supported keyword arguments include:
            - client_factory: Callable which returns a client needed to access the underlying command method. (function)
            - confirmation: Prompt prior to the action being executed. This is useful if the action
                            would cause a loss of data. (bool)
            - exception_handler: Exception handler for handling non-standard exceptions (function)
            - no_wait_param: The name of a boolean parameter that will be exposed as `--no-wait` to skip long
              running operation polling. (string)
            - transform: Transform function for transforming the output of the command (function)
            - table_transformer: Transform function or JMESPath query to be applied to table output to create a
                                 better output format for tables. (function or string)
            - resource_type: The ResourceType enum value to use with min or max API. (ResourceType)
            - min_api: Minimum API version required for commands within the group (string)
            - max_api: Maximum API version required for commands within the group (string)
        :rtype: None
        """
        self._check_stale()
        merged_kwargs = self.group_kwargs.copy()
        custom_command_type = merged_kwargs.get('custom_command_type', None)
        if not custom_command_type:
            raise CLIError('Module does not have `custom_command_type` set!')
        if custom_command_type:
            merged_kwargs.update(custom_command_type.settings)
        merged_kwargs.update(kwargs)

        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        self.command_loader._cli_command(command_name,  # pylint: disable=protected-access
                                         operation=merged_kwargs['operations_tmpl'].format(method_name),
                                         **merged_kwargs)

    def generic_update_command(self, name,
                               getter_name='get', setter_name='create_or_update', setter_arg_name='parameters',
                               child_collection_prop_name=None, child_collection_key='name', child_arg_name='item_name',
                               custom_func_name=None, **kwargs):
        self._check_stale()
        merged_kwargs = self.group_kwargs.copy()
        merged_kwargs.update(kwargs)

        operations_tmpl = merged_kwargs.get('operations_tmpl', None)
        if not operations_tmpl:
            group_command_type = merged_kwargs.get('command_type', None)
            operations_tmpl = group_command_type.settings['operations_tmpl'] if group_command_type else None
        getter_tmpl = operations_tmpl
        setter_tmpl = operations_tmpl

        custom_tmpl = None
        if custom_func_name:
            custom_tmpl = self.group_kwargs.get('custom_command_type').settings['operations_tmpl']

        _cli_generic_update_command(
            self.command_loader,
            '{} {}'.format(self.group_name, name),
            getter_op=getter_tmpl.format(getter_name),
            setter_op=setter_tmpl.format(setter_name),
            setter_arg_name=setter_arg_name,
            custom_function_op=custom_tmpl.format(custom_func_name) if custom_func_name else None,
            child_collection_prop_name=child_collection_prop_name,
            child_collection_key=child_collection_key,
            child_arg_name=child_arg_name,
            **merged_kwargs)

    def generic_wait_command(self, name, getter_name='get', **kwargs):
        self._check_stale()
        merged_kwargs = self.group_kwargs.copy()
        merged_kwargs.update(kwargs)

        operations_tmpl = merged_kwargs.get('operations_tmpl', None)
        if not operations_tmpl:
            command_type = merged_kwargs.get('command_type', None)
            operations_tmpl = command_type.settings['operations_tmpl'] if command_type else None
        getter_tmpl = operations_tmpl

        _cli_generic_wait_command(
            self.command_loader,
            '{} {}'.format(self.group_name, name),
            getter_op=getter_tmpl.format(getter_name),
            **merged_kwargs)


# PARAMETERS UTILITIES

def patch_arg_make_required(argument):
    argument.type.settings['required'] = True


def patch_arg_make_optional(argument):
    argument.type.settings['required'] = False


def patch_arg_update_description(description):
    def _patch_action(argument):
        argument.type.settings['help'] = description

    return _patch_action


class _ParametersContext(ArgumentsContext):

    def __init__(self, command_loader, scope, **kwargs):
        super(_ParametersContext, self).__init__(command_loader, scope)
        self.scope = scope  # this is called "command" in knack, but that is not an accurate name
        self.group_kwargs = kwargs
        self.is_stale = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_stale = True

    def _applicable(self):
        command_name = self.command_loader.command_name
        scope = self.scope
        return command_name.startswith(scope)

    def _check_stale(self):
        if self.is_stale:
            message = "command authoring error: argument context '{}' is stale! " \
                      "Check that the subsequent block for has a corresponding `as` statement.".format(self.scope)
            logger.error(message)
            raise CLIError(message)

    # pylint: disable=arguments-differ
    def argument(self, dest, arg_type=None, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        merged_kwargs = self.group_kwargs.copy()
        if arg_type:
            merged_kwargs.update(arg_type.settings)
        merged_kwargs.update(kwargs)
        if self.command_loader.supported_api_version(resource_type=merged_kwargs.get('resource_type'),
                                                     min_api=merged_kwargs.get('min_api'),
                                                     max_api=merged_kwargs.get('max_api')):
            super(_ParametersContext, self).argument(dest, **merged_kwargs)
        else:
            self.ignore(dest)

    def expand(self, dest, model_type, group_name=None, patches=None):
        # TODO:
        # two privates symbols are imported here. they should be made public or this utility class
        # should be moved into azure.cli.core
        from azure.cli.core.sdk.validators import get_complex_argument_processor
        from knack.introspection import extract_args_from_signature, option_descriptions
        self._check_stale()
        if not self._applicable():
            return

        if not patches:
            patches = dict()

        # fetch the documentation for model parameters first. for models, which are the classes
        # derive from msrest.serialization.Model and used in the SDK API to carry parameters, the
        # document of their properties are attached to the classes instead of constructors.
        parameter_docs = option_descriptions(model_type)

        expanded_arguments = []
        for name, arg in extract_args_from_signature(model_type.__init__, excluded_params=EXCLUDED_PARAMS):
            if name in parameter_docs:
                arg.type.settings['help'] = parameter_docs[name]

            if group_name:
                arg.type.settings['arg_group'] = group_name

            if name in patches:
                patches[name](arg)

            self.extra(name, arg_type=arg)
            expanded_arguments.append(name)

        self.argument(dest,
                      arg_type=ignore_type,
                      validator=get_complex_argument_processor(expanded_arguments, dest, model_type))

    def ignore(self, *args):
        self._check_stale()
        if not self._applicable():
            return

        for arg in args:
            super(_ParametersContext, self).ignore(arg)

    def extra(self, dest, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        merged_kwargs = self.group_kwargs.copy()
        merged_kwargs.update(kwargs)
        if self.command_loader.supported_api_version(resource_type=merged_kwargs.get('resource_type'),
                                                     min_api=merged_kwargs.get('min_api'),
                                                     max_api=merged_kwargs.get('max_api')):
            super(_ParametersContext, self).extra(dest, **merged_kwargs)
