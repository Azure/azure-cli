# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZResourceIdArgFormat, AAZListArg, AAZResourceIdArg
from azure.cli.command_modules.network.aaz.latest.network.lb.outbound_rule._create import Create as _LBOutboundRuleCreate


class LBOutboundRuleCreate(_LBOutboundRuleCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
        )
        args_schema.frontend_ip_configs = AAZListArg(
            options=["--frontend-ip-configs"],
            arg_group="Properties",
            help="The List of frontend IP configuration IDs or names.",
        )
        args_schema.frontend_ip_configs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
            )
        )

        args_schema.protocol._required = True
        args_schema.backend_address_pool._required = True
        args_schema.frontend_ip_configurations._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        args.frontend_ip_configurations = assign_aaz_list_arg(
            args.frontend_ip_configurations,
            args.frontend_ip_configs,
            element_transformer=lambda _, id: {"id": id}
        )
