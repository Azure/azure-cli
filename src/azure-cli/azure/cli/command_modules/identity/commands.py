# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import (_msi_user_identities_operations,
                           _msi_operations_operations,
                           _msi_federated_identity_credentials_operations)
from ._validators import process_msi_namespace

def load_command_table(self, _):
    # Base operations
    with self.command_group('identity') as g:
        g.custom_command('create', 'create_identity', validator=process_msi_namespace)
        g.command('show', 'get', operations_tmpl='azure.mgmt.msi.operations#UserAssignedIdentitiesOperations.{}')
        g.command('delete', 'delete', operations_tmpl='azure.mgmt.msi.operations#UserAssignedIdentitiesOperations.{}')
        g.custom_command('list', 'list_user_assigned_identities')
        g.custom_command('list-resources', 'list_identity_resources', min_api='2021-09-30-preview')
        g.command('list-operations', 'list', operations_tmpl='azure.mgmt.msi.operations#Operations.{}')

    # Federated credential operations
    with self.command_group('identity federated-credential',
                          operations_tmpl='azure.mgmt.msi.operations#FederatedIdentityCredentialsOperations.{}',
                          client_factory=_msi_federated_identity_credentials_operations,
                          is_preview=True) as g:
        g.custom_command('create', 'create_or_update_federated_credential')
        g.custom_command('update', 'create_or_update_federated_credential')
        g.custom_command('delete', 'delete_federated_credential', confirmation=True)
        g.custom_command('show', 'show_federated_credential')
        g.custom_command('list', 'list_federated_credential')
