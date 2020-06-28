# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from {{ mod_path }}._help import helps  # pylint: disable=unused-import


class {{ loader_name }}(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from {{ mod_path }}._client_factory import cf_{{ name }}
        {{ name }}_custom = CliCommandType(
            operations_tmpl='{{ mod_path }}.custom#{}',
            client_factory=cf_{{ name }})
        super({{ loader_name }}, self).__init__(cli_ctx=cli_ctx,
                                                  custom_command_type={{ name }}_custom)

    def load_command_table(self, args):
        from {{ mod_path }}.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from {{ mod_path }}._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = {{ loader_name }}

