#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=line-too-long

from azure.cli.core.commands.parameters import \
    (location_type, enum_choice_list, get_resource_name_completion_list)
from azure.cli.core.commands import register_cli_argument
from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku
from ._factory import iot_hub_service_factory
from .custom import iot_device_list


def get_device_id_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    client = iot_hub_service_factory(kwargs)
    return [d.device_id for d in iot_device_list(client, parsed_args.hub_name, top=100)] if parsed_args.hub_name else []

register_cli_argument('iot', 'hub_name', options_list=('--hub-name', '--name', '--hub', '-n'),
                      completer=get_resource_name_completion_list('Microsoft.Devices/IotHubs'),
                      help='The IoT Hub name.')
register_cli_argument('iot', 'device_id', options_list=('--device-id', '-d'), help='Device Id.',
                      completer=get_device_id_completion_list)

# Arguments for 'iot hub create'
register_cli_argument('iot hub create', 'hub_name', completer=None)
register_cli_argument('iot hub create', 'location', location_type,
                      help='Location of your IoT Hub. Default is the location of target resource group.')
register_cli_argument('iot hub create', 'sku',
                      help='Pricing tier for Azure IoT Hub. Default value is F1, which is free. '
                           'Note that only one free IoT Hub instance is allowed in each subscription. '
                           'Exception will be thrown if free instances exceed one.',
                      **enum_choice_list(IotHubSku))
register_cli_argument('iot hub create', 'unit', help='Units in your IoT Hub.', type=int)

# Arguments for 'iot hub show-connection-string'
register_cli_argument('iot hub show-connection-string', 'policy_name',
                      help='The access policy you choose to use.')

# Arguments for 'iot device create'
register_cli_argument('iot device create', 'device_id', completer=None)

# Arguments for 'iot device list'
register_cli_argument('iot device list', 'top', help='Maximum number of device identities to return.', type=int)

# Arguments for 'iot device show-connection-string'
register_cli_argument('iot device show-connection-string', 'top',
                      help='Maximum number of connection strings to return.', type=int)
