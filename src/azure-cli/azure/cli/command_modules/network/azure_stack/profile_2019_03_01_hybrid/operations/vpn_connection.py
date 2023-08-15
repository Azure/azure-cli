# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger

from ._util import import_aaz_by_profile

logger = get_logger(__name__)


_VpnConnection = import_aaz_by_profile("network.vpn_connection")


class VpnConnectionUpdate(_VpnConnection.Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ipsec_policies._registered = False

        return args_schema


class VpnConnectionDeviceConfigScriptShow(_VpnConnection.ShowDeviceConfigScript):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.device_family._required = True
        args_schema.firmware_version._required = True
        args_schema.vendor._required = True

        return args_schema


_VpnConnIpsecPolicy = import_aaz_by_profile("network.vpn_connection.ipsec_policy")


class VpnConnIpsecPolicyAdd(_VpnConnIpsecPolicy.Add):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ipsec_policy_index._registered = False
        return args_schema


_VpnConnSharedKey = import_aaz_by_profile("network.vpn_connection.shared_key")


class VpnConnSharedKeyUpdate(_VpnConnSharedKey.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.value._required = True
        return args_schema


def list_vpn_connections(cmd, resource_group_name, virtual_network_gateway_name=None):
    if virtual_network_gateway_name:
        return _VpnConnection.ListConnection(cli_ctx=cmd.cli_ctx)(
            command_args={"resource_group": resource_group_name,
                          "vnet_gateway": virtual_network_gateway_name})
    return _VpnConnection.List(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": resource_group_name})


def clear_vpn_conn_ipsec_policies(cmd, resource_group_name, connection_name, no_wait=False):
    class VpnConnIpsecPoliciesClear(_VpnConnection.Update):

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance.properties.ipsec_policies, client_flatten=True)
            return result

        def pre_operations(self):
            args = self.ctx.args
            args.ipsec_policies = None
            args.use_policy_based_traffic_selectors = False

    ipsec_policies_args = {
        "resource_group": resource_group_name,
        "name": connection_name,
        "no_wait": no_wait,
    }
    return VpnConnIpsecPoliciesClear(cli_ctx=cmd.cli_ctx)(command_args=ipsec_policies_args)
