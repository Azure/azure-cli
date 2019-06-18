# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from ._client_factory import iotcentral_service_factory


def load_command_table(self, _):

    from azure.cli.core.commands import CliCommandType

    iotcentral_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.iotcentral.operations#IoTCentaralOperations.{}'
    )

    update_custom_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.iotcentral.custom#{}')

    with self.command_group('iotcentral app', iotcentral_sdk, client_factory=iotcentral_service_factory) as g:
        g.custom_command('create', 'iotcentral_app_create')
        g.custom_command('list', 'iotcentral_app_list')
        g.custom_command('show', 'iotcentral_app_get')
        g.generic_update_command('update', getter_name='iotcentral_app_get',
                                 setter_name='iotcentral_app_update', command_type=update_custom_util)
        g.custom_command('delete', 'iotcentral_app_delete')
