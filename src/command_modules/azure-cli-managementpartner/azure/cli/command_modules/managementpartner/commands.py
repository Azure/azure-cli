# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.managementpartner._client_factory import managementpartner_partner_client_factory
from ._exception_handler import managementpartner_exception_handler


def load_command_table(self, _):
    def managementpartner_type(*args, **kwargs):
        return CliCommandType(*args, exception_handler=managementpartner_exception_handler, **kwargs)

    managementpartner_partner_sdk = managementpartner_type(
        operations_tmpl='azure.mgmt.managementpartner.operations.partner_operations#PartnerOperations.{}',
        client_factory=managementpartner_partner_client_factory
    )

    with self.command_group('managementpartner', managementpartner_partner_sdk) as g:
        g.command('show', 'get')
        g.command('create', 'create')
        g.command('update', 'update')
        g.command('delete', 'delete')
