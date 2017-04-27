# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument, cli_command
from azure.cli.core.commands.parameters import ignore_type
from azure.cli.core.commands.arm import cli_generic_update_command


# COMMANDS UTILITIES

def create_service_adapter(service_model, service_class=None):
    def _service_adapter(method_name):
        if service_class is not None:
            return '{}#{}.{}'.format(service_model, service_class, method_name)
        else:
            return '{}#{}'.format(service_model, method_name)

    return _service_adapter


# pylint: disable=too-few-public-methods
class ServiceGroup(object):
    def __init__(self, scope, client_factory, service_adapter=None, custom_path=None):
        self._scope = scope
        self._factory = client_factory
        self._service_adapter = service_adapter or (lambda name: name)
        self._custom_path = custom_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def group(self, group_name):
        return CommandGroup(self._scope, group_name, self._factory, self._service_adapter,
                            self._custom_path)


class CommandGroup(object):
    # pylint: disable=too-many-arguments
    def __init__(self, scope, group_name, client_factory, service_adapter=None, custom_path=None):
        self._scope = scope
        self._group_name = group_name
        self._client_factory = client_factory
        self._service_adapter = service_adapter or (lambda name: name)
        self._custom_path = custom_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def command(self, name, method_name, transform=None, table_transformer=None, confirmation=None):
        cli_command(self._scope,
                    '{} {}'.format(self._group_name, name),
                    self._service_adapter(method_name),
                    client_factory=self._client_factory,
                    transform=transform,
                    table_transformer=table_transformer,
                    confirmation=confirmation)

    def custom_command(self, name, custom_func_name, confirmation=None):
        cli_command(self._scope,
                    '{} {}'.format(self._group_name, name),
                    self._custom_path.format(custom_func_name),
                    client_factory=self._client_factory,
                    confirmation=confirmation)

    # pylint: disable=too-many-arguments
    def generic_update_command(self, name, getter_op, setter_op, custom_func_name=None,
                               setter_arg_name='parameters'):
        if custom_func_name:
            custom_function_op = self._custom_path.format(custom_func_name)
        else:
            custom_function_op = None

        cli_generic_update_command(
            self._scope,
            '{} {}'.format(self._group_name, name),
            self._service_adapter(getter_op),
            self._service_adapter(setter_op),
            factory=self._client_factory,
            custom_function_op=custom_function_op,
            setter_arg_name=setter_arg_name)


# PARAMETERS UTILITIES

def patch_arg_make_required(argument):
    argument.type.settings['required'] = True


def patch_arg_update_description(description):
    def _patch_action(argument):
        argument.type.settings['help'] = description

    return _patch_action


class ParametersContext(object):
    def __init__(self, command):
        self._commmand = command

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def ignore(self, argument_name):
        register_cli_argument(self._commmand, argument_name, ignore_type)

    def argument(self, argument_name, arg_type=None, **kwargs):
        register_cli_argument(self._commmand, argument_name, arg_type=arg_type, **kwargs)

    def register_alias(self, argument_name, options_list, **kwargs):
        register_cli_argument(self._commmand, argument_name, options_list=options_list, **kwargs)

    def register(self, argument_name, options_list, **kwargs):
        register_cli_argument(self._commmand, argument_name, options_list=options_list, **kwargs)

    def expand(self, argument_name, model_type, group_name=None, patches=None):
        # TODO:
        # two privates symbols are imported here. they should be made public or this utility class
        # should be moved into azure.cli.core
        from azure.cli.core.commands import _cli_extra_argument_registry
        from azure.cli.core.commands._introspection import \
            (extract_args_from_signature, _option_descriptions)

        from azure.cli.core.sdk.validators import get_complex_argument_processor

        if not patches:
            patches = dict()

        self.ignore(argument_name)

        # fetch the documentation for model parameters first. for models, which are the classes
        # derive from msrest.serialization.Model and used in the SDK API to carry parameters, the
        # document of their properties are attached to the classes instead of constructors.
        parameter_docs = _option_descriptions(model_type)

        expanded_arguments = []
        for name, arg in extract_args_from_signature(model_type.__init__):
            if name in parameter_docs:
                arg.type.settings['help'] = parameter_docs[name]

            if group_name:
                arg.type.settings['arg_group'] = group_name

            if name in patches:
                patches[name](arg)

            _cli_extra_argument_registry[self._commmand][name] = arg
            expanded_arguments.append(name)

        self.argument(argument_name,
                      arg_type=ignore_type,
                      validator=get_complex_argument_processor(expanded_arguments,
                                                               argument_name,
                                                               model_type))
