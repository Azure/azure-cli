#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from __future__ import print_function

from azure.cli.core.commands import cli_command, LongRunningOperation
from ._factory import (iot_hub_service_factory,)
from azure.cli.command_modules.iot.custom import \
    (iot_hub_create, iot_device_create)

# iot hub commands
factory = iot_hub_service_factory

cli_command('iot hub create', iot_hub_create, factory,
            transform=LongRunningOperation('creating IoT Hub...', '', 10000.0))

cli_command('iot device create', iot_device_create, factory)

