# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.arguments import CLIArgumentType
from azure.mgmt.iotcentral.models.iot_central_client_enums import AppSku

from azure.cli.core.commands.parameters import (get_location_type,
                                                get_resource_name_completion_list,
                                                get_enum_type)

app_name_type = CLIArgumentType(
    completer=get_resource_name_completion_list(
        'Microsoft.IoTCentral/IoTApps'),
    help='IoT Central application name.')


def load_arguments(self, _):

    with self.argument_context('iotcentral app') as c:
        c.argument('app_name',
                   app_name_type,
                   options_list=['--name', '-n'],
                   id_part='display_name')

    with self.argument_context('iotcentral app create') as c:
        c.argument('app_name', completer=None)
        c.argument('location', get_location_type(self.cli_ctx),
                   help='Location of your IoT Central application. Default is the location of target resource group.')
        c.argument('sku', arg_type=get_enum_type(AppSku),
                   help='Pricing tier for IoT Central applications. Default value is F1, which is free.')
        c.argument(
            'subdomain', help='Subdomain for the IoT Central URL. Each application must have a unique subdomain.')
