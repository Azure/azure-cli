# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.tunnel_interface._update import Update as _LBAddressPoolTunnelInterfaceUpdate


class LBAddressPoolTunnelInterfaceUpdate(_LBAddressPoolTunnelInterfaceUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.identifier._nullable = False
        args_schema.type._nullable = False
        args_schema.protocol._nullable = False
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
