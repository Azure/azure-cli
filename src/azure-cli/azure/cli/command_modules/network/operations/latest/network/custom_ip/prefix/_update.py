# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.custom_ip.prefix._update import Update as _CustomIpPrefixUpdate


class CustomIpPrefixUpdate(_CustomIpPrefixUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.state.enum = AAZArgEnum({"commission": "Commissioning", "decommission": "Decommissioning", "deprovision": "Deprovisioning", "provision": "Provisioning"})

        return args_schema
