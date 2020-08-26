# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import AzArgumentContext


class RdbmsArgumentContext(AzArgumentContext):  # pylint: disable=too-few-public-methods

    def __init__(self, command_loader, scope, **kwargs):    # pylint: disable=unused-argument
        super(RdbmsArgumentContext, self).__init__(command_loader, scope)
        self.validators = []

    def expand(self, dest, model_type, group_name=None, patches=None):
        super(RdbmsArgumentContext, self).expand(dest, model_type, group_name, patches)

        from knack.arguments import ignore_type

        # Remove the validator and store it into a list
        arg = self.command_loader.argument_registry.arguments[self.command_scope].get(dest, None)
        if not arg:  # when the argument context scope is N/A
            return

        self.validators.append(arg.settings['validator'])
        dest_option = ['--__{}'.format(dest.upper())]
        if dest == 'parameters':
            from .validators import get_combined_validator
            self.argument(dest,
                          arg_type=ignore_type,
                          options_list=dest_option,
                          validator=get_combined_validator(self.validators))
        else:
            self.argument(dest, options_list=dest_option, arg_type=ignore_type, validator=None)
