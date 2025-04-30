# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.commands import CliCommandType

from ._client_factory import _msi_user_identities_operations, _msi_operations_operations, \
    _msi_federated_identity_credentials_operations

from ._validators import process_msi_namespace


def load_command_table(self, _):

    identity_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations#UserAssignedIdentitiesOperations.{}',
        client_factory=_msi_user_identities_operations
    )
    msi_operations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations#Operations.{}',
        client_factory=_msi_operations_operations
    )
    federated_identity_credentials_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations#FederatedIdentityCredentialsOperations.{}',
        client_factory=_msi_federated_identity_credentials_operations
    )

    with self.command_group('identity', is_preview=True) as g:
        g.command_group('', identity_sdk, client_factory=_msi_user_identities_operations) as g2:
            g2.custom_command('create', 'create_identity', validator=process_msi_namespace)
            g2.show_command('show', 'get')
            g2.command('delete', 'delete')
            g2.custom_command('list', 'list_user_assigned_identities')
            g2.custom_command('list-resources', 'list_identity_resources', min_api='2021-09-30-preview')

        g.command_group('', msi_operations_sdk, client_factory=_msi_operations_operations) as g2:
            g2.command('list-operations', 'list')

        g.command_group('federated-credential', federated_identity_credentials_sdk,
                      client_factory=_msi_federated_identity_credentials_operations,
                      min_api='2025-01-31-PREVIEW') as g2:
            g2.custom_command('create', 'create_or_update_federated_credential')
            g2.custom_command('update', 'create_or_update_federated_credential')
            g2.custom_show_command('show', 'show_federated_credential')
            g2.custom_command('delete', 'delete_federated_credential', confirmation=True)
            g2.custom_command('list', 'list_federated_credential')
