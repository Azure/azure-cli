# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import register_cli_argument, ignore_type
from azure.cli.core.commands.validators import get_complex_argument_processor
from azure.cli.core.commands._introspection import (extract_args_from_signature,
                                                    _option_descriptions)
from azure.cli.core.commands import _cli_extra_argument_registry


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

    def expand(self, argument_name, model_type, group_name=None, patches=None):
        if not patches:
            patches = dict()

        self.ignore(argument_name)

        # Fetch the documentation for model parameters first. Note: a class's constructor's
        # docstring is set on the class itself.
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
                      validator=get_complex_argument_processor(expanded_arguments, model_type))
