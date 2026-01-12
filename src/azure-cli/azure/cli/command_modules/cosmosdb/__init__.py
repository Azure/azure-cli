# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.events import EVENT_INVOKER_PRE_PARSE_ARGS

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.cosmosdb._help import helps  # pylint: disable=unused-import


def _documentdb_deprecate(_, args):
    if args[0] == 'documentdb':
        from azure.cli.core.util import CLIError
        raise CLIError('All documentdb commands have been renamed to cosmosdb')


class CosmosDbCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.cosmosdb._client_factory import cf_cosmosdb_document
        from azure.cli.command_modules.cosmosdb._command_type import CosmosDbCommandGroup
        from azure.cli.core.profiles import ResourceType
        cosmosdb_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.cosmosdb.custom#{}',
            client_factory=cf_cosmosdb_document)

        cli_ctx.register_event(EVENT_INVOKER_PRE_PARSE_ARGS, _documentdb_deprecate)

        super().__init__(cli_ctx=cli_ctx,
                         resource_type=ResourceType.MGMT_COSMOSDB,
                         custom_command_type=cosmosdb_custom,
                         command_group_cls=CosmosDbCommandGroup)

    def load_command_table(self, args):
        from azure.cli.command_modules.cosmosdb.commands import load_command_table
        from azure.cli.core.aaz import load_aaz_command_table
        try:
            from . import aaz
        except ImportError:
            aaz = None
        if aaz:
            load_aaz_command_table(
                loader=self,
                aaz_pkg_name=aaz.__name__,
                args=args
            )
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.cosmosdb._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = CosmosDbCommandsLoader
