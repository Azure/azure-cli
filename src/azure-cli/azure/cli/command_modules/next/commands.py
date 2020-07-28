# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.next._client_factory import cf_next


def load_command_table(self, _):

    # TODO: Add command type here
    # next_sdk = CliCommandType(
    #    operations_tmpl='<PATH>.operations#.{}',
    #    client_factory=cf_next)


    with self.command_group('') as g:
        g.custom_command('next', 'handle_next')
