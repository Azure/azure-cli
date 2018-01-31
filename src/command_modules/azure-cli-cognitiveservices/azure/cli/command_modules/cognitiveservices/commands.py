# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.cognitiveservices._client_factory import (
    cf_cognitive_service_accounts,
    cf_accounts)


def load_command_table(self, _):
    mgmt_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations.cognitive_services_accounts_operations#CognitiveServicesAccountsOperations.{}',  # pylint: disable=line-too-long
        client_factory=cf_cognitive_service_accounts
    )

    with self.command_group('cognitiveservices account', mgmt_type) as g:
        g.custom_command('create', 'create')
        g.command('delete', 'delete')
        g.command('show', 'get_properties')
        g.custom_command('update', 'update')
        g.command('list-skus', 'list_skus')

    with self.command_group('cognitiveservices account keys', mgmt_type) as g:
        g.command('regenerate', 'regenerate_key')
        g.command('list', 'list_keys')

    with self.command_group('cognitiveservices') as g:
        g.custom_command('list', 'list_resources', client_factory=cf_accounts)
