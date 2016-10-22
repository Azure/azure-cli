#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from.custom import (list_contexts,
                    show_contexts,
                    activate_context,
                    delete_context,
                    create_context,
                    modify_context)

cli_command('context list', list_contexts)
cli_command('context show', show_contexts)
cli_command('context delete', delete_context)
cli_command('context create', create_context)
cli_command('context switch', activate_context)
cli_command('context modify', modify_context)
