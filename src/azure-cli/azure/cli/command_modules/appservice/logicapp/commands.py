# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.appservice.commands import (
    ex_handler_factory,
)


def load_logicapp_commands(command_group):
    logicapp_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.logicapp.custom#{}')

    with command_group('logicapp', custom_command_type=logicapp_custom, is_preview=True) as g:
        g.custom_command('create', 'create_logicapp', exception_handler=ex_handler_factory())
