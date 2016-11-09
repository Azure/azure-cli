#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command, LongRunningOperation
from ._factory import iot_hub_service_factory as factory

# iot hub commands
cli_command(__name__, 'iot hub create', 'azure.cli.command_modules.iot.custom#iot_hub_create', factory, transform=LongRunningOperation('creating IoT Hub...', '', 10000.0))
cli_command(__name__, 'iot hub list', 'azure.cli.command_modules.iot.custom#iot_hub_list', factory)
cli_command(__name__, 'iot hub show-connection-string', 'azure.cli.command_modules.iot.custom#iot_hub_show_connection_string', factory)
cli_command(__name__, 'iot hub show', 'azure.cli.command_modules.iot.custom#iot_hub_get', factory)

cli_command(__name__, 'iot device create', 'azure.cli.command_modules.iot.custom#iot_device_create', factory)
cli_command(__name__, 'iot device list', 'azure.cli.command_modules.iot.custom#iot_device_list', factory)
cli_command(__name__, 'iot device show-connection-string', 'azure.cli.command_modules.iot.custom#iot_device_show_connection_string', factory)
cli_command(__name__, 'iot device show', 'azure.cli.command_modules.iot.custom#iot_device_get', factory)
cli_command(__name__, 'iot device delete', 'azure.cli.command_modules.iot.custom#iot_device_delete', factory)
