#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=line-too-long

from azure.cli.commands.parameters import (location_type, get_enum_choices)
from azure.cli.commands import register_cli_argument
from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku


# Arguments for 'iot hub create'
register_cli_argument('iot hub create', 'name', options_list=('--name', '-n'),
                      help='Name for new Azure IoT Hub.')
register_cli_argument('iot hub create', 'location', location_type,
                      help='Location of your IoT Hub. Default is the location of target resource group.')
register_cli_argument('iot hub create', 'sku',
                      choices=get_enum_choices(IotHubSku),
                      help='Pricing tier for Azure IoT Hub. Default value is F1, which is free. '
                           'Note that only one free IoT Hub instance is allowed in each subscription. '
                           'Exception will be thrown if free instances exceed one.')
register_cli_argument('iot hub create', 'unit', help='Units in your IoT Hub.', type=int)


# Arguments for 'iot device create'
register_cli_argument('iot device create', 'hub', help='Target IoT Hub name.')
register_cli_argument('iot device create', 'device_id',
                      options_list=('--device-id', '-d'), help='Device Id.')
