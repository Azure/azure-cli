# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.vpn_connection.ipsec_policy._add import Add as _VpnConnIpsecPolicyAdd


class VpnConnIpsecPolicyAdd(_VpnConnIpsecPolicyAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ipsec_policy_index._registered = False
        return args_schema
