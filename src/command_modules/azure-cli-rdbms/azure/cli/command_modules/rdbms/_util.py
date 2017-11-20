# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.sdk.util import _ParametersContext


class _PolyParametersContext(_ParametersContext):

    def __init__(self, command_loader, scope, **kwargs):
        super(_PolyParametersContext, self).__init__(command_loader, scope)
        self.validators = []

    def expand(self, argument_name, model_type, group_name=None, patches=None):
        super(_PolyParametersContext, self).expand(argument_name, model_type, group_name, patches)

        from knack.arguments import ignore_type

        # Remove the validator and store it into a list
        arg = _get_cli_argument(self._commmand, argument_name)
        self.validators.append(arg.settings['validator'])
        if argument_name == 'parameters':
            from .validators import get_combined_validator
            self.argument(argument_name,
                          arg_type=ignore_type,
                          validator=get_combined_validator(self.validators))
        else:
            self.argument(argument_name, arg_type=ignore_type, validator=None)
