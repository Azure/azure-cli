# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway.aad._assign import Assign as _VnetGatewayAadAssign


class VnetGatewayAadAssign(_VnetGatewayAadAssign):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.audience._required = True
        args_schema.issuer._required = True
        args_schema.tenant._required = True

        return args_schema
