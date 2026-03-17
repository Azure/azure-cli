# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway.ipsec_policy._add import Add as _VnetGatewayIpsecPolicyAdd


class VnetGatewayIpsecPolicyAdd(_VnetGatewayIpsecPolicyAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vpn_client_ipsec_policy_index._registered = False

        return args_schema
