# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.commands import CliCommandType

from ._client_factory import _msi_user_identities_operations, _msi_operations_operations

from ._validators import process_msi_namespace


def load_command_table(self, _):

    identity_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations#UserAssignedIdentitiesOperations.{}',
        client_factory=_msi_user_identities_operations
    )

    with self.command_group('identity', identity_sdk, client_factory=_msi_user_identities_operations, min_api='2018-11-30') as g:
        g.custom_command('create', 'create_identity', validator=process_msi_namespace)
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_user_assigned_identities')
        g.command('list-operations', 'list', operations_tmpl='azure.mgmt.msi.operations#Operations.{}',
                  client_factory=_msi_operations_operations)
