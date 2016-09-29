#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=line-too-long

from azure.cli.core.commands.parameters import (location_type, get_enum_choices, get_resource_name_completion_list)
from azure.cli.core.commands import register_cli_argument, CliArgumentType

from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku

hub_name_type = CliArgumentType(options_list=('--hub-name', '--name', '--hub', '-n'), help='The IoT Hub name.',
                                completer=get_resource_name_completion_list('Microsoft.Devices/IotHubs'))
device_id_type = CliArgumentType(options_list=('--device-id', '-d'), help='Device Id.')

# Arguments for 'iot hub create'
register_cli_argument('iot hub create', 'hub_name', hub_name_type)
register_cli_argument('iot hub create', 'location', location_type,
                      help='Location of your IoT Hub. Default is the location of target resource group.')
register_cli_argument('iot hub create', 'sku',
                      choices=get_enum_choices(IotHubSku),
                      help='Pricing tier for Azure IoT Hub. Default value is F1, which is free. '
                           'Note that only one free IoT Hub instance is allowed in each subscription. '
                           'Exception will be thrown if free instances exceed one.')
register_cli_argument('iot hub create', 'unit', help='Units in your IoT Hub.', type=int)

# Arguments for 'iot hub show-connection-string'
register_cli_argument('iot hub show-connection-string', 'hub_name', hub_name_type)
register_cli_argument('iot hub show-connection-string', 'policy_name',
                      help='The access policy you choose to use.')

# Arguments for 'iot device create'
register_cli_argument('iot device create', 'hub_name', hub_name_type)
register_cli_argument('iot device create', 'device_id', device_id_type)

# Arguments for 'iot device list'
register_cli_argument('iot device list', 'hub_name', hub_name_type)
register_cli_argument('iot device list', 'top', help='Maximum number of device identities to return.', type=int)

# Arguments for 'iot device show-connection-string'
register_cli_argument('iot device show-connection-string', 'hub_name', hub_name_type)
register_cli_argument('iot device show-connection-string', 'device_id', device_id_type)
