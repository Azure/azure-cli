# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.vpn_connection._show_device_config_script import ShowDeviceConfigScript as _VpnConnectionDeviceConfigScriptShow


class VpnConnectionDeviceConfigScriptShow(_VpnConnectionDeviceConfigScriptShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.device_family._required = True
        args_schema.firmware_version._required = True
        args_schema.vendor._required = True

        return args_schema
