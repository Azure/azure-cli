# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.role._help  # pylint: disable=unused-import
from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType
from ._client_factory import _graph_client_factory as graph_client_factory
from .msgrpah import GraphError


class RoleCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        role_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.role.custom#{}')
        super(RoleCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                 resource_type=ResourceType.MGMT_AUTHORIZATION,
                                                 operation_group='role_assignments',
                                                 custom_command_type=role_custom)

    def load_command_table(self, args):
        if args and args[0] in ('role', 'ad'):
            from knack.log import get_logger
            logger = get_logger(__name__)
            logger.warning("This command or command group has been migrated to Microsoft Graph API. "
                           "Please carefully review all breaking changes introduced during this migration: "
                           "https://docs.microsoft.com/cli/azure/microsoft-graph-migration")
        from azure.cli.command_modules.role.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.role._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = RoleCommandsLoader


__all__ = [
    # Public msgraph.GraphClient factory that should be used by other modules
    "graph_client_factory",
    # Public Exception that is raised by msgraph.GraphClient
    "GraphError"
]
