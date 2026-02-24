# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.nic.ip_config.inbound_nat_rule._add import Add as _NICIPConfigNATAdd


class NICIPConfigNATAdd(_NICIPConfigNATAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            help="Name of the load balancer",
        )
        args_schema.inbound_nat_rule._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/loadBalancers/{lb_name}/inboundNatRules/{}",
        )
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result["ipConfigurations"][0]
