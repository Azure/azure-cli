# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.private_link_service._update import Update as _PrivateLinkServiceUpdate


class PrivateLinkServiceUpdate(_PrivateLinkServiceUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(options=['--lb-name'], help="Name of the load balancer to retrieve frontend IP configs from. Ignored if a frontend IP configuration ID is supplied.")
        args_schema.lb_frontend_ip_configs = AAZListArg(options=['--lb-frontend-ip-configs'], help="Space-separated list of names or IDs of load balancer frontend IP configurations to link to. If names are used, also supply `--lb-name`.", nullable=True)
        args_schema.lb_frontend_ip_configs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIpConfigurations/{}"
            ),
            nullable=True
        )
        args_schema.load_balancer_frontend_ip_configurations._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.lb_frontend_ip_configs):
            args.load_balancer_frontend_ip_configurations = assign_aaz_list_arg(
                args.load_balancer_frontend_ip_configurations,
                args.lb_frontend_ip_configs,
                element_transformer=lambda _, lb_frontend_ip_config: {"id": lb_frontend_ip_config}
            )
