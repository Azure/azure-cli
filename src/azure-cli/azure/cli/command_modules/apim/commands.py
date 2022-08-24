# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements


from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._format import (service_output_format)
from azure.cli.command_modules.apim._client_factory import cf_service


def load_command_table(self, _):
    service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiManagementServiceOperations.{}',
        client_factory=cf_service
    )

    # pylint: disable=line-too-long
    with self.command_group('apim', service_sdk) as g:
        g.custom_command('create', 'apim_create', supports_no_wait=True, table_transformer=service_output_format)
        g.custom_show_command('show', 'apim_get', table_transformer=service_output_format)
        g.custom_command('list', 'apim_list', table_transformer=service_output_format)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.generic_update_command('update', custom_func_name='apim_update', getter_name='get', setter_name='begin_create_or_update', supports_no_wait=True)
        g.custom_command('check-name', 'apim_check_name_availability')
        g.custom_command('backup', 'apim_backup', supports_no_wait=True)
        g.custom_command('restore', 'apim_restore', supports_no_wait=True)
        g.custom_command('apply-network-updates', 'apim_apply_network_configuration_updates', supports_no_wait=True)
        g.wait_command('wait')
