#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=line-too-long

from azure.cli.commands.parameters import (location_type,)
from azure.cli.commands import register_cli_argument, CliArgumentType


name_type = CliArgumentType(
    options_list=('--name', '-n'),
    help='Name for new Azure IoT Hub.')
resource_group_type = CliArgumentType(
    options_list=('--resource-group', '-g'),
    help='Target resource group name.')
sku_type = CliArgumentType(
    choices=['F1', 'S1', 'S2', 'S3'], default='F1',
    help='Pricing tier for Azure IoT Hub. Default value is F1, which is free. '
         'Note that only one free IoT Hub instance is allowed in each subscription. '
         'Exception will be thrown if free instances exceed one.'
)
device_id_type = CliArgumentType(options_list=('--device-id', '-d'), help='Device Id.')

# Arguments for 'iot hub create'
register_cli_argument('iot hub create', 'name', name_type)
register_cli_argument('iot hub create', 'resource_group', resource_group_type)
register_cli_argument('iot hub create', 'location', location_type,
                      help='Location of your IoT Hub. Default is the location of target resource group.')
register_cli_argument('iot hub create', 'sku', sku_type)
register_cli_argument('iot hub create', 'unit', CliArgumentType(default=1, help='Units in your IoT Hub.'))

# Arguments for 'iot device create'
register_cli_argument('iot device create', 'hub', help='Target IoT Hub name.')
register_cli_argument('iot device create', 'resource_group', resource_group_type)
register_cli_argument('iot device create', 'device_id', device_id_type)
