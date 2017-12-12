# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.cli.core.prompting import prompt_y_n
from azure.cli.core.commands import cli_command


def transform_extension_list_available(results):
    return [OrderedDict([('Name', r)]) for r in results]


def ext_add_has_confirmed(command_args):
    return bool(not command_args.get('source') or prompt_y_n('Are you sure you want to install this extension?'))


cli_command(__name__, 'extension add', 'azure.cli.command_modules.extension.custom#add_extension',
            confirmation=ext_add_has_confirmed)
cli_command(__name__, 'extension remove', 'azure.cli.command_modules.extension.custom#remove_extension')
cli_command(__name__, 'extension list', 'azure.cli.command_modules.extension.custom#list_extensions')
cli_command(__name__, 'extension show', 'azure.cli.command_modules.extension.custom#show_extension')
cli_command(__name__, 'extension list-available',
            'azure.cli.command_modules.extension.custom#list_available_extensions',
            table_transformer=transform_extension_list_available)
cli_command(__name__, 'extension update', 'azure.cli.command_modules.extension.custom#update_extension')
