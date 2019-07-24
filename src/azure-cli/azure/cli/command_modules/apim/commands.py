# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._format import (service_output_format)
from azure.cli.command_modules.apim._client_factory import (api_client_factory, service_client_factory)

def load_command_table(self, _):

    service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiManagementServiceOperations.{}',
        client_factory=service_client_factory
    )

    api_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiOperations.{}',
        client_factory=api_client_factory
    )

    with self.command_group('apim', service_sdk,  is_preview=True) as g:
        g.custom_command('create', 'create_apim', supports_no_wait=True)
        g.custom_show_command('show', 'get_apim', table_transformer=service_output_format) 
        g.custom_command('list', 'list_apim', table_transformer=service_output_format)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.generic_update_command('update', setter_name='update', custom_func_name='update_apim')
        g.custom_command('check-name', 'check_name_availability')
        g.custom_command('backup', 'apim_backup', supports_no_wait=True)
        g.custom_command('apply-vnet-updates', 'apim_apply_network_configuration_updates', supports_no_wait=True)

    with self.command_group('apim api', api_sdk) as g:
        g.custom_command('list', 'list_apim_api')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)

