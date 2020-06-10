# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.reservations._help  # pylint: disable=unused-import
from azure.cli.command_modules.reservations._client_factory import reservation_mgmt_client_factory
from ._exception_handler import reservations_exception_handler


class ReservationsCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        reservations_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.reservations.custom#{}',
                                             client_factory=reservation_mgmt_client_factory,
                                             exception_handler=reservations_exception_handler)
        super(ReservationsCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                         custom_command_type=reservations_custom,
                                                         resource_type=ResourceType.MGMT_RESERVATIONS)

    def load_command_table(self, args):
        from azure.cli.command_modules.reservations.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.reservations._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ReservationsCommandsLoader
