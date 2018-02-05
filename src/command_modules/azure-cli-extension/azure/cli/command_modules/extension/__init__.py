# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from collections import OrderedDict

from knack.prompting import prompt_y_n
from knack.util import CLIError

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType

import azure.cli.command_modules.extension._help  # pylint: disable=unused-import


# pylint: disable=line-too-long
class ExtensionCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(ExtensionCommandsLoader, self).__init__(cli_ctx=cli_ctx)

    def load_command_table(self, args):

        def ext_add_has_confirmed(command_args):
            return bool(not command_args.get('source') or prompt_y_n('Are you sure you want to install this extension?'))

        def transform_extension_list_available(results):
            return [OrderedDict([('Name', r)]) for r in results]

        def validate_extension_add(namespace):
            if (namespace.extension_name and namespace.source) or (not namespace.extension_name and not namespace.source):
                raise CLIError("usage error: --name NAME | --source SOURCE")

        extension_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.extension.custom#{}')

        with self.command_group('extension', extension_custom) as g:
            g.command('add', 'add_extension', confirmation=ext_add_has_confirmed, validator=validate_extension_add)
            g.command('remove', 'remove_extension')
            g.command('list', 'list_extensions')
            g.command('show', 'show_extension')
            g.command('list-available', 'list_available_extensions', table_transformer=transform_extension_list_available)
            g.command('update', 'update_extension')

        return self.command_table

    def load_arguments(self, command):

        from argcomplete.completers import FilesCompleter
        from azure.cli.command_modules.extension._completers import (
            extension_name_completion_list, extension_name_from_index_completion_list)

        with self.argument_context('extension') as c:
            c.argument('extension_name', options_list=['--name', '-n'], help='Name of extension', completer=extension_name_completion_list)
            # This is a hidden parameter for now
            c.argument('index_url', options_list=['--index'], help=argparse.SUPPRESS)

        with self.argument_context('extension add') as c:
            c.argument('extension_name', completer=extension_name_from_index_completion_list)
            c.argument('source', options_list=['--source', '-s'], help='Filepath or URL to an extension', completer=FilesCompleter())
            c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation.')


COMMAND_LOADER_CLS = ExtensionCommandsLoader
