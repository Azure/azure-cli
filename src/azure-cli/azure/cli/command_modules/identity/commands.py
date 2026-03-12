# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import _msi_user_identities_operations, _msi_operations_operations


def load_command_table(self, _):

    identity_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations#UserAssignedIdentitiesOperations.{}',
        client_factory=_msi_user_identities_operations
    )
    msi_operations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations#Operations.{}',
        client_factory=_msi_operations_operations
    )
    with self.command_group('identity', identity_sdk, client_factory=_msi_user_identities_operations) as g:
        # Note: 'create', 'update', and 'show' commands are defined
        # via AAZ generated code for the latest preview version.
        g.command('delete', 'delete')
        g.custom_command('list', 'list_user_assigned_identities')
        g.custom_command('list-resources', 'list_identity_resources', min_api='2021-09-30-preview')

    with self.command_group('identity', msi_operations_sdk, client_factory=_msi_operations_operations) as g:
        g.command('list-operations', 'list')
